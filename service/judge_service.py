import os
import json
from .base_agent import BaseAgentService
from .prompt_builders.judge_prompt_builder import JudgePromptBuilder

class JudgeService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = JudgePromptBuilder

    def prepare_input(
        self,
        jury_path: str,
        lawyer_results_path: str,
        prosecutor_results_path: str,
        lawyer_reply_path: str,
        prosecutor_reply_path: str
    ) -> dict:
        # Load jury results
        with open(jury_path, "r", encoding="utf-8") as f:
            jury = json.load(f)
        # Load lawyer analysis
        with open(lawyer_results_path, "r", encoding="utf-8") as f:
            lawyer = f.read().strip()
        # Load prosecutor analysis
        with open(prosecutor_results_path, "r", encoding="utf-8") as f:
            prosecutor = f.read().strip()
        # Load lawyer reply brief
        lawyer_reply = ""
        if os.path.exists(lawyer_reply_path):
            with open(lawyer_reply_path, "r", encoding="utf-8") as f:
                lawyer_reply = f.read().strip()
        # Load prosecutor reply brief
        prosecutor_reply = ""
        if os.path.exists(prosecutor_reply_path):
            with open(prosecutor_reply_path, "r", encoding="utf-8") as f:
                prosecutor_reply = f.read().strip()

        return {
            "jury_results": jury,
            "lawyer_results": lawyer,
            "lawyer_reply_brief": lawyer_reply,
            "prosecutor_results": prosecutor,
            "prosecutor_reply_brief": prosecutor_reply
        }

    def decide(self, judge_input_path: str, model_type: str = "deepseek-chat") -> str:
        with open(judge_input_path, "r", encoding="utf-8") as f:
            judge_input = json.load(f)
        prompt = self.builder.build_decision_prompt(judge_input)
        return self._invoke(prompt, model_type)
