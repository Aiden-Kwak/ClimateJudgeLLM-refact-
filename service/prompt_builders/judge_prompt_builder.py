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

        Finally, return your entire response **as valid JSON** matching exactly this schema:

        {{
            "executive_summary":    "string",
            "summary":              "string",
            "original_excerpt":     "string",
            "source_file":          "string",
            "source_page":          number,
            "background": [
                {{
                "name":        "string",
                "description": "string",
                "source_file": "string",
                "source_page": number
                }}
                …
            ],
            "original_defense": [
                {{
                "quote":       "string",
                "source_file": "string",
                "source_page": number
                }}
                …
            ],
            "defense_rebuttal": [
                {{
                "point":       "string",
                "quote":       "string",
                "source_file": "string",
                "source_page": number
                }}
                …
            ],
            "original_prosecution": [
                {{
                "quote":       "string",
                "source_file": "string",
                "source_page": number
                }}
                …
            ],
            "prosecution_rebuttal": [
                {{
                "point":       "string",
                "quote":       "string",
                "source_file": "string",
                "source_page": number
                }}
                …
            ],
            "sources": [
                {{
                "file":  "string",
                "pages": [number, …]
                }}
                …
            ],
            "verdict":              "string",
            "classification":       "string" // one of ["Accurate","Inaccurate","Misleading","Overgeneralization","Unsupported"]
        }}

        You are only allowed to base your analysis on the following provided document. Avoid using external information.

        =============== Provided Document (Start) ===============
        {json.dumps(judge_input, ensure_ascii=False, indent=4)}
        =============== Provided Document (End) ===============
        """