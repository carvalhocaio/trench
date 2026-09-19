from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from trench.domain.entities import Game, TeamGameStats
from trench.domain.enums import GameStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamEfficiency:
    team_id: UUID
    games_played: int
    yards_per_play: float | None
    yards_per_play_allowed: float | None
    turnover_margin: float
    sacks_made_per_game: float
    sacks_allowed_per_game: float


def pair_with_opponent(
    games: Iterable[Game], stats: Iterable[TeamGameStats]
) -> dict[UUID, list[tuple[TeamGameStats, TeamGameStats]]]:
    """For each team, the list of (own, opponent) TeamGameStats per game they played.

    TeamGameStats always describes its own team's offensive output (sacks
    allowed, yards gained), so anything about a team's defense (sacks made,
    yards allowed) requires reading the opponent's row for the same game_id.
    """
    final_games = {game.id: game for game in games if game.status is GameStatus.FINAL}
    by_game: dict[UUID, dict[UUID, TeamGameStats]] = defaultdict(dict)
    for line in stats:
        if line.game_id in final_games:
            by_game[line.game_id][line.team_id] = line

    pairs: dict[UUID, list[tuple[TeamGameStats, TeamGameStats]]] = defaultdict(list)
    for game_id, by_team in by_game.items():
        game = final_games[game_id]
        home = by_team.get(game.home_team_id)
        away = by_team.get(game.away_team_id)
        if home is None or away is None:
            continue
        pairs[game.home_team_id].append((home, away))
        pairs[game.away_team_id].append((away, home))
    return pairs


def compute_efficiency(
    games: Iterable[Game], stats: Iterable[TeamGameStats]
) -> dict[UUID, TeamEfficiency]:
    """Season-to-date play-style facts for narrative use (no shrinkage).

    Only GameStatus.FINAL games count, matching analytics.ratings.compute_ratings.
    """
    return {
        team_id: _efficiency(team_id, pairs)
        for team_id, pairs in pair_with_opponent(games, stats).items()
    }


def _efficiency(
    team_id: UUID, pairs: list[tuple[TeamGameStats, TeamGameStats]]
) -> TeamEfficiency:
    games_played = len(pairs)
    own_yards_per_play = [
        own.total_yards / own.offensive_plays
        for own, _ in pairs
        if own.offensive_plays > 0
    ]
    opponent_yards_per_play = [
        opponent.total_yards / opponent.offensive_plays
        for _, opponent in pairs
        if opponent.offensive_plays > 0
    ]
    return TeamEfficiency(
        team_id=team_id,
        games_played=games_played,
        yards_per_play=_mean(own_yards_per_play),
        yards_per_play_allowed=_mean(opponent_yards_per_play),
        turnover_margin=sum(
            opponent.turnovers - own.turnovers for own, opponent in pairs
        )
        / games_played,
        sacks_made_per_game=sum(opponent.sacks for _, opponent in pairs) / games_played,
        sacks_allowed_per_game=sum(own.sacks for own, _ in pairs) / games_played,
    )


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
