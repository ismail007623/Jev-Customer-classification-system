
import json
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.ticket import TicketCreateRequest, TicketListData, TicketListItem, TicketResponse ,TestLLM , ResponseLLM
from app.services.ticket_service import TicketService
from app.core.logging import get_logger
from app.utils.exceptions import NotFoundError
from app.utils.classification import get_ticket_itent 
from app.utils.redis_cache import generate_ticket_cache_key
from app.utils.responses import error_response, success_response
from app.core.redis import redis_client

logger = get_logger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_service(db: AsyncSession = Depends(get_db)) -> TicketService:
    return TicketService(db)


@router.post("")
async def create_ticket(
    payload: TicketCreateRequest,
    service: TicketService = Depends(get_ticket_service),
):
    try:
        logger.info("Creating and processing ticket")

        ticket = await service.create_ticket(payload)
        message = (
            "Ticket processed successfully"
            if ticket.status == "completed"
            else "Ticket created but processing failed"
        )

        logger.info("Ticket %s processed with status=%s", ticket.id, ticket.status)

        return success_response(
            data=TicketResponse.model_validate(ticket).model_dump(mode="json"),
            message=message,
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error("Error while creating ticket: %s", e)
        return error_response(
            message=f"Error while creating ticket: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("")
async def list_tickets(
    category: Literal["billing", "technical"] | None = None,
    status_filter: Literal["pending", "processing", "completed", "failed"] | None = Query(
        None, alias="status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: TicketService = Depends(get_ticket_service),
):
    try:
        logger.info(
            "Listing tickets (category=%s, status=%s, page=%s, page_size=%s)",
            category,
            status_filter,
            page,
            page_size,
        )

        tickets, total = await service.list_tickets(
            category=category,
            status=status_filter,
            page=page,
            page_size=page_size,
        )

        data = TicketListData(
            items=[TicketListItem.model_validate(t) for t in tickets],
            page=page,
            page_size=page_size,
            total=total,
        )

        logger.info("Successfully fetched %s tickets", len(tickets))

        return success_response(
            data=data.model_dump(mode="json"),
            message="Tickets fetched successfully",
        )

    except Exception as e:
        logger.error("Error while listing tickets: %s", e)
        return error_response(
            message=f"Error while listing tickets: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
):
    try:
        logger.info("Fetching ticket %s", ticket_id)

        ticket = await service.get_ticket(ticket_id)

        logger.info("Successfully fetched ticket %s", ticket_id)

        return success_response(
            data=TicketResponse.model_validate(ticket).model_dump(mode="json"),
            message="Ticket fetched successfully",
        )

    except NotFoundError as e:
        logger.error("Ticket not found: %s", e)
        return error_response(
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        logger.error("Error while fetching ticket %s: %s", ticket_id, e)
        return error_response(
            message=f"Error while fetching ticket: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/{ticket_id}/reprocess")
async def reprocess_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
):
    try:
        logger.info("Reprocessing ticket %s", ticket_id)

        ticket = await service.reprocess_ticket(ticket_id)
        message = (
            "Ticket reprocessed successfully"
            if ticket.status == "completed"
            else "Ticket reprocessing failed"
        )

        logger.info("Ticket %s reprocessed with status=%s", ticket_id, ticket.status)

        return success_response(
            data=TicketResponse.model_validate(ticket).model_dump(mode="json"),
            message=message,
        )

    except NotFoundError as e:
        logger.error("Ticket not found for reprocess: %s", e)
        return error_response(
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        logger.error("Error while reprocessing ticket %s: %s", ticket_id, e)
        return error_response(
            message=f"Error while reprocessing ticket: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@router.post("llm-classifier")
async def create_ticket(payload:TestLLM):
    """
    """
    try:
        logger.info("Entring into LLM classification Endpoint")
        name = payload.name
        subject = payload.subject
        issue = payload.issue

        cache_key = generate_ticket_cache_key(
            subject=subject,
            issue=issue
        )

        cached_response = await redis_client.get(cache_key)

        if cached_response:
            logger.info("Ticket classification returned from Redis cache")

            cached_data = json.loads(cached_response)

            return success_response(
                data={
                    "result": cached_data["result"],
                    "source": "cache",
                    "token_usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0
                    }
                },
                message="Classification successfully completed",
                status_code=status.HTTP_200_OK
            )

        llm_response = await get_ticket_itent(name , subject , issue)

        await redis_client.set(cache_key,json.dumps(llm_response), ex=86400)


        logger.info("Classification successfully completed")
        return success_response(
            data = llm_response , message="Classification successfully completed" , status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Classifcation API failed : {e}")
        return error_response(
            message=f"Classifcation API failed : {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



