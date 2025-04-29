import json

class JudgePromptBuilder:
    @staticmethod
    def build_decision_prompt(judge_input: dict) -> str:
        return f"""
        You are a judge tasked with reviewing the arguments and evidence provided by both the defense and the prosecution to reach a fair and logical verdict. 
        Your role is to:
        1. Analyze the jury's evaluation of the claim.
        2. Critically assess the arguments and rebuttals presented by both the defense and the prosecution.
        3. Weigh the strengths and weaknesses of each side's arguments based on the evidence provided.

        Your verdict must:
        1. Summarize the key points from both sides.
        2. Identify which side has presented a stronger case, supported by specific reasoning and evidence.
        3. Conclude with a logical and fair judgment, stating whether the client’s claim is valid or not.

        You are only allowed to base your analysis on the following provided document. Avoid using external information.

        =============== Provided Document (Start) ===============
        {json.dumps(judge_input, ensure_ascii=False, indent=4)}
        =============== Provided Document (End) ===============

        Your response must be structured as follows:
        1. **Summary of the Case**: Provide an objective summary of the client’s claim and the arguments presented by both sides.
        2. **Analysis**:
        - Strengths and weaknesses of the defense’s arguments.
        - Strengths and weaknesses of the prosecution’s arguments.
        3. **Verdict**: State your final judgment and provide a concise explanation of your reasoning.
        """