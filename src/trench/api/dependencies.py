from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trench.application.injuries import InjuryReportService
from trench.application.predictions import PredictionService
from trench.application.roster import RosterService
from trench.application.schedule import ScheduleService
from trench.application.stats import GameStatsService
from trench.config import AnalyticsSettings, get_analytics_settings
from trench.domain.repositories import (
    AbsenceRepository,
    GameRepository,
    PlayerGameStatsRepository,
    PlayerRepository,
    PredictionSnapshotRepository,
    TeamGameStatsRepository,
    TeamRepository,
)
from trench.infrastructure.repositories.absences import SqlAbsenceRepository
from trench.infrastructure.repositories.games import SqlGameRepository
from trench.infrastructure.repositories.player_stats import (
    SqlPlayerGameStatsRepository,
)
from trench.infrastructure.repositories.players import SqlPlayerRepository
from trench.infrastructure.repositories.predictions import (
    SqlPredictionSnapshotRepository,
)
from trench.infrastructure.repositories.team_stats import SqlTeamGameStatsRepository
from trench.infrastructure.repositories.teams import SqlTeamRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session, session.begin():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_team_repository(session: SessionDep) -> TeamRepository:
    return SqlTeamRepository(session)


TeamRepositoryDep = Annotated[TeamRepository, Depends(get_team_repository)]


def get_game_repository(session: SessionDep) -> GameRepository:
    return SqlGameRepository(session)


GameRepositoryDep = Annotated[GameRepository, Depends(get_game_repository)]


def get_player_repository(session: SessionDep) -> PlayerRepository:
    return SqlPlayerRepository(session)


PlayerRepositoryDep = Annotated[PlayerRepository, Depends(get_player_repository)]


def get_team_stats_repository(session: SessionDep) -> TeamGameStatsRepository:
    return SqlTeamGameStatsRepository(session)


TeamStatsRepositoryDep = Annotated[
    TeamGameStatsRepository, Depends(get_team_stats_repository)
]


def get_player_stats_repository(session: SessionDep) -> PlayerGameStatsRepository:
    return SqlPlayerGameStatsRepository(session)


PlayerStatsRepositoryDep = Annotated[
    PlayerGameStatsRepository, Depends(get_player_stats_repository)
]


def get_absence_repository(session: SessionDep) -> AbsenceRepository:
    return SqlAbsenceRepository(session)


AbsenceRepositoryDep = Annotated[AbsenceRepository, Depends(get_absence_repository)]


def get_snapshot_repository(session: SessionDep) -> PredictionSnapshotRepository:
    return SqlPredictionSnapshotRepository(session)


SnapshotRepositoryDep = Annotated[
    PredictionSnapshotRepository, Depends(get_snapshot_repository)
]

AnalyticsSettingsDep = Annotated[AnalyticsSettings, Depends(get_analytics_settings)]


def get_schedule_service(
    teams: TeamRepositoryDep, games: GameRepositoryDep
) -> ScheduleService:
    return ScheduleService(teams=teams, games=games)


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]


def get_roster_service(
    teams: TeamRepositoryDep, players: PlayerRepositoryDep
) -> RosterService:
    return RosterService(teams=teams, players=players)


RosterServiceDep = Annotated[RosterService, Depends(get_roster_service)]


def get_game_stats_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    team_stats: TeamStatsRepositoryDep,
    player_stats: PlayerStatsRepositoryDep,
) -> GameStatsService:
    return GameStatsService(
        games=games,
        players=players,
        team_stats=team_stats,
        player_stats=player_stats,
    )


GameStatsServiceDep = Annotated[GameStatsService, Depends(get_game_stats_service)]


def get_injury_report_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    absences: AbsenceRepositoryDep,
) -> InjuryReportService:
    return InjuryReportService(games=games, players=players, absences=absences)


InjuryReportServiceDep = Annotated[
    InjuryReportService, Depends(get_injury_report_service)
]


def get_prediction_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    absences: AbsenceRepositoryDep,
    snapshots: SnapshotRepositoryDep,
    settings: AnalyticsSettingsDep,
) -> PredictionService:
    return PredictionService(
        games=games,
        players=players,
        absences=absences,
        snapshots=snapshots,
        settings=settings,
    )


PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
