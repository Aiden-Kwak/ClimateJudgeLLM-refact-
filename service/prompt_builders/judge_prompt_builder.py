import json

class JudgePromptBuilder:
    @staticmethod
    def build_decision_prompt(judge_input: dict) -> str:
        return f"""
        You are a judge tasked with reviewing arguments and evidence to reach a fair and logical verdict on a legal claim related to climate science.

        Each claim evaluation contains:
        - The jury’s evaluation of the question and sub-questions
        - Arguments from both the defense and prosecution
        - Raw evidence passages (field: "evidence") that must be the **only** source for all quotes

        Your responsibilities are:
        1. Base your entire judgment strictly and solely on the contents of the "evidence" field in the provided input. Do not refer to any generated summaries or externally imagined content.
        2. For every quote you include (from defense, prosecution, rebuttals, etc.), you must locate and **exactly match** a passage found in the provided evidence. Do not paraphrase or invent new text.
        3. Reflect the actual tone and nuance of the defense and prosecution. Do not over-summarize or clean up their arguments. Present them faithfully as they appear.
        4. Assign one of the five classification labels below, based on the following definitions:

        Classification Guidelines:
        - "Accurate": The client’s claim is well supported by strong, directly relevant, and properly cited scientific evidence.
        - "Inaccurate": The claim is refuted by evidence, and key factual elements are proven wrong.
        - "Misleading": The claim uses technically correct information in a way that creates a false impression.
        - "Overgeneralization": The claim takes a narrow, specific phenomenon and unjustifiably expands it into a broad conclusion.
        - "Unsupported": The claim lacks sufficient scientific evidence to be confirmed or refuted.

        Your output must:
        - Provide a short "executive_summary" clearly stating your final judgment.
        - Include a "summary" of the key debate.
        - Provide the "original_excerpt" and exact citation from the source file that contains the claim being evaluated. Set "original_excerpt" to the exact sentence or phrase from the evidence that contains the client's original claim — no paraphrasing, no explanation. It must match a passage in the evidence word-for-word.
        - Fill in quotes and rebuttals **with text exactly matching the evidence field** in the input, and **cite file name and page number**.
        - Only use content from the evidence list. Do not quote or refer to any text that is not directly available in the evidence.

        Finally, return your response strictly in this JSON format:

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

        =============== Provided Document (Start) ===============
        {json.dumps(judge_input, ensure_ascii=False, indent=4)}
        =============== Provided Document (End) ================
        """
