from ..llm.groq import call_groq
from .parser import safe_parse_json


class BaseAnalyzer:
    tool_name: str = ""

    def build_prompt(self, data: dict) -> str:
        raise NotImplementedError

    def analyze(self, data: dict) -> dict:
        """
        Analyze execution data menggunakan LLM.
        
        Returns:
            dict: Parsed JSON dari LLM response, atau dict dengan error jika parsing gagal
        """
        prompt = self.build_prompt(data)
        
        try:
            # Call LLM
            raw_response = call_groq(prompt)
            
            # Parse JSON response
            if isinstance(raw_response, str):
                parsed = safe_parse_json(raw_response)
                return parsed
            elif isinstance(raw_response, dict):
                return raw_response
            else:
                return {
                    "risk": "unknown",
                    "error": "Unexpected response type from LLM",
                    "raw": str(raw_response)
                }
        except Exception as e:
            return {
                "risk": "unknown",
                "error": f"LLM call failed: {str(e)}"
            }