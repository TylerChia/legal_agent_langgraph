"""
Contract parsing node - extracts key clauses and information
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import re

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def parse_contract_node(state: dict) -> dict:
    """
    Parse the contract and extract key information
    """
    contract_text = state["contract_text"]
    mode = state["mode"]
    
    if mode == "creator":
        system_prompt = """You are an expert contract parser specializing in influencer/brand deal contracts.
        
Extract and structure the following information from the contract:
- Deliverables (what content must be created, formats, platforms, quantities)
- Due dates and timelines (convert to PST/Pacific time)
- Payment terms (amounts, schedule, invoicing)
- Ownership & Licensing terms
- Exclusivity or non-compete clauses
- Usage rights (perpetual, limited, etc.)
- Approval processes
- Termination conditions
- Any legal red flags

CRITICAL: Return ONLY valid JSON. No markdown, no explanations, no text before or after.
Use double quotes for strings. No trailing commas. Properly escape quotes in text.

Format:
{
  "deliverables": [],
  "dates": [],
  "payment_terms": {},
  "legal_flags": [],
  "company_name": "",
  "clauses": []
}

Do NOT fabricate information. If something is not in the contract, omit it or use null."""
    else:
        system_prompt = """You are an expert legal contract parser.
        
Extract and categorize all key clauses from this contract:
- Parties involved
- Key obligations
- Payment terms
- Termination conditions
- Liability and indemnification
- Intellectual property rights
- Confidentiality
- Legal risks or unusual clauses

CRITICAL: Return ONLY valid JSON with no additional text.

Format:
{
  "parties": [],
  "obligations": [],
  "payment_terms": {},
  "clauses": []
}"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Contract text:\n\n{contract_text}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # Use robust JSON extraction
        parsed_data = extract_json_safely(content)
        
        if parsed_data:
            print(f"Contract Parsed! \n{parsed_data}")
            return {
                **state,
                "parsed_contract": parsed_data
            }
        else:
            # Fallback: create basic structure
            print("Could not parse contract JSON, creating basic structure")
            return {
                **state,
                "parsed_contract": {
                    "error": "JSON parsing failed",
                    "raw_content": content[:1000],  # First 1000 chars
                    "deliverables": [],
                    "clauses": []
                }
            }
            
    except Exception as e:
        print(f"Error parsing contract: {e}")
        return {
            **state,
            "error": f"Contract parsing failed: {str(e)}",
            "parsed_contract": {"error": str(e)}
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
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
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
    
    # Remove any text after the last closing brace
    last_brace = json_str.rfind('}')
    if last_brace != -1:
        json_str = json_str[:last_brace + 1]
    
    return json_str