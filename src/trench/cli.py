import argparse
import asyncio
import json
from collections.abc import Sequence

from trench.api.app import create_app
from trench.application.seed import seed_teams
from trench.config import get_database_settings
from trench.domain.league import NFL_FRANCHISES
from trench.infrastructure.database import create_engine, create_session_factory
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


COMMANDS = {"openapi": _openapi, "seed-teams": _seed_teams}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="trench")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    print(asyncio.run(COMMANDS[args.command]()))


if __name__ == "__main__":
    main()
