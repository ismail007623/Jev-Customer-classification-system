from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse


def success_response(
    data: Any,
    message: str,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        content={
            "data": data,
            "message": message,
            "status": "success",
        },
        status_code=status_code,
    )


def error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    return JSONResponse(
        content={
            "data": None,
            "message": message,
            "status": "error",
        },
        status_code=status_code,
    )
