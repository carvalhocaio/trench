from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from trench.domain.entities import Absence, Game, Player
from trench.domain.enums import AbsenceStatus, Position, Unit


@dataclass(frozen=True, slots=True, kw_only=True)
class PointsAdjustment:
    home: float = 0.0
    away: float = 0.0


NO_ADJUSTMENT = PointsAdjustment()


@dataclass(frozen=True, slots=True, kw_only=True)
class AbsenceImpact:
    player: Player
    status: AbsenceStatus
    applies_to_home: bool
    points_delta: float


@dataclass(frozen=True, slots=True, kw_only=True)
class AbsenceReport:
    impacts: tuple[AbsenceImpact, ...]

    @property
    def adjustment(self) -> PointsAdjustment:
        return PointsAdjustment(
            home=sum(i.points_delta for i in self.impacts if i.applies_to_home),
            away=sum(i.points_delta for i in self.impacts if not i.applies_to_home),
        )


def assess_absences(
    game: Game,
    absences: Iterable[Absence],
    players: Mapping[UUID, Player],
    *,
    position_weights: Mapping[Position, float],
    absence_probabilities: Mapping[AbsenceStatus, float],
) -> AbsenceReport:
    impacts = [
        _impact(
            game,
            absence,
            players,
            position_weights=position_weights,
            absence_probabilities=absence_probabilities,
        )
        for absence in absences
    ]
    impacts.sort(key=lambda impact: abs(impact.points_delta), reverse=True)
    return AbsenceReport(impacts=tuple(impacts))


def _impact(
    game: Game,
    absence: Absence,
    players: Mapping[UUID, Player],
    *,
    position_weights: Mapping[Position, float],
    absence_probabilities: Mapping[AbsenceStatus, float],
) -> AbsenceImpact:
    if absence.game_id != game.id:
        raise ValueError(f"absence belongs to game {absence.game_id}, not {game.id}")
    player = players.get(absence.player_id)
    if player is None:
        raise ValueError(f"unknown player {absence.player_id}")

    expected_points = (
        position_weights[player.position] * absence_probabilities[absence.status]
    )
    hurts_own_scoring = player.position.unit is not Unit.DEFENSE
    return AbsenceImpact(
        player=player,
        status=absence.status,
        applies_to_home=game.is_home(player.team_id) == hurts_own_scoring,
        points_delta=-expected_points if hurts_own_scoring else expected_points,
    )
