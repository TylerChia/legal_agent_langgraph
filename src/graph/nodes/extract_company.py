"""
Company name extraction node - extracts primary company/brand name
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def extract_company_node(state: dict) -> dict:
    """
    Extract the primary company/brand name from the contract
    Falls back to regex extraction if LLM fails
    """
    contract_text = state["contract_text"]
    
    system_prompt = """You are an expert at identifying company and brand names in legal contracts.

Extract the PRIMARY company or brand name from this contract. This is typically:
- The company hiring the creator/contractor
- The brand mentioned in a sponsorship deal
- The party offering the agreement (not the individual/creator)

Return ONLY valid JSON with this structure:
{
    "company_name": "The Company Name",
    "confidence": "high|medium|low",
    "context": "Brief explanation of where/how you found it"
}

If you cannot find a company name, return:
{
    "company_name": null,
    "confidence": "none",
    "context": "No clear company name found"
}

Do NOT return the creator's name, individual names, or generic terms like "The Influencer"."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Contract text (first 3000 chars):\n\n{contract_text[:3000]}")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        company_name = result.get("company_name")
        confidence = result.get("confidence", "unknown")
        
        print(f"🏢 LLM extracted company: {company_name} (confidence: {confidence})")
        
        # If LLM failed or low confidence, try regex fallback
        if not company_name or confidence == "low" or confidence == "none":
            company_name = regex_extract_company(contract_text)
            if company_name:
                print(f"🏢 Regex fallback found: {company_name}")
        
        return {
            **state,
            "company_name": company_name or "Unknown Company",
            "company_extraction_method": "llm" if result.get("company_name") else "regex"
        }
        
    except Exception as e:
        print(f"Error extracting company name with LLM: {e}")
        # Fallback to regex
        company_name = regex_extract_company(contract_text)
        return {
            **state,
            "company_name": company_name or "Unknown Company",
            "company_extraction_method": "regex_fallback"
        }

def regex_extract_company(contract_text: str) -> str:
    """
    Fallback regex-based company name extraction
    Uses multiple patterns to find company names
    """
    # Pattern 1: "between X and Y" structures
    between_patterns = [
        r"between\s+(.*?)\s+(?:and|&)",
        r"by and between\s+(.*?)\s+(?:and|&)",
        r"entered into by\s+(.*?)\s+(?:and|&)",
        r"Agreement is made between\s+(.*?)\s+(?:and|&)",
        r"This Agreement is made by\s+(.*?)\s+(?:and|&)",
        r"contract between\s+(.*?)\s+(?:and|&)",
    ]
    
    for pattern in between_patterns:
        match = re.search(pattern, contract_text, flags=re.IGNORECASE)
        if match:
            possible_name = match.group(1).strip()
            # Clean up common artifacts
            possible_name = re.sub(r'^["\']+|["\']+$', '', possible_name)  # Remove quotes
            possible_name = re.sub(r'\s+', ' ', possible_name)  # Normalize whitespace
            
            # Skip if it looks like an individual or generic term
            skip_terms = [
                "the influencer", "the creator", "the contractor", 
                "the individual", "the party", "the client",
                "you", "your", "creator", "influencer"
            ]
            if any(term in possible_name.lower() for term in skip_terms):
                continue
            
            # Skip if too long (likely includes extra text)
            if len(possible_name.split()) <= 6:
                return possible_name
    
    # Pattern 2: Look for formal company suffixes
    company_patterns = [
        r"\b([A-Z][A-Za-z0-9&\s]+(?:Inc\.|LLC|Ltd\.|Corporation|Corp\.|Company|Co\.))\b",
        r"\b([A-Z][A-Z\s&]+(?:Inc\.|LLC|Ltd\.|Corporation|Corp\.|Company|Co\.))\b",  # All caps
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, contract_text[:2000])  # Search first 2000 chars
        if matches:
            # Return the first non-generic match
            for match in matches:
                match = match.strip()
                if len(match.split()) <= 5:  # Reasonable company name length
                    return match
    
    # Pattern 3: Look for quoted company names
    quoted_pattern = r'"([A-Z][A-Za-z0-9\s&,\.]+)"'
    quoted_matches = re.findall(quoted_pattern, contract_text[:1500])
    for match in quoted_matches:
        if len(match.split()) <= 5 and not any(word.lower() in ["agreement", "contract", "terms"] for word in match.split()):
            return match
    
    # Pattern 4: Capitalized multi-word names (be more selective)
    cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    cap_matches = re.findall(cap_pattern, contract_text[:1500])
    
    # Filter for likely company names
    for match in cap_matches:
        words = match.split()
        # Must be 2-4 words, all capitalized properly
        if 2 <= len(words) <= 4:
            # Skip common contract language
            skip_words = ["This Agreement", "The Party", "The Creator", "The Influencer"]
            if match not in skip_words:
                return match
    
    return ""  # No company name found