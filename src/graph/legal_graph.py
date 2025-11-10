"""
LangGraph workflow for contract analysis
Replaces CrewAI with a state-based graph approach
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os

# Define the state that flows through the graph
class ContractState(TypedDict):
    # Inputs
    contract_text: str
    user_email: str
    mode: str  # 'legal' or 'creator'
    
    # Intermediate state
    company_name: Optional[str]
    company_extraction_method: Optional[str]
    parsed_contract: Optional[dict]
    risk_analysis: Optional[dict]
    research_results: Optional[dict]
    deliverables: Optional[list]
    
    # Outputs
    summary_file: Optional[str]
    calendar_file: Optional[str]
    notification_results: Optional[list]
    error: Optional[str]

# Initialize the LLM
llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def create_legal_graph(mode: str = "legal"):
    """
    Create a LangGraph workflow for contract analysis
    
    Args:
        mode: 'legal' for basic analysis, 'creator' for brand deal analysis
    """
    from graph.nodes.extract_company import extract_company_node
    from graph.nodes.parse_contract import parse_contract_node
    from graph.nodes.analyze_risk import analyze_risks_node
    from graph.nodes.research_terms import research_terms_node
    from graph.nodes.extract_deliverables import extract_deliverables_node
    from graph.nodes.write_summary import write_summary_node
    from graph.nodes.send_notifications import send_notifications_node
    
    # Create the graph
    workflow = StateGraph(ContractState)
    
    # Add all nodes
    workflow.add_node("extract_company", extract_company_node)
    workflow.add_node("parse_contract", parse_contract_node)
    workflow.add_node("analyze_risks", analyze_risks_node)
    workflow.add_node("research_terms", research_terms_node)
    workflow.add_node("write_summary", write_summary_node)
    workflow.add_node("send_notifications", send_notifications_node)
    
    if mode == "creator":
        workflow.add_node("extract_deliverables", extract_deliverables_node)
    
    # Define the flow with research step included
    workflow.set_entry_point("extract_company")
    workflow.add_edge("extract_company", "parse_contract")
    workflow.add_edge("parse_contract", "analyze_risks")
    workflow.add_edge("analyze_risks", "research_terms")  # Research unclear terms
    
    if mode == "creator":
        workflow.add_edge("research_terms", "extract_deliverables")
        workflow.add_edge("extract_deliverables", "write_summary")
    else:
        workflow.add_edge("research_terms", "write_summary")  # Skip deliverables in legal mode
    
    workflow.add_edge("write_summary", "send_notifications")
    workflow.add_edge("send_notifications", END)
    
    return workflow.compile()

def run_legal_analysis(contract_text: str, user_email: str, mode: str = "legal") -> dict:
    """
    Run the complete legal analysis workflow
    
    Args:
        contract_text: The contract text to analyze
        user_email: User's email for notifications
        mode: 'legal' or 'creator'
        
    Returns:
        Final state with results or errors
    """
    graph = create_legal_graph(mode)
    
    initial_state = {
        "contract_text": contract_text,
        "user_email": user_email,
        "mode": mode,
        "company_name": None,
        "company_extraction_method": None,
        "parsed_contract": None,
        "risk_analysis": None,
        "research_results": None,
        "deliverables": None,
        "summary_file": None,
        "calendar_file": None,
        "notification_results": None,
        "error": None
    }
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    return final_state