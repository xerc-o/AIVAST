from ai.llm.groq import call_groq

class BaseAnalyzer:
    tool_name: str = ""

    def build_prompt(self, data: dict) -> str:
        raise NotImplementedError

    def analyze(self, data: dict) -> dict:
        prompt = self.build_prompt(data)
        return call_groq(prompt)