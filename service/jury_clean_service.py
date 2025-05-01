import os
import json
from .base_agent import BaseAgentService
from .prompt_builders.jury_cleaner_prompt_builder import JuryCleanerPromptBuilder

class JuryCleanService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = JuryCleanerPromptBuilder

    def _clean(self, jury_results_path: str, model_type: str) -> str:
        with open(jury_results_path, "r", encoding="utf-8") as f:
            document = json.load(f)
        prompt = self.builder.build_jury_cleaner_prompt(document)
        return self._invoke(prompt, model_type)