from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..models.state import CurationState
from .nodes import (
    search_literature,
    fetch_abstracts,
    extract_evidence,
    calculate_scores,
    classify_relationship
)

def build_curation_graph():
    """Build the complete curation graph"""
    workflow = StateGraph(CurationState)
    
    workflow.add_node("search", search_literature)
    workflow.add_node("fetch", fetch_abstracts)
    workflow.add_node("extract", extract_evidence)
    workflow.add_node("score", calculate_scores)
    workflow.add_node("classify", classify_relationship)
    
    workflow.add_edge("search", "fetch")
    workflow.add_edge("fetch", "extract")
    workflow.add_edge("extract", "score")
    workflow.add_edge("score", "classify")
    workflow.add_edge("classify", END)
    
    # entry point
    workflow.set_entry_point("search")
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)