import json

class JuryCleanerPromptBuilder:
    @staticmethod
    def build_jury_cleaner_prompt(target: json) -> str:
        return f"""
        You are an expert assistant refining a JSON document that includes a legal claim analysis.

        Each entry contains:
        - a question (string)
        - a response (string)
        - an evidence field: a JSON array of objects with "file_name", "page_number", and "text".

        Your task:
        1. For each question, review the list of evidence.
        2. Remove any evidence items that are irrelevant to the specific question.
        3. In each remaining evidence:
        - Remove or replace any problematic unicode characters that could break LaTeX (e.g., �, …, ₂, “, ”, •, etc).
        4. Do not change any keys, structure, or order. Only modify the evidence[*].text values or remove entries.
        5. Do not alter other fields such as "introduction", "response", or "question".

        Return only valid JSON and nothing else. Do not include explanation or commentary.

        =============== Target Document (Start) ===============
        {json.dumps(target, ensure_ascii=False, indent=4)}
        =============== Target Document (End) ================
        """
