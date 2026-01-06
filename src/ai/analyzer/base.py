from ..llm.groq import call_groq
from .parser import safe_parse_json
import logging # Import logging module

logger = logging.getLogger(__name__) # Get a logger instance
logger.setLevel(logging.DEBUG) # Explicitly set logger level to DEBUG

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
        logger.debug(f"LLM Prompt: {prompt}") # Log the prompt
        
        try:
            # Call LLM
            raw_response = call_groq(prompt)
            logger.debug(f"LLM Raw Response: {raw_response[:500]}") # Log raw response
            
            # Parse JSON response
            if isinstance(raw_response, str):
                parsed = safe_parse_json(raw_response)
                logger.debug(f"LLM Parsed Response: {parsed}") # Log parsed response
                return parsed
            elif isinstance(raw_response, dict):
                logger.debug(f"LLM Parsed Response (dict): {raw_response}")
                return raw_response
            else:
                return {
                    "risk": "unknown",
                    "error": "Unexpected response type from LLM",
                    "raw": str(raw_response)
                }
        except Exception as e:
            logger.error(f"LLM call or parsing failed: {str(e)}", exc_info=True) # Log errors
            return {
                "risk": "unknown",
                "error": f"LLM call failed: {str(e)}"
            }