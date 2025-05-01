from model.data_models import QuestionResult
from model.llm_model import LLMModel

class QAService:
    def __init__(self, llm: LLMModel):
        self.llm = llm

    @staticmethod
    def _build_prompt(claim: str) -> str:
        return f"""
        The following is a claim provided by the user. Generate detailed questions needed to evaluate the validity of the claim. 
        Each question should help assess the logical basis, support or refute the claim, and actively explore counterexamples. 
        The generated questions should be output in python list format, with each question written as a single sentence. 
        Limit the number of questions to 5.
        ===== Provided Claim (Start) =====
        {claim}
        ===== Provided Claim (End) =====

        Input Format:
        "<text containing the claim>"

        Output Format:
        "<a sentence containing the purpose and content of the question>", \n
        ...

        Example Input:
        "Electric cars are more environmentally friendly."

        Example Output:
        "Scientific basis verification: How much lower is the carbon footprint of electric car production compared to internal combustion engine cars?",
        "Counterexample exploration: What are some examples of environmental issues caused by electric car battery waste?",
        "Relevant data verification: What research results compare the environmental impact of electric and internal combustion engine cars over their lifecycle?"
        """

    def generate_questions(self, claim: str) -> list[str]:
        prompt = self._build_prompt(claim)
        response = self.llm.call_openai(prompt, model="gpt-3.5-turbo")
        return self.llm.parse_response(response)
