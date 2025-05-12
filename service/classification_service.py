import json
from .base_agent import BaseAgentService
from .prompt_builders.classification_prompt_builder import ClassificationPromptBuilder

class ClassificationService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = ClassificationPromptBuilder

    def classify(self, judge_input_path: str, model_type: str = "deepseek-chat") -> str:
        with open(judge_input_path, "r", encoding="utf-8") as f:
            judge_input = json.load(f)
        
        prompt = self.builder.build_classification_prompt(judge_input)
        return self._invoke(prompt, model_type) 