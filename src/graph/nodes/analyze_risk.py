"""
Risk analysis node - evaluates legal and business risks
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import re

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def analyze_risks_node(state: dict) -> dict:
    """
    Analyze the parsed contract for risks
    """
    parsed_contract = state.get("parsed_contract")
    mode = state["mode"]
    
    if not parsed_contract:
        return {**state, "risk_analysis": {"error": "No parsed contract available"}}
    
    if mode == "creator":
        system_prompt = """You are a contract risk analyst specializing in influencer/brand deals.

Analyze the contract for these specific risks:
- **Content Ownership**: Does the brand get perpetual or exclusive rights?
- **Exclusivity**: Does it prevent working with competing brands?
- **Usage Rights**: Can the brand use content indefinitely or resell it?
- **Payment Terms**: Are payments delayed, conditional, or unclear?
- **Approval Process**: Are revision/reshoot terms unreasonable?
- **Termination**: Are penalties unfair to the creator?
- **Creator Rights**: Can the creator repost their own content?

Rate each risk as Low, Medium, or High and explain why.

CRITICAL: Return ONLY valid JSON. Do not include any text before or after the JSON.
Use double quotes for all strings, no trailing commas, proper escaping.

Format:
{
  "risks": [
    {
      "category": "Content Ownership",
      "level": "High",
      "reason": "Brand gets perpetual rights",
      "recommendation": "Negotiate time-limited rights"
    }
  ],
  "overall_risk_score": "Medium"
}"""
    else:
        system_prompt = """You are a legal risk analyst.

Analyze the contract for:
- Unfair liability or indemnification clauses
- Ambiguous terms that could lead to disputes
- Unusual or concerning provisions
- Imbalanced obligations between parties

CRITICAL: Return ONLY valid JSON with no additional text.

Format:
{
  "risks": [
    {
      "category": "string",
      "level": "Low|Medium|High",
      "reason": "string"
    }
  ],
  "overall_risk_score": "Low|Medium|High"
}"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Parsed contract data:\n\n{json.dumps(parsed_contract, indent=2)}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # Try multiple JSON extraction methods
        risk_data = extract_json_safely(content)
        
        if risk_data:
            print(f"Risks Analyzed! \n{risk_data}")
            return {
                **state,
                "risk_analysis": risk_data
            }
        else:
            # Fallback: create basic risk structure from text
            print("Could not parse JSON, creating basic risk analysis")
            return {
                **state,
                "risk_analysis": {
                    "risks": [{
                        "category": "General Analysis",
                        "level": "Medium",
                        "reason": "Analysis completed but JSON parsing failed. See summary for details.",
                        "raw_analysis": content[:500]  # Include first 500 chars
                    }],
                    "overall_risk_score": "Medium",
                    "parsing_note": "Risk analysis text available but not fully structured"
                }
            }
            
    except Exception as e:
        print(f"Error analyzing risks: {e}")
        return {
            **state,
            "risk_analysis": {
                "error": f"Risk analysis failed: {str(e)}",
                "risks": [],
                "overall_risk_score": "Unknown"
            }
        }

def extract_json_safely(content: str) -> dict:
    """
    Try multiple methods to extract valid JSON from LLM response
    """
    # Method 1: Direct JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Method 2: Extract from markdown code blocks
    json_patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"<json>(.*?)</json>",
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    
    # Method 3: Find JSON object in text
    # Look for content between first { and last }
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
            
            # Try to fix common JSON issues
            json_str = fix_common_json_errors(json_str)
            
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    return None

def fix_common_json_errors(json_str: str) -> str:
    """
    Attempt to fix common JSON formatting issues
    """
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Replace single quotes with double quotes (but be careful with apostrophes)
    # This is risky, so we skip it for now
    
    # Remove any text after the last closing brace
    last_brace = json_str.rfind('}')
    if last_brace != -1:
        json_str = json_str[:last_brace + 1]
    
    return json_str