"""
Deliverables extraction node - formats deliverables for calendar
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import re

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def extract_deliverables_node(state: dict) -> dict:
    """
    Extract deliverables with dates for calendar integration
    """
    parsed_contract = state.get("parsed_contract")
    user_email = state["user_email"]
    
    if not parsed_contract:
        return {**state, "deliverables": []}
    
    system_prompt = """You are extracting deliverables for calendar scheduling.

For each deliverable with a due date, provide:
- summary: Brief title (e.g., "Instagram Reel Due")
- description: What needs to be delivered
- start_date: Date in YYYY-MM-DD format
- start_time: Time in HH:MM 24-hour format if specified, otherwise null
- timezone: Timezone if specified (PST, EST, etc.), otherwise null
- user_email: The provided email

Look for time indicators like:
- "by 5:00 PM PST"
- "due at 14:00 EST"
- "before 3:00 PM Pacific"

If no specific time is mentioned, set start_time to null for all-day events.
Only include deliverables with explicit due dates.

CRITICAL: Return ONLY valid JSON array. No markdown, no explanations.
Use double quotes for all strings. No trailing commas.

Format:
[
  {
    "summary": "Instagram Reel Due",
    "description": "Create 30-second reel",
    "start_date": "2025-12-01",
    "start_time": "17:00",
    "timezone": "PST",
    "user_email": "user@example.com"
  }
]"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User email: {user_email}\n\nParsed contract:\n{json.dumps(parsed_contract, indent=2)}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # Use robust JSON extraction
        deliverables = extract_json_safely(content)
        
        # Ensure it's a list
        if isinstance(deliverables, dict):
            deliverables = deliverables.get("deliverables", [])
        
        if not isinstance(deliverables, list):
            deliverables = []
        
        # Save to file for calendar integration
        if deliverables:
            print(f"Deliverables Extracted! \n {deliverables}")
            with open("calendar_deliverables.json", "w") as f:
                json.dump(deliverables, f, indent=2)
        
        return {
            **state,
            "deliverables": deliverables,
            "calendar_file": "calendar_deliverables.json" if deliverables else None
        }
        
    except Exception as e:
        print(f"Error extracting deliverables: {e}")
        return {
            **state,
            "deliverables": [],
            "calendar_file": None
        }

def extract_json_safely(content: str):
    """
    Try multiple methods to extract valid JSON from LLM response
    Returns dict, list, or None
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
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    
    # Method 3: Find JSON array in text (look for [ ... ])
    try:
        # Try to find array first
        array_start = content.find('[')
        array_end = content.rfind(']') + 1
        if array_start != -1 and array_end > array_start:
            json_str = content[array_start:array_end]
            json_str = fix_common_json_errors(json_str)
            return json.loads(json_str)
        
        # Fall back to object { ... }
        obj_start = content.find('{')
        obj_end = content.rfind('}') + 1
        if obj_start != -1 and obj_end > obj_start:
            json_str = content[obj_start:obj_end]
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
    
    return json_str