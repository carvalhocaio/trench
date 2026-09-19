from fastapi import APIRouter, Query

from trench.api.dependencies import HighlightsServiceDep
from trench.api.schemas import HighlightsRead

router = APIRouter(tags=["highlights"])


@router.get("/highlights")
async def season_highlights(
    highlights: HighlightsServiceDep,
    season: int,
    limit: int = Query(default=5, ge=1, le=32),
) -> HighlightsRead:
    leaders = await highlights.season(season, limit=limit)
    return HighlightsRead.from_leaders(season, leaders)
