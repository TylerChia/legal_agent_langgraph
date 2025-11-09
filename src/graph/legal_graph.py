# src/graph/legal_graph.py
from langgraph.graph import StateGraph
from langgraph.nodes import LLMNode, ToolNode, FunctionNode
from langchain_openai import ChatOpenAI

from src.tools.simple_calendar_tool import SimpleGoogleCalendarTool
from src.tools.email_tool import send_summary_email
from src.graph.nodes.extract_text import extract_text_from_pdf
from src.graph.nodes.parse_contract import parse_contract
from src.graph.nodes.extract_deliverables import extract_deliverables
from src.graph.nodes.write_summary import write_summary

# Build LangGraph
def build_legal_graph():
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

    graph = StateGraph()

    # --- NODES ---
    graph.add_node("extract_text", FunctionNode(fn=extract_text_from_pdf))
    graph.add_node("parse_contract", LLMNode(llm=llm, prompt=parse_contract))
    graph.add_node("extract_deliverables", LLMNode(llm=llm, prompt=extract_deliverables))
    graph.add_node("write_summary", FunctionNode(fn=write_summary))
    graph.add_node("send_email", FunctionNode(fn=send_summary_email))

    calendar_tool = SimpleGoogleCalendarTool()
    graph.add_node("create_calendar_events", ToolNode(tool=calendar_tool))

    # --- EDGES ---
    graph.add_edge("extract_text", "parse_contract")
    graph.add_edge("parse_contract", "extract_deliverables")
    graph.add_edge("extract_deliverables", "write_summary")
    graph.add_edge("write_summary", "send_email")
    graph.add_edge("extract_deliverables", "create_calendar_events")

    # Entry and exit
    graph.set_entry_point("extract_text")
    graph.set_finish_point("send_email")

    return graph.compile()
