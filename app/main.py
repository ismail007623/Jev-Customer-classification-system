from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.database.base import Base
from app.database.session import engine
from app.services.jev_service import JevClassifierService
from app.utils.exceptions import AppError
from app.utils.responses import error_response


logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    logger.error("Application error: %s", exc.message)

    return error_response(
        message=exc.message,
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def generic_error_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc)

    return error_response(
        message="An unexpected error occurred",
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
    )