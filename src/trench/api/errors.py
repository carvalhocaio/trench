from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from trench.analytics.errors import InsufficientDataError
from trench.application.previews import PreviewUnavailableError
from trench.application.errors import (
    NotFoundError,
    ScheduleConflictError,
    TeamNotInGameError,
)
from trench.domain.errors import DomainValidationError

type ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

STATUS_BY_ERROR: dict[type[Exception], int] = {
    DomainValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    TeamNotInGameError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ScheduleConflictError: status.HTTP_409_CONFLICT,
    InsufficientDataError: status.HTTP_409_CONFLICT,
    PreviewUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def register_exception_handlers(app: FastAPI) -> None:
    for error_type, status_code in STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _responder(status_code))
    app.add_exception_handler(
        IntegrityError,
        _responder(status.HTTP_409_CONFLICT, "resource conflicts with existing data"),
    )


def _responder(status_code: int, detail: str | None = None) -> ExceptionHandler:
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code, content={"detail": detail or str(exc)}
        )

    return handle
