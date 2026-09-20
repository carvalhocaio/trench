from fastapi import APIRouter

from trench.api.dependencies import CalibrationServiceDep, CalibrationSettingsDep
from trench.api.schemas import CalibrationRead

router = APIRouter(tags=["calibration"])


@router.get("/calibration")
async def get_calibration(
    season: int,
    calibration: CalibrationServiceDep,
    settings: CalibrationSettingsDep,
) -> CalibrationRead:
    return CalibrationRead.build(
        season=season,
        settings=settings,
        backtest=await calibration.backtest(season),
        live=await calibration.live(season),
        home_field_effect=await calibration.home_field_effect(season),
    )
