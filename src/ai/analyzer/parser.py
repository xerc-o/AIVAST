import json

def safe_parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "risk": "unknown",
            "error": "LLM returned invalid JSON",
            "raw": text
        }
