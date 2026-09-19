from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    MetaData,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

from trench.domain.entities import MAX_WEEK
from trench.domain.enums import AbsenceStatus, Conference, Division, Position

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _enum_column(enum_class: type[StrEnum]) -> Enum:
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=True,
        length=max(len(member.value) for member in enum_class),
        values_callable=lambda members: [member.value for member in members],
    )


def _non_negative(*columns: str) -> tuple[CheckConstraint, ...]:
    return tuple(
        CheckConstraint(f"{column} >= 0", name=f"{column}_non_negative")
        for column in columns
    )


class Base(DeclarativeBase):
    registry = registry(
        metadata=MetaData(naming_convention=NAMING_CONVENTION),
        type_annotation_map={datetime: DateTime(timezone=True)},
    )


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    abbreviation: Mapped[str] = mapped_column(String(4), unique=True)
    conference: Mapped[Conference] = mapped_column(_enum_column(Conference))
    division: Mapped[Division] = mapped_column(_enum_column(Division))


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    position: Mapped[Position] = mapped_column(_enum_column(Position))


class GameModel(Base):
    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint(f"week BETWEEN 1 AND {MAX_WEEK}", name="week_range"),
        CheckConstraint("home_team_id <> away_team_id", name="distinct_teams"),
        CheckConstraint(
            "(home_score IS NULL) = (away_score IS NULL)", name="complete_score"
        ),
        *_non_negative("home_score", "away_score"),
        UniqueConstraint("season", "week", "home_team_id"),
        UniqueConstraint("season", "week", "away_team_id"),
        Index("ix_games_season_week", "season", "week"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    season: Mapped[int]
    week: Mapped[int]
    kickoff: Mapped[datetime]
    home_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    home_score: Mapped[int | None]
    away_score: Mapped[int | None]


class TeamGameStatsModel(Base):
    __tablename__ = "team_game_stats"
    __table_args__ = _non_negative("offensive_plays", "turnovers", "sacks")

    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    offensive_plays: Mapped[int]
    passing_yards: Mapped[int]
    rushing_yards: Mapped[int]
    turnovers: Mapped[int]
    sacks: Mapped[int]


class PlayerGameStatsModel(Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (
        *_non_negative("passing_touchdowns", "rushing_attempts", "sacks"),
        CheckConstraint("sacks * 2 = floor(sacks * 2)", name="half_sacks"),
    )

    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    passing_touchdowns: Mapped[int] = mapped_column(default=0)
    rushing_attempts: Mapped[int] = mapped_column(default=0)
    rushing_yards: Mapped[int] = mapped_column(default=0)
    sacks: Mapped[float] = mapped_column(default=0.0)


class AbsenceModel(Base):
    __tablename__ = "absences"

    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), primary_key=True)
    status: Mapped[AbsenceStatus] = mapped_column(_enum_column(AbsenceStatus))


class PredictionSnapshotModel(Base):
    __tablename__ = "prediction_snapshots"
    __table_args__ = (
        *_non_negative("home_projected_points", "away_projected_points"),
        CheckConstraint(
            "home_win_probability BETWEEN 0 AND 1", name="probability_range"
        ),
        Index("ix_prediction_snapshots_game_id_as_of", "game_id", "as_of"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    as_of: Mapped[datetime]
    home_projected_points: Mapped[float]
    away_projected_points: Mapped[float]
    home_win_probability: Mapped[float]
    model_version: Mapped[str] = mapped_column(String(32))
