from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

TicketCategory = Literal["billing", "technical"]
TicketStatus = Literal["pending", "processing", "completed", "failed"]


class TicketCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_email: EmailStr
    subject: str = Field(..., min_length=3, max_length=500)
    message: str = Field(..., min_length=10)


class TicketResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    subject: str
    message: str
    category: TicketCategory | None
    classification_confidence: float | None
    generated_response: str | None
    status: TicketStatus
    processing_time_ms: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    subject: str
    category: TicketCategory | None
    classification_confidence: float | None
    status: TicketStatus
    processing_time_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketListData(BaseModel):
    items: list[TicketListItem]
    page: int
    page_size: int
    total: int


ApiEnvelopeStatus = Literal["success", "error"]


class ApiResponse(BaseModel):
    status: ApiEnvelopeStatus
    message: str
    data: TicketResponse | TicketListData | dict | None = None


class ApiErrorResponse(BaseModel):
    status: ApiEnvelopeStatus = "error"
    message: str
    data: None = None


class TestLLM(BaseModel):
    name: str 
    subject: str
    issue: str

class ResponseLLM(BaseModel):
    intent: Literal["billing", "technical"]
