import argparse
import asyncio
import json
from collections.abc import Sequence

import httpx

from trench.api.app import create_app
from trench.application.errors import ScheduleConflictError
from trench.application.schedule import ScheduleService
from trench.application.seed import seed_teams
from trench.config import get_database_settings
from trench.domain.entities import MAX_WEEK
from trench.domain.league import NFL_FRANCHISES
from trench.infrastructure.database import create_engine, create_session_factory
from trench.infrastructure.espn import fetch_week
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.teams import SqlTeamRepository


async def _seed_teams() -> str:
    engine = create_engine(get_database_settings())
    try:
        async with create_session_factory(engine)() as session, session.begin():
            result = await seed_teams(SqlTeamRepository(session), NFL_FRANCHISES)
    finally:
        await engine.dispose()
    return f"teams created: {len(result.created)}, skipped: {len(result.skipped)}"


async def _openapi() -> str:
    return json.dumps(create_app().openapi(), indent=2, ensure_ascii=False)


async def _import_schedule(season: int) -> str:
    engine = create_engine(get_database_settings())
    try:
        async with create_session_factory(engine)() as session, session.begin():
            teams_repo = SqlTeamRepository(session)
            service = ScheduleService(
                teams=teams_repo, games=SqlGameRepository(session)
            )
            team_ids = {
                team.abbreviation: team.id for team in await teams_repo.list_all()
            }

            created = 0
            already_scheduled = 0
            scores_recorded = 0
            async with httpx.AsyncClient(timeout=30.0) as client:
                for week in range(1, MAX_WEEK + 1):
                    for espn_game in await fetch_week(client, season, week):
                        home_id = team_ids[espn_game.home_abbreviation]
                        away_id = team_ids[espn_game.away_abbreviation]
                        try:
                            game = await service.schedule(
                                season=season,
                                week=week,
                                kickoff=espn_game.kickoff,
                                home_team_id=home_id,
                                away_team_id=away_id,
                            )
                            created += 1
                        except ScheduleConflictError:
                            existing = await service.find(
                                season, week=week, team_id=home_id
                            )
                            game = next(g for g in existing if g.involves(away_id))
                            already_scheduled += 1
                        if espn_game.score is not None and game.score is None:
                            await service.record_score(game.id, espn_game.score)
                            scores_recorded += 1
    finally:
        await engine.dispose()
    return (
        f"games created: {created}, already scheduled: {already_scheduled}, "
        f"scores recorded: {scores_recorded}"
    )


COMMANDS = {"openapi": _openapi, "seed-teams": _seed_teams}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="trench")
    parser.add_argument("command", choices=[*sorted(COMMANDS), "import-schedule"])
    parser.add_argument("--season", type=int, help="season year, e.g. 2026")
    args = parser.parse_args(argv)
    if args.command == "import-schedule":
        if args.season is None:
            parser.error("import-schedule requires --season")
        print(asyncio.run(_import_schedule(args.season)))
        return
    print(asyncio.run(COMMANDS[args.command]()))


if __name__ == "__main__":
    main()
