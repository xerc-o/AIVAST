from ..llm.groq import call_groq
from .parser import safe_parse_json
import logging # Import logging module

logger = logging.getLogger(__name__) # Get a logger instance
logger.setLevel(logging.DEBUG) # Explicitly set logger level to DEBUG

class BaseAnalyzer:
    tool_name: str = ""

    def build_prompt(self, data: dict) -> str:
        raise NotImplementedError

    def truncate_text(self, text: str, max_chars: int = 40000) -> str:
        """Truncates text to prevent LLM context overflow."""
        if not text: return ""
        if len(text) <= max_chars: return text
        return text[:max_chars] + "\n\n[... OUTPUT TRUNCATED DUE TO LENGTH ...]"

    def _ensure_schema(self, data: dict, target: str = "Unknown") -> dict:
        """Ensures the analysis dict matches the expected frontend schema."""
        schema = {
            "metadata": {"target": target, "confidence": "Medium"},
            "analysis": "No analysis details provided.",
            "issue": {"type": "None identified", "severity": "info", "endpoint": "N/A", "parameter": "N/A", "owasp": "N/A"},
            "evidence": {"payload": "N/A", "response_behavior": "N/A"},
            "impact": "No significant impact identified.",
            "recommendations": [],
            "next_actions": [],
            "summary": "Analysis completed with no critical findings."
        }
        
        # Merge AI data into schema
        if not isinstance(data, dict): return schema
        
        for key, value in schema.items():
            if key not in data:
                data[key] = value
            elif isinstance(value, dict) and isinstance(data[key], dict):
                # Shallow merge for nested dicts (metadata, issue, evidence)
                for subkey, subval in value.items():
                    if subkey not in data[key]:
                        data[key][subkey] = subval
                        
        return data

    def analyze(self, data: dict) -> dict:
        """
        Analyze execution data menggunakan LLM.
        """
        prompt = self.build_prompt(data)
        target = data.get("target", "Unknown")
        
        try:
            raw_response = call_groq(prompt)
            
            if isinstance(raw_response, str):
                parsed = safe_parse_json(raw_response)
                # Ensure we have the full schema
                return self._ensure_schema(parsed, target=target)
            else:
                return self._ensure_schema({"error": "Unexpected LLM response type"}, target=target)
                
        except Exception as e:
            logger.error(f"LLM call or parsing failed: {str(e)}", exc_info=True)
            return self._ensure_schema({"error": f"LLM failure: {str(e)}"}, target=target)