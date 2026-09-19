from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from trench.domain.entities import Player, PlayerGameStats
from trench.domain.enums import Position

QUALIFYING_CARRIES_PER_TEAM_GAME = 6.25


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerSeason:
    player: Player
    games: int
    passing_touchdowns: int
    rushing_attempts: int
    rushing_yards: int
    sacks: float

    @property
    def yards_per_carry(self) -> float | None:
        if self.rushing_attempts == 0:
            return None
        return self.rushing_yards / self.rushing_attempts


@dataclass(frozen=True, slots=True, kw_only=True)
class SeasonLeaders:
    passing_touchdowns: tuple[PlayerSeason, ...]
    yards_per_carry: tuple[PlayerSeason, ...]
    sacks: tuple[PlayerSeason, ...]


def aggregate_seasons(
    stats: Iterable[PlayerGameStats], players: Mapping[UUID, Player]
) -> list[PlayerSeason]:
    lines: dict[UUID, list[PlayerGameStats]] = defaultdict(list)
    for line in stats:
        lines[line.player_id].append(line)
    return [
        PlayerSeason(
            player=players[player_id],
            games=len(player_lines),
            passing_touchdowns=sum(line.passing_touchdowns for line in player_lines),
            rushing_attempts=sum(line.rushing_attempts for line in player_lines),
            rushing_yards=sum(line.rushing_yards for line in player_lines),
            sacks=sum(line.sacks for line in player_lines),
        )
        for player_id, player_lines in lines.items()
    ]


def season_leaders(
    seasons: Iterable[PlayerSeason],
    *,
    team_games: Mapping[UUID, int],
    limit: int,
    qualifying_carries: float = QUALIFYING_CARRIES_PER_TEAM_GAME,
) -> SeasonLeaders:
    candidates = list(seasons)

    def qualified_rusher(season: PlayerSeason) -> bool:
        minimum = qualifying_carries * team_games.get(season.player.team_id, 0)
        return (
            season.player.position is Position.RB
            and season.rushing_attempts > 0
            and season.rushing_attempts >= minimum
        )

    return SeasonLeaders(
        passing_touchdowns=_top(
            (s for s in candidates if s.passing_touchdowns > 0),
            key=lambda s: s.passing_touchdowns,
            limit=limit,
        ),
        yards_per_carry=_top(
            (s for s in candidates if qualified_rusher(s)),
            key=lambda s: s.rushing_yards / s.rushing_attempts,
            limit=limit,
        ),
        sacks=_top(
            (s for s in candidates if s.sacks > 0),
            key=lambda s: s.sacks,
            limit=limit,
        ),
    )


def _top(
    seasons: Iterable[PlayerSeason],
    *,
    key: Callable[[PlayerSeason], float],
    limit: int,
) -> tuple[PlayerSeason, ...]:
    ranked = sorted(seasons, key=lambda s: (-key(s), s.games, s.player.name))
    return tuple(ranked[:limit])
