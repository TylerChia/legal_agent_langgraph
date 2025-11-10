"""
Web research node - searches for unclear contract terms
Uses LLM to identify which terms need clarification
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
import os
import json
import re

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def research_terms_node(state: dict) -> dict:
    """
    Research unclear or concerning contract terms using web search
    LLM identifies which terms need clarification, then searches for them
    """
    parsed_contract = state.get("parsed_contract")
    risk_analysis = state.get("risk_analysis")
    
    # Use LLM to identify unclear terms that need research
    unclear_terms = identify_unclear_terms_with_llm(parsed_contract, risk_analysis)
    
    if not unclear_terms or len(unclear_terms) == 0:
        print("📚 No unclear terms identified - skipping research")
        return {
            **state,
            "research_results": {"searched": False, "message": "No unclear terms found"}
        }
    
    print(f"📚 LLM identified {len(unclear_terms)} terms to research: {unclear_terms}")
    
    # Step 2: Perform web searches for identified terms
    search = DuckDuckGoSearchRun()
    research_results = {}
    
    for term in unclear_terms[:3]:  # Limit to 3 searches to avoid rate limits
        try:
            # Search with influencer/creator context
            query = f"{term} contract legal meaning"
            print(f"🔍 Searching: {query}")
            
            search_result = search.run(query)
            
            # Step 3: Use LLM to summarize the search results
            summary = summarize_search_results(term, search_result)
            research_results[term] = summary
            
        except Exception as e:
            print(f"Search failed for '{term}': {str(e)}")
            research_results[term] = f"Could not research this term: {str(e)}"
    
    return {
        **state,
        "research_results": {
            "searched": True,
            "terms": research_results
        }
    }

def identify_unclear_terms_with_llm(parsed_contract: dict, risk_analysis: dict) -> list:
    """
    Use LLM to identify legal or technical terms that might need clarification
    Returns a list of terms to research
    """
    system_prompt = """You are a legal contract analyzer helping non-lawyers understand their contracts.

Review the parsed contract and risk analysis to identify legal or technical terms that:
1. Are complex or use legal jargon
2. Could have significant impact on the client's rights or obligations
3. Might not be well understood by someone without legal training
4. Are flagged as risks or concerns in the analysis

Return ONLY a JSON array of 3-5 specific terms found in THIS contract that need explanation.
Each term should be a short phrase (1-4 words).
If no unclear terms are found, return an empty array.

Format:
["term 1", "term 2", "term 3"]"""
    
    context = {
        "parsed_contract": parsed_contract,
        "risk_analysis": risk_analysis
    }
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Contract data:\n\n{json.dumps(context, indent=2)}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Use robust JSON extraction
        terms = extract_json_safely(content)
        
        # Ensure it's a list
        if not isinstance(terms, list):
            terms = []
        
        # Clean and validate terms
        terms = [str(term).strip() for term in terms if term]
        terms = [term for term in terms if len(term) > 2 and len(term.split()) <= 6]
        
        return terms[:5]  # Max 5 terms
        
    except Exception as e:
        print(f"Error identifying unclear terms: {e}")
        return []

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

def summarize_search_results(term: str, search_results: str) -> str:
    """
    Use LLM to summarize web search results into a concise, friendly explanation
    """
    system_prompt = """You are a legal research assistant.

Summarize the search results into a clear, concise explanation (2-4 sentences) that:
1. Defines the term in the given context
2. Explains why it matters (how it affects their rights, money, or content)
3. Mentions any red flags or common concerns

Be direct and practical. Use friendly language, not legal jargon.
Focus on actionable information that helps clients understand their contract.

If the search results don't provide clear information, say so and provide a basic definition based on your knowledge."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Term to explain: {term}\n\nSearch results:\n{search_results[:2000]}")
    ]
    
    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        return f"Could not generate explanation: {str(e)}"