import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from model.data_models import QuestionResult, JuryDocument
from typing import Any

class JuryService:
    def __init__(self, rag_service):
        self.rag = rag_service

    def _prompt(self, question: str, original_claim: str) -> str:
        return f"""
        You are a juror tasked with preparing a logical and well-reasoned response... "{question}" ... "{original_claim}"
        """

    def evaluate(self, questions: list[str], resource: Any, original_claim: str) -> dict:
        results: list[QuestionResult] = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.rag.query, resource, q, 5): q for q in questions}
            for future in as_completed(futures):
                q = futures[future]
                response, evidence = future.result()
                results.append(QuestionResult(q, response, evidence))
        doc = JuryDocument(
            introduction=f"This document presents the jury's analysis to evaluate the original claim: '{original_claim}'...",
            questions=results,
            conclusion="Based on the above responses and evidence, please provide a logical conclusion regarding the claim."
        )
        # JSON 직렬화 가능하게 dict로 변환
        return json.loads(json.dumps(doc, default=lambda o: o.__dict__, ensure_ascii=False))
