import json
import re

def safe_parse_json(text: str) -> dict:
    """
    Tries to parse JSON from text, even if it's wrapped in markdown or contains junk.
    """
    if not text:
        return {"error": "empty_response", "risk": "unknown"}
        
    # Clean up common markdown junk
    cleaned = text.strip()
    
    # 1. Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # 2. Try to find content within ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            cleaned = match.group(1) # Try further cleaning on the content
            
    # 3. Last ditch: Find the first '{' and the last '}'
    try:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            json_str = cleaned[start:end+1]
            return json.loads(json_str)
    except Exception:
        pass

    return {
        "risk": "unknown",
        "error": "LLM returned invalid JSON format",
        "raw": text
    }
