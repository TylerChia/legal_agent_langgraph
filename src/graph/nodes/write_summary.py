"""
Summary writing node - creates user-friendly contract summary
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def write_summary_node(state: dict) -> dict:
    """
    Write a user-friendly summary of the contract
    Includes web research results if available
    """
    parsed_contract = state.get("parsed_contract")
    risk_analysis = state.get("risk_analysis")
    research_results = state.get("research_results")
    mode = state["mode"]
    
    if not parsed_contract:
        return {**state, "error": "No parsed contract to summarize"}
    
    # Check if research was performed
    has_research = (research_results and 
                   research_results.get("searched") and 
                   research_results.get("terms"))
    
    if mode == "creator":
        if has_research:
            system_prompt = """You are writing a contract summary for a content creator.

Create a concise, friendly summary in markdown format with these sections:

## Brand Deal Summary
Brief overview of the partnership

## Deliverables & Deadlines
List what must be created and when (be specific about dates and times)

## Payment Terms
How and when the creator gets paid

## Legal & Risk Concerns
Key risks like:
- Content ownership (who owns what)
- Exclusivity restrictions
- Usage rights (can brand use content forever?)
- Any red flags

## Key Terms Explained
Web research has provided explanations for unclear legal terms.
Include a section explaining these terms in creator-friendly language.
Use the research results to help creators understand what these terms mean for them.

Keep it succinct - creators want actionable info, not legal jargon.

End with:
### Disclaimer
This summary is for informational purposes only and not legal advice.

Return ONLY the markdown content, no preamble."""
        else:
            system_prompt = """You are writing a contract summary for a content creator.

Create a concise, friendly summary in markdown format with these sections:

## Brand Deal Summary
Brief overview of the partnership

## Deliverables & Deadlines
List what must be created and when (be specific about dates and times)

## Payment Terms
How and when the creator gets paid

## Legal & Risk Concerns
Key risks like:
- Content ownership (who owns what)
- Exclusivity restrictions
- Usage rights (can brand use content forever?)
- Any red flags

Keep it succinct - creators want actionable info, not legal jargon.

End with:
### Disclaimer
This summary is for informational purposes only and not legal advice.

Return ONLY the markdown content, no preamble."""
    else:
        system_prompt = """You are writing a contract summary.

Create a structured markdown summary with:
- Key parties and purpose
- Main obligations
- Payment terms
- Termination conditions
- Notable legal provisions
- Risk assessment

If research results are provided, include relevant legal term explanations.

Return ONLY the markdown content."""
    
    # Build context with all available data
    context = {
        "parsed_contract": parsed_contract,
        "risk_analysis": risk_analysis
    }
    
    # Add research results to context if available
    if has_research:
        context["research_results"] = research_results
        print(f"📚 Including research for {len(research_results['terms'])} terms in summary")
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Contract data:\n\n{json.dumps(context, indent=2)}")
    ]
    
    try:
        response = llm.invoke(messages)
        summary = response.content
        
        # Remove any markdown code blocks if present
        if "```markdown" in summary:
            summary = summary.split("```markdown")[1].split("```")[0].strip()
        elif summary.startswith("```") and summary.endswith("```"):
            summary = summary.strip("`").strip()
        
        # Write to file
        with open("contract_summary.md", "w", encoding="utf-8") as f:
            f.write(summary)
        
        print("✅ Contract summary written successfully")
        
        return {
            **state,
            "summary_file": "contract_summary.md"
        }
    except Exception as e:
        print(f"Error writing summary: {e}")
        return {
            **state,
            "error": f"Summary writing failed: {str(e)}"
        }