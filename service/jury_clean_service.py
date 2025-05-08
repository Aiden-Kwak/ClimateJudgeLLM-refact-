import os
import json
import re
import time
from typing import Optional
from openai import APITimeoutError
from .base_agent import BaseAgentService
from .prompt_builders.jury_cleaner_prompt_builder import JuryCleanerPromptBuilder

class JuryCleanService(BaseAgentService):
    def __init__(self, llm):
        super().__init__(llm)
        self.builder = JuryCleanerPromptBuilder
        self.max_retries = 3
        self.retry_delay = 2  # 초기 재시도 대기 시간 (초)

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

    def _clean_single_question_with_retry(self, question_data: dict, model_type: str) -> Optional[dict]:
        """단일 question 데이터를 정제하며, 실패 시 재시도합니다."""
        for attempt in range(self.max_retries):
            try:
                prompt = self.builder.build_single_question_cleaner_prompt(question_data)
                cleaned_response = self._invoke(prompt, model_type)
                return self._extract_json(cleaned_response)
            except (json.JSONDecodeError, APITimeoutError) as e:
                if attempt == self.max_retries - 1:  # 마지막 시도
                    print(f"[ERROR] 최대 재시도 횟수 초과: {str(e)}")
                    return None
                wait_time = self.retry_delay * (2 ** attempt)  # 지수 백오프
                print(f"[INFO] {attempt + 1}번째 시도 실패. {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"[ERROR] 예상치 못한 오류 발생: {str(e)}")
                return None
        return None

    def _clean(self, jury_results_path: str, model_type: str) -> dict:
        """jury_results.json 파일을 읽고 questions를 하나씩 정제합니다."""
        with open(jury_results_path, "r", encoding="utf-8") as f:
            document = json.load(f)
        
        # questions를 하나씩 정제
        cleaned_questions = []
        total_questions = len(document["questions"])
        
        for i, question in enumerate(document["questions"], 1):
            print(f"[INFO] Question {i}/{total_questions} 정제 중...")
            
            cleaned_question = self._clean_single_question_with_retry(question, model_type)
            if cleaned_question:
                cleaned_questions.append(cleaned_question)
            else:
                print(f"[WARN] Question {i} 정제 실패. 원본 유지.")
                cleaned_questions.append(question)
            
            # 진행 상황 표시
            print(f"[INFO] 진행률: {i}/{total_questions} ({(i/total_questions)*100:.1f}%)")
        
        # 정제된 questions로 업데이트
        document["questions"] = cleaned_questions
        
        return document