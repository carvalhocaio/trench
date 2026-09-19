import argparse
import asyncio
import json
from collections.abc import Sequence

import httpx

from trench.api.app import create_app
from trench.application.errors import ScheduleConflictError
from trench.application.schedule import ScheduleService
from trench.application.seed import seed_teams
from trench.application.stats import GameStatsService
from trench.config import get_database_settings
from trench.domain.entities import MAX_WEEK, Absence, Player, TeamGameStats
from trench.domain.league import NFL_FRANCHISES
from trench.infrastructure.database import create_engine, create_session_factory
from trench.infrastructure.espn import (
    fetch_boxscore,
    fetch_injuries,
    fetch_roster,
    fetch_week,
)
from trench.infrastructure.repositories.absences import SqlAbsenceRepository
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.player_stats import SqlPlayerGameStatsRepository
from trench.infrastructure.repositories.players import SqlPlayerRepository
from trench.infrastructure.repositories.team_stats import SqlTeamGameStatsRepository
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


async def _import_rosters() -> str:
    engine = create_engine(get_database_settings())
    try:
        async with create_session_factory(engine)() as session, session.begin():
            teams_repo = SqlTeamRepository(session)
            players_repo = SqlPlayerRepository(session)
            created = 0
            updated = 0
            async with httpx.AsyncClient(timeout=30.0) as client:
                for team in await teams_repo.list_all():
                    existing = {
                        player.name: player
                        for player in await players_repo.list_by_team(team.id)
                    }
                    for espn_player in await fetch_roster(client, team.abbreviation):
                        current = existing.get(espn_player.name)
                        if current is None:
                            await players_repo.save(
                                Player(
                                    name=espn_player.name,
                                    team_id=team.id,
                                    position=espn_player.position,
                                )
                            )
                            created += 1
                        elif current.position != espn_player.position:
                            await players_repo.save(
                                Player(
                                    id=current.id,
                                    name=current.name,
                                    team_id=team.id,
                                    position=espn_player.position,
                                )
                            )
                            updated += 1
    finally:
        await engine.dispose()
    return f"players created: {created}, positions updated: {updated}"


async def _import_injuries(season: int, week: int) -> str:
    engine = create_engine(get_database_settings())
    try:
        async with create_session_factory(engine)() as session, session.begin():
            teams_repo = SqlTeamRepository(session)
            players_repo = SqlPlayerRepository(session)
            absences_repo = SqlAbsenceRepository(session)
            service = ScheduleService(
                teams=teams_repo, games=SqlGameRepository(session)
            )
            teams_by_name = {team.name: team for team in await teams_repo.list_all()}

            recorded = 0
            cleared = 0
            skipped_no_game = 0
            skipped_unknown_player = 0
            roster_cache: dict[str, dict[str, Player]] = {}
            async with httpx.AsyncClient(timeout=30.0) as client:
                for injury in await fetch_injuries(client):
                    team = teams_by_name.get(injury.team_name)
                    if team is None:
                        continue
                    games = await service.find(season, week=week, team_id=team.id)
                    if not games:
                        skipped_no_game += 1
                        continue
                    if team.abbreviation not in roster_cache:
                        roster_cache[team.abbreviation] = {
                            player.name: player
                            for player in await players_repo.list_by_team(team.id)
                        }
                    player = roster_cache[team.abbreviation].get(injury.player_name)
                    if player is None:
                        skipped_unknown_player += 1
                        continue
                    game = games[0]
                    if injury.status is None:
                        await absences_repo.remove(game.id, player.id)
                        cleared += 1
                    else:
                        await absences_repo.save(
                            Absence(
                                game_id=game.id,
                                player_id=player.id,
                                status=injury.status,
                            )
                        )
                        recorded += 1
    finally:
        await engine.dispose()
    return (
        f"absences recorded: {recorded}, cleared: {cleared}, "
        f"no game this week: {skipped_no_game}, "
        f"unknown player: {skipped_unknown_player}"
    )


async def _import_stats(season: int, week: int) -> str:
    engine = create_engine(get_database_settings())
    try:
        async with create_session_factory(engine)() as session, session.begin():
            teams_repo = SqlTeamRepository(session)
            players_repo = SqlPlayerRepository(session)
            games_repo = SqlGameRepository(session)
            schedule = ScheduleService(teams=teams_repo, games=games_repo)
            stats = GameStatsService(
                games=games_repo,
                players=players_repo,
                team_stats=SqlTeamGameStatsRepository(session),
                player_stats=SqlPlayerGameStatsRepository(session),
            )
            team_ids = {
                team.abbreviation: team.id for team in await teams_repo.list_all()
            }

            team_stats_recorded = 0
            player_stats_recorded = 0
            skipped_no_game = 0
            skipped_unknown_player = 0
            roster_cache: dict[str, dict[str, Player]] = {}
            async with httpx.AsyncClient(timeout=30.0) as client:
                for espn_game in await fetch_week(client, season, week):
                    if espn_game.score is None:
                        continue
                    home_id = team_ids[espn_game.home_abbreviation]
                    away_id = team_ids[espn_game.away_abbreviation]
                    games = await schedule.find(season, week=week, team_id=home_id)
                    matching = [g for g in games if g.involves(away_id)]
                    if not matching:
                        skipped_no_game += 1
                        continue
                    game_id = matching[0].id

                    box = await fetch_boxscore(client, espn_game.espn_id)
                    for team_box in box.teams:
                        team_id = team_ids.get(team_box.abbreviation)
                        if team_id is None:
                            continue
                        await stats.record_team_stats(
                            TeamGameStats(
                                game_id=game_id,
                                team_id=team_id,
                                offensive_plays=team_box.offensive_plays,
                                passing_yards=team_box.passing_yards,
                                rushing_yards=team_box.rushing_yards,
                                turnovers=team_box.turnovers,
                                sacks=team_box.sacks,
                            )
                        )
                        team_stats_recorded += 1

                    for player_box in box.players:
                        team_id = team_ids.get(player_box.team_abbreviation)
                        if team_id is None:
                            continue
                        if player_box.team_abbreviation not in roster_cache:
                            roster_cache[player_box.team_abbreviation] = {
                                player.name: player
                                for player in await players_repo.list_by_team(team_id)
                            }
                        player = roster_cache[player_box.team_abbreviation].get(
                            player_box.name
                        )
                        if player is None:
                            skipped_unknown_player += 1
                            continue
                        await stats.record_player_stats(
                            game_id=game_id, player_id=player.id, **player_box.fields
                        )
                        player_stats_recorded += 1
    finally:
        await engine.dispose()
    return (
        f"team stats recorded: {team_stats_recorded}, "
        f"player stats recorded: {player_stats_recorded}, "
        f"games not found: {skipped_no_game}, unknown players: {skipped_unknown_player}"
    )


COMMANDS = {
    "openapi": _openapi,
    "seed-teams": _seed_teams,
    "import-rosters": _import_rosters,
}
SEASON_COMMANDS = {"import-schedule": _import_schedule}
SEASON_WEEK_COMMANDS = {
    "import-injuries": _import_injuries,
    "import-stats": _import_stats,
}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="trench")
    choices = [
        *sorted(COMMANDS),
        *sorted(SEASON_COMMANDS),
        *sorted(SEASON_WEEK_COMMANDS),
    ]
    parser.add_argument("command", choices=choices)
    parser.add_argument("--season", type=int, help="season year, e.g. 2026")
    parser.add_argument("--week", type=int, help="week number, e.g. 2")
    args = parser.parse_args(argv)
    if args.command in SEASON_COMMANDS:
        if args.season is None:
            parser.error(f"{args.command} requires --season")
        print(asyncio.run(SEASON_COMMANDS[args.command](args.season)))
        return
    if args.command in SEASON_WEEK_COMMANDS:
        if args.season is None or args.week is None:
            parser.error(f"{args.command} requires --season and --week")
        print(asyncio.run(SEASON_WEEK_COMMANDS[args.command](args.season, args.week)))
        return
    print(asyncio.run(COMMANDS[args.command]()))


if __name__ == "__main__":
    main()
