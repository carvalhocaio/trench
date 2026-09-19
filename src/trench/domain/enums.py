from enum import StrEnum


class Conference(StrEnum):
    AFC = "AFC"
    NFC = "NFC"


class Division(StrEnum):
    EAST = "EAST"
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    WEST = "WEST"


class Unit(StrEnum):
    OFFENSE = "OFFENSE"
    DEFENSE = "DEFENSE"
    SPECIAL_TEAMS = "SPECIAL_TEAMS"


class Position(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    OL = "OL"
    DL = "DL"
    EDGE = "EDGE"
    LB = "LB"
    CB = "CB"
    S = "S"
    K = "K"
    P = "P"

    @property
    def unit(self) -> Unit:
        return _POSITION_UNITS[self]


_POSITION_UNITS: dict[Position, Unit] = {
    Position.QB: Unit.OFFENSE,
    Position.RB: Unit.OFFENSE,
    Position.WR: Unit.OFFENSE,
    Position.TE: Unit.OFFENSE,
    Position.OL: Unit.OFFENSE,
    Position.DL: Unit.DEFENSE,
    Position.EDGE: Unit.DEFENSE,
    Position.LB: Unit.DEFENSE,
    Position.CB: Unit.DEFENSE,
    Position.S: Unit.DEFENSE,
    Position.K: Unit.SPECIAL_TEAMS,
    Position.P: Unit.SPECIAL_TEAMS,
}


class GameStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    FINAL = "FINAL"


class AbsenceStatus(StrEnum):
    OUT = "OUT"
    DOUBTFUL = "DOUBTFUL"
    QUESTIONABLE = "QUESTIONABLE"
