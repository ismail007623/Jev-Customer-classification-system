from typing import Literal

from app.graph.state import SupportTicketState


def route_ticket(state: SupportTicketState) -> Literal["billing", "technical"]:
    if state.get("category") == "billing":
        return "billing"
    return "technical"
