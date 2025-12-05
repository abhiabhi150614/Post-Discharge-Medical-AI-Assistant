from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END, START
from .receptionist import receptionist_node
from .clinical import clinical_node

class AgentState(TypedDict):
    session_id: str
    messages: List[dict]
    patient_data: Optional[dict]
    current_agent: str
    handoff_to_clinical: bool
    user_name: Optional[str]

def router(state: AgentState):
    handoff = state.get("handoff_to_clinical")
    print(f"DEBUG: Router called. Handoff state: {handoff}")
    if handoff:
        return "clinical"
    return "receptionist"

workflow = StateGraph(AgentState)

workflow.add_node("receptionist", receptionist_node)
workflow.add_node("clinical", clinical_node)

# Conditional entry point based on state
workflow.add_conditional_edges(
    START,
    router,
    {
        "receptionist": "receptionist",
        "clinical": "clinical"
    }
)

workflow.add_conditional_edges(
    "receptionist",
    router,
    {
        "receptionist": END,
        "clinical": "clinical"
    }
)

workflow.add_edge("clinical", END)

graph = workflow.compile()
