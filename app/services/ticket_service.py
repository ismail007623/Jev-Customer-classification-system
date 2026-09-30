import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.graph.support_graph import support_graph
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreateRequest
from app.utils.exceptions import NotFoundError

logger = get_logger(__name__)


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _run_graph(self, ticket: Ticket) -> Ticket:
        start_time = time.perf_counter()

        try:
            logger.info("Running LangGraph pipeline for ticket %s", ticket.id)

            initial_state = {
                "ticket_id": ticket.id,
                "subject": ticket.subject,
                "message": ticket.message,
                "category": ticket.category,
                "confidence": ticket.classification_confidence,
                "generated_response": ticket.generated_response,
                "status": "processing",
                "error": None,
                "processing_time_ms": None,
            }

            result = await support_graph.ainvoke(initial_state)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            ticket.category = result.get("category")
            ticket.classification_confidence = result.get("confidence")
            ticket.generated_response = result.get("generated_response")
            ticket.status = result.get("status", "completed")
            ticket.processing_time_ms = elapsed_ms

            await self.db.commit()
            await self.db.refresh(ticket)

            logger.info("Ticket processing completed in %s ms", elapsed_ms)
            return ticket

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            ticket.status = "failed"
            ticket.processing_time_ms = elapsed_ms
            await self.db.commit()
            await self.db.refresh(ticket)
            logger.error("Error while processing ticket %s through LangGraph: %s", ticket.id, e)
            raise Exception(f"Error while processing ticket through LangGraph: {e}") from e

    async def create_ticket(self, data: TicketCreateRequest) -> Ticket:
        try:
            logger.info("Creating ticket in database")

            ticket = Ticket(
                customer_name=data.customer_name,
                customer_email=str(data.customer_email),
                subject=data.subject,
                message=data.message,
                status="processing",
            )
            self.db.add(ticket)
            await self.db.commit()
            await self.db.refresh(ticket)

            logger.info("Ticket created: %s", ticket.id)

            try:
                return await self._run_graph(ticket)
            except Exception:
                return ticket

        except Exception as e:
            logger.error("Database error while creating ticket: %s", e)
            raise Exception(f"Database error while creating ticket: {e}") from e

    async def get_ticket(self, ticket_id: int) -> Ticket:
        try:
            logger.info("Fetching ticket %s from database", ticket_id)

            result = await self.db.execute(select(Ticket).where(Ticket.id == ticket_id))
            ticket = result.scalar_one_or_none()

            if ticket is None:
                logger.error("Ticket %s not found", ticket_id)
                raise NotFoundError("Ticket not found")

            logger.info("Successfully fetched ticket %s", ticket_id)
            return ticket

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Database error while fetching ticket %s: %s", ticket_id, e)
            raise Exception(f"Database error while fetching ticket: {e}") from e

    async def list_tickets(
        self,
        category: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ticket], int]:
        try:
            logger.info("Fetching tickets from database")

            query = select(Ticket)
            count_query = select(func.count()).select_from(Ticket)

            if category:
                query = query.where(Ticket.category == category)
                count_query = count_query.where(Ticket.category == category)
            if status:
                query = query.where(Ticket.status == status)
                count_query = count_query.where(Ticket.status == status)

            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()

            offset = (page - 1) * page_size
            query = query.order_by(Ticket.created_at.desc()).offset(offset).limit(page_size)

            result = await self.db.execute(query)
            tickets = list(result.scalars().all())

            logger.info("Successfully fetched %s tickets from database", len(tickets))
            return tickets, total

        except Exception as e:
            logger.error("Database error while listing tickets: %s", e)
            raise Exception(f"Database error while listing tickets: {e}") from e

    async def reprocess_ticket(self, ticket_id: int) -> Ticket:
        try:
            logger.info("Preparing ticket %s for reprocessing", ticket_id)

            ticket = await self.get_ticket(ticket_id)

            ticket.status = "processing"
            ticket.category = None
            ticket.classification_confidence = None
            ticket.generated_response = None
            ticket.processing_time_ms = None
            await self.db.commit()
            await self.db.refresh(ticket)

            logger.info("Reprocessing ticket: %s", ticket.id)

            try:
                return await self._run_graph(ticket)
            except Exception:
                return ticket

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error while reprocessing ticket %s: %s", ticket_id, e)
            raise Exception(f"Error while reprocessing ticket: {e}") from e
