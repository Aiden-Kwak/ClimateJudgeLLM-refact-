from model.data_models import QuestionResult
from model.llm_model import LLMModel

class QAService:
    def __init__(self, llm: LLMModel):
        self.llm = llm

    @staticmethod
    def _build_prompt(claim: str) -> str:
        return f"""
        The following is a claim provided by the user. Generate detailed questions needed to evaluate the validity of the claim. ... [이하 생략 없음]
        ===== Provided Claim (Start) =====
        {claim}
        ===== Provided Claim (End) =====
        """

    def generate_questions(self, claim: str) -> list[str]:
        prompt = self._build_prompt(claim)
        response = self.llm.call_openai(prompt, model="gpt-3.5-turbo")
        return self.llm.parse_response(response)
