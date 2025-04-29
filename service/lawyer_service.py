import os
import json
from .base_agent import BaseAgentService
from .prompt_builders.lawyer_prompt_builder import LawyerPromptBuilder

class LawyerService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = LawyerPromptBuilder

    def analyze(self, jury_results_path: str, claim: str, model_type: str) -> str:
        with open(jury_results_path, "r", encoding="utf-8") as f:
            document = json.load(f)
        prompt = self.builder.build_analysis_prompt(document, claim)
        return self._invoke(prompt, model_type)

    def reply_brief(self, prosecutor_reply_path: str, claim: str, model_type: str) -> str:
        if os.path.exists(prosecutor_reply_path):
            with open(prosecutor_reply_path, "r", encoding="utf-8") as f:
                prosecutor_brief = f.read().strip()
        else:
            prosecutor_brief = ""
        prompt = self.builder.build_reply_brief_prompt(prosecutor_brief, claim)
        return self._invoke(prompt, model_type)