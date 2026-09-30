from app.core.logging import get_logger
from app.graph.state import SupportTicketState
from app.services.jev_service import JevClassifierService
from app.services.llm_service import get_llm_service


logger = get_logger(__name__)


# Use your configured Jev service
jev_service = JevClassifierService()


async def classify_ticket_node(state: SupportTicketState) -> dict:
    ticket_id = state["ticket_id"]

    logger.info(
        "Classifying ticket: %s",
        ticket_id,
    )

    classification = await jev_service.classify_ticket(
        subject=state["subject"],
        message=state["message"],
    )

    return {
        "category": classification.category,
        "confidence": classification.confidence,
    }


async def billing_response_node(state: SupportTicketState) -> dict:
    ticket_id = state["ticket_id"]

    logger.info(
        "Routing ticket %s -> billing",
        ticket_id,
    )

    logger.info(
        "Generating response for ticket %s",
        ticket_id,
    )

    response = await get_llm_service().generate_billing_response(
        subject=state["subject"],
        message=state["message"],
        category=state["category"] or "billing",
    )

    return {
        "generated_response": response
    }


async def technical_response_node(state: SupportTicketState) -> dict:
    ticket_id = state["ticket_id"]

    logger.info(
        "Routing ticket %s -> technical",
        ticket_id,
    )

    logger.info(
        "Generating response for ticket %s",
        ticket_id,
    )

    response = await get_llm_service().generate_technical_response(
        subject=state["subject"],
        message=state["message"],
        category=state["category"] or "technical",
    )

    return {
        "generated_response": response
    }


async def save_response_node(state: SupportTicketState) -> dict:

    logger.info(
        "Saving response for ticket %s",
        state["ticket_id"],
    )

    return {
        "status": "completed"
    }