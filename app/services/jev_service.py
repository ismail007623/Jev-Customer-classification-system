from dataclasses import dataclass
from typing import Literal

from typesafe_sdk import AsyncTypeSafeClient, Choice

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import ClassificationError


logger = get_logger(__name__)

TicketCategory = Literal["billing", "technical"]

ALLOWED_CATEGORIES = {
    "billing",
    "technical",
}


@dataclass
class TicketClassification:
    category: TicketCategory
    confidence: float


class JevClassifierService:

    def __init__(self) -> None:
        self._model = settings.JEV_MODEL

        self._client = AsyncTypeSafeClient(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api",
        )

    async def classify_ticket(
        self,
        subject: str,
        message: str,
    ) -> TicketClassification:

        state = (
            f"Subject: {subject}\n\n"
            f"Message: {message}"
        )

        logger.info(
            "Sending ticket to Jev through OpenRouter"
        )

        try:
            result = await self._client.system_one(
                model=self._model,
                state=state,
                questions={
                    "category": Choice(
                        instructions=(
                            "Classify this customer support ticket "
                            "into the correct category."
                        ),
                        criteria={
                            "billing": (
                                "Payments, charges, refunds, invoices, "
                                "subscriptions and billing disputes."
                            ),
                            "technical": (
                                "Bugs, errors, login issues, "
                                "features not working and server errors."
                            ),
                        },
                    )
                },
            )

        except Exception as exc:
            logger.exception(
                "Error while classifying ticket with Jev"
            )

            raise ClassificationError(
                f"Jev classification failed: {exc}"
            ) from exc

        answer = result.answers["category"]

        category = answer.choice.strip().lower()

        if category not in ALLOWED_CATEGORIES:
            raise ClassificationError(
                f"Unexpected category from Jev: {category}"
            )

        confidence = float(answer.confidence)

        logger.info(
            "Ticket classified: category=%s confidence=%.2f",
            category,
            confidence,
        )

        return TicketClassification(
            category=category,
            confidence=confidence,
        )

    async def close(self) -> None:
        await self._client.aclose()