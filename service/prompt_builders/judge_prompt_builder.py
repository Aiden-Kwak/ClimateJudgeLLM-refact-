import json

class JudgePromptBuilder:
    @staticmethod
    def build_decision_prompt(judge_input: dict) -> str:
        return f"""
        You are a judge tasked with reviewing the arguments and evidence provided by both the defense and the prosecution to reach a fair and logical verdict.
        Your role is to:
        1. Analyze the jury's evaluation of the claim.
        2. Critically assess the arguments and rebuttals presented by both sides.
        3. Weigh the strengths and weaknesses of each side's arguments based on the evidence provided.

        Provided Document (Start):
        {json.dumps(judge_input, ensure_ascii=False, indent=4)}
        Provided Document (End)

        Your response must be structured as follows:
        1. **Summary of the Case**:
        2. **Analysis**:
        - Strengths and weaknesses of the defense’s arguments.
        - Strengths and weaknesses of the prosecution’s arguments.
        3. **Verdict**:
        """