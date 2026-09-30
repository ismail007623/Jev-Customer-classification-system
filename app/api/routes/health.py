from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_db
from app.utils.responses import error_response, success_response

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Running health check")
        db_status = "connected"

        try:
            await db.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        except Exception as db_exc:
            logger.error("Database health check failed: %s", db_exc)
            db_status = "disconnected"

        jev_status = "unknown"
        openai_status = "unknown"
        try:
            from app.services.jev_service import get_jev_classifier_service
            from app.services.llm_service import get_llm_service

            jev_status = (
                "connected"
                if await get_jev_classifier_service().verify_connection()
                else "auth_failed"
            )
            openai_status = (
                "connected"
                if await get_llm_service().verify_connection()
                else "auth_failed"
            )
        except Exception as exc:
            logger.error("External API health check failed: %s", exc)
            jev_status = "error"
            openai_status = "error"

        return success_response(
            data={
                "status": "healthy",
                "service": settings.APP_NAME,
                "database": db_status,
                "jev": jev_status,
                "openai": openai_status,
            },
            message="Health check completed successfully",
        )

    except Exception as e:
        logger.error("Error during health check: %s", e)
        return error_response(
            message=f"Error during health check: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
