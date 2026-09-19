from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trench.agent.models import build_model
from trench.agent.preview import AgentPreviewWriter, create_preview_agent
from trench.application.calibration import CalibrationService
from trench.application.highlights import HighlightsService
from trench.application.injuries import InjuryReportService
from trench.application.predictions import PredictionService
from trench.application.previews import (
    CachingPreviewWriter,
    PreviewService,
    PreviewUnavailableError,
    PreviewWriter,
)
from trench.application.roster import RosterService
from trench.application.schedule import ScheduleService
from trench.application.stats import GameStatsService
from trench.config import AnalyticsSettings, get_analytics_settings, get_llm_settings
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


def get_calibration_settings(
    settings: AnalyticsSettingsDep,
    shrinkage_games: float | None = Query(default=None, gt=0),
    home_field_advantage: float | None = Query(default=None, ge=-10, le=10),
    score_margin_stddev: float | None = Query(default=None, gt=0),
) -> AnalyticsSettings:
    overrides = {
        key: value
        for key, value in (
            ("shrinkage_games", shrinkage_games),
            ("home_field_advantage", home_field_advantage),
            ("score_margin_stddev", score_margin_stddev),
        )
        if value is not None
    }
    return settings.model_copy(update=overrides) if overrides else settings


CalibrationSettingsDep = Annotated[AnalyticsSettings, Depends(get_calibration_settings)]


def get_calibration_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    absences: AbsenceRepositoryDep,
    snapshots: SnapshotRepositoryDep,
    settings: CalibrationSettingsDep,
) -> CalibrationService:
    predictions = PredictionService(
        games=games,
        players=players,
        absences=absences,
        snapshots=snapshots,
        settings=settings,
    )
    return CalibrationService(predictions=predictions, games=games, snapshots=snapshots)


CalibrationServiceDep = Annotated[CalibrationService, Depends(get_calibration_service)]


def get_highlights_service(
    games: GameRepositoryDep,
    players: PlayerRepositoryDep,
    player_stats: PlayerStatsRepositoryDep,
) -> HighlightsService:
    return HighlightsService(games=games, players=players, player_stats=player_stats)


HighlightsServiceDep = Annotated[HighlightsService, Depends(get_highlights_service)]


@lru_cache
def get_preview_writer() -> PreviewWriter:
    try:
        settings = get_llm_settings()
    except ValidationError as error:
        raise PreviewUnavailableError(
            "LLM is not configured: set GOOGLE_API_KEY"
        ) from error
    agent = create_preview_agent(build_model(settings), language=settings.language)
    return CachingPreviewWriter(
        AgentPreviewWriter(agent), max_entries=settings.preview_cache_size
    )


PreviewWriterDep = Annotated[PreviewWriter, Depends(get_preview_writer)]


def get_preview_service(
    predictions: PredictionServiceDep,
    highlights: HighlightsServiceDep,
    teams: TeamRepositoryDep,
    writer: PreviewWriterDep,
) -> PreviewService:
    return PreviewService(
        predictions=predictions, highlights=highlights, teams=teams, writer=writer
    )


PreviewServiceDep = Annotated[PreviewService, Depends(get_preview_service)]
