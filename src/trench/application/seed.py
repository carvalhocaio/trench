from collections.abc import Iterable
from dataclasses import dataclass

from trench.domain.entities import Team
from trench.domain.league import Franchise
from trench.domain.repositories import TeamRepository


@dataclass(frozen=True, slots=True, kw_only=True)
class SeedResult:
    created: tuple[str, ...]
    skipped: tuple[str, ...]


async def seed_teams(
    teams: TeamRepository, franchises: Iterable[Franchise]
) -> SeedResult:
    created: list[str] = []
    skipped: list[str] = []
    for franchise in franchises:
        if await teams.get_by_abbreviation(franchise.abbreviation):
            skipped.append(franchise.abbreviation)
            continue
        await teams.save(
            Team(
                name=franchise.name,
                abbreviation=franchise.abbreviation,
                conference=franchise.conference,
                division=franchise.division,
            )
        )
        created.append(franchise.abbreviation)
    return SeedResult(created=tuple(created), skipped=tuple(skipped))
