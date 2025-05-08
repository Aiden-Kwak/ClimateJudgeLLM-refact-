import os
import json
import re
from .base_agent import BaseAgentService
from .prompt_builders.jury_cleaner_prompt_builder import JuryCleanerPromptBuilder

class JuryCleanService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = JuryCleanerPromptBuilder

    def _extract_json(self, text: str) -> dict:
        """응답에서 JSON을 추출하고 파싱합니다."""
        # 1. 먼저 직접 JSON 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. 중괄호로 둘러싸인 부분 추출 시도
        try:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                return json.loads(match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass

        # 3. 마크다운 코드 블록에서 추출 시도
        try:
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass

        raise json.JSONDecodeError("Could not extract valid JSON from response", text, 0)

    def _clean_single_question(self, question_data: dict, model_type: str) -> dict:
        """단일 question 데이터를 정제합니다."""
        prompt = self.builder.build_single_question_cleaner_prompt(question_data)
        cleaned_response = self._invoke(prompt, model_type)
        
        try:
            return self._extract_json(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            print(f"원본 응답:\n{cleaned_response}")
            return question_data  # 실패시 원본 반환

    def _clean(self, jury_results_path: str, model_type: str) -> dict:
        """jury_results.json 파일을 읽고 questions를 하나씩 정제합니다."""
        with open(jury_results_path, "r", encoding="utf-8") as f:
            document = json.load(f)
        
        # questions를 하나씩 정제
        cleaned_questions = []
        for i, question in enumerate(document["questions"], 1):
            print(f"[INFO] Question {i}/{len(document['questions'])} 정제 중...")
            try:
                cleaned_question = self._clean_single_question(question, model_type)
                cleaned_questions.append(cleaned_question)
            except Exception as e:
                print(f"[ERROR] Question {i} 정제 실패: {e}")
                cleaned_questions.append(question)  # 실패시 원본 유지
        
        # 정제된 questions로 업데이트
        document["questions"] = cleaned_questions
        
        return document