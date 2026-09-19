from uuid import UUID

from fastapi import APIRouter, status

from trench.api.dependencies import InjuryReportServiceDep
from trench.api.schemas import AbsencePayload, AbsenceRead, ErrorResponse

router = APIRouter(prefix="/games/{game_id}/absences", tags=["absences"])


@router.get("", responses={404: {"model": ErrorResponse}})
async def list_absences(
    game_id: UUID, report: InjuryReportServiceDep
) -> list[AbsenceRead]:
    return [AbsenceRead.model_validate(a) for a in await report.list_game(game_id)]


@router.put("/{player_id}", responses={404: {"model": ErrorResponse}})
async def report_absence(
    game_id: UUID,
    player_id: UUID,
    payload: AbsencePayload,
    report: InjuryReportServiceDep,
) -> AbsenceRead:
    absence = await report.report(game_id, player_id, payload.status)
    return AbsenceRead.model_validate(absence)


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def clear_absence(
    game_id: UUID, player_id: UUID, report: InjuryReportServiceDep
) -> None:
    await report.clear(game_id, player_id)
