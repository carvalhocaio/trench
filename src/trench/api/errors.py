from collections.abc import Awaitable, Callable
from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from trench.analytics.errors import InsufficientDataError
from trench.application.errors import (
    NotFoundError,
    ScheduleConflictError,
    TeamNotInGameError,
)
from trench.application.previews import PreviewUnavailableError
from trench.domain.errors import DomainValidationError, GameNotStartedError

type ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    TEAM_NOT_IN_GAME = "team_not_in_game"
    NOT_FOUND = "not_found"
    SCHEDULE_CONFLICT = "schedule_conflict"
    INSUFFICIENT_DATA = "insufficient_data"
    PREVIEW_UNAVAILABLE = "preview_unavailable"
    GAME_NOT_STARTED = "game_not_started"
    CONFLICT = "conflict"


STATUS_BY_ERROR: dict[type[Exception], tuple[int, ErrorCode]] = {
    DomainValidationError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.VALIDATION_ERROR,
    ),
    TeamNotInGameError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.TEAM_NOT_IN_GAME,
    ),
    NotFoundError: (status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND),
    ScheduleConflictError: (status.HTTP_409_CONFLICT, ErrorCode.SCHEDULE_CONFLICT),
    InsufficientDataError: (status.HTTP_409_CONFLICT, ErrorCode.INSUFFICIENT_DATA),
    PreviewUnavailableError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.PREVIEW_UNAVAILABLE,
    ),
    GameNotStartedError: (status.HTTP_409_CONFLICT, ErrorCode.GAME_NOT_STARTED),
}


def register_exception_handlers(app: FastAPI) -> None:
    for error_type, (status_code, code) in STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _responder(status_code, code))
    app.add_exception_handler(
        IntegrityError,
        _responder(
            status.HTTP_409_CONFLICT,
            ErrorCode.CONFLICT,
            "resource conflicts with existing data",
        ),
    )


def _responder(
    status_code: int, code: ErrorCode, detail: str | None = None
) -> ExceptionHandler:
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail or str(exc), "code": code},
        )

    return handle
