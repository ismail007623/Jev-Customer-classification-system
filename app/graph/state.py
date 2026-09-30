from typing import Optional, TypedDict


class SupportTicketState(TypedDict):
    ticket_id: int
    subject: str
    message: str
    category: Optional[str]
    confidence: Optional[float]
    generated_response: Optional[str]
    status: str
    error: Optional[str]
    processing_time_ms: Optional[int]
