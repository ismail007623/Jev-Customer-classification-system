from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    billing_response_node,
    classify_ticket_node,
    save_response_node,
    technical_response_node,
)
from app.graph.router import route_ticket
from app.graph.state import SupportTicketState


def build_support_graph():
    graph = StateGraph(SupportTicketState)

    graph.add_node("classify_ticket", classify_ticket_node)
    graph.add_node("billing_agent", billing_response_node)
    graph.add_node("technical_agent", technical_response_node)
    graph.add_node("save_response", save_response_node)

    graph.add_edge(START, "classify_ticket")
    graph.add_conditional_edges(
        "classify_ticket",
        route_ticket,
        {
            "billing": "billing_agent",
            "technical": "technical_agent",
        },
    )
    graph.add_edge("billing_agent", "save_response")
    graph.add_edge("technical_agent", "save_response")
    graph.add_edge("save_response", END)

    return graph.compile()


support_graph = build_support_graph()
