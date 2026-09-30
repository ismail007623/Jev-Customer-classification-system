from openai import AsyncOpenAI, AuthenticationError

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# SYSTEM PROMPTS
# =========================================================

BILLING_SYSTEM_PROMPT = """
You are a professional customer support assistant.

The ticket has already been classified as BILLING.

Respond to the customer's issue clearly and professionally.

Do not claim that a refund has been issued.
Do not claim that payment records were checked.
Do not invent account information.
Do not say that you accessed the customer's account.

Since this is a demo and there are no actual billing tools,
provide helpful next steps based only on the customer's message.

Keep the response concise.
"""


TECHNICAL_SYSTEM_PROMPT = """
You are a professional technical support assistant.

The ticket has already been classified as TECHNICAL.

Respond with useful troubleshooting guidance.

Do not claim that you checked logs, databases, user accounts,
or servers unless such information was explicitly provided.

Use only the information included in the ticket.

Keep the response concise and actionable.
"""


# =========================================================
# LLM SERVICE
# =========================================================

class LLMService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    # =====================================================
    # VERIFY CONNECTION
    # =====================================================

    async def verify_connection(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Reply only with OK"}],
                max_tokens=5,
            )
            return True
        except Exception as exc:
            logger.error("OpenAI connection verification failed: %s", exc)
            return False

    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    async def _generate_response(
        self,
        system_prompt: str,
        subject: str,
        message: str,
        category: str,
    ) -> str:

        user_content = (
            f"Ticket Category: {category.upper()}\n"
            f"Subject: {subject}\n"
            f"Message: {message}"
        )

        try:
            logger.info("Generating %s support response via OpenAI", category)

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError("OpenAI returned an empty response")

            logger.info("Successfully generated %s support response", category)
            return content.strip()

        except AuthenticationError as exc:
            logger.error("OpenAI authentication failed: %s", exc)
            raise RuntimeError(
                "OpenAI authentication failed. Check OPENAI_API_KEY in backend/.env."
            ) from exc
        except Exception as exc:
            logger.error("Error generating %s support response: %s", category, exc)
            raise RuntimeError(f"Failed to generate {category} response") from exc

    # =====================================================
    # BILLING
    # =====================================================

    async def generate_billing_response(
        self,
        subject: str,
        message: str,
        category: str = "billing",
    ) -> str:

        return await self._generate_response(
            system_prompt=BILLING_SYSTEM_PROMPT,
            subject=subject,
            message=message,
            category=category,
        )

    # =====================================================
    # TECHNICAL
    # =====================================================

    async def generate_technical_response(
        self,
        subject: str,
        message: str,
        category: str = "technical",
    ) -> str:

        return await self._generate_response(
            system_prompt=TECHNICAL_SYSTEM_PROMPT,
            subject=subject,
            message=message,
            category=category,
        )


# =========================================================
# SINGLETON
# =========================================================

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:

    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService()

    return _llm_service
