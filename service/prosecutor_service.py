import json
import os
from .base_agent import BaseAgentService
from .prompt_builders.prosecutor_prompt_builder import ProsecutorPromptBuilder

class ProsecutorService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = ProsecutorPromptBuilder

    def analyze(self, jury_results_path: str, claim: str, model_type: str) -> str:
        with open(jury_results_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        prompt = self.builder.build_analysis_prompt(doc, claim)
        return self._invoke(prompt, model_type)

    def reply_brief(self, lawyer_reply_path: str, claim: str, model_type: str) -> str:
        if os.path.exists(lawyer_reply_path):
            with open(lawyer_reply_path, encoding="utf-8") as f:
                defense_brief = f.read().strip()
        else:
            defense_brief = ""

        prompt = self.builder.build_reply_brief_prompt(defense_brief, claim)
        return self._invoke(prompt, model_type)