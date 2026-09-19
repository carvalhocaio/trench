import pytest

from trench.domain.enums import Position, Unit


def test_every_position_belongs_to_a_unit() -> None:
    assert all(isinstance(position.unit, Unit) for position in Position)


@pytest.mark.parametrize(
    ("position", "unit"),
    [
        (Position.QB, Unit.OFFENSE),
        (Position.EDGE, Unit.DEFENSE),
        (Position.K, Unit.SPECIAL_TEAMS),
    ],
)
def test_position_unit(position: Position, unit: Unit) -> None:
    assert position.unit is unit
