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
        """
        판사의 의견을 생성합니다. 이제 classification_service에 의존하지 않습니다.
        
        Args:
            judge_input_path (str): 판사 입력 JSON 파일 경로
            model_type (str): 사용할 LLM 모델 타입
            
        Returns:
            str: 판사의 판결 결과
        """
        with open(judge_input_path, "r", encoding="utf-8") as f:
            judge_input = json.load(f)
        
        # 빈 classification_results로 프롬프트 생성
        # 이 함수는 입력 인자가 필요하지만 실제로는 사용하지 않음
        classification_results = "{}"
        
        # 분류 결과를 포함하여 판사 프롬프트 생성
        prompt = self.builder.build_decision_prompt(judge_input, classification_results)
        return self._invoke(prompt, model_type)
