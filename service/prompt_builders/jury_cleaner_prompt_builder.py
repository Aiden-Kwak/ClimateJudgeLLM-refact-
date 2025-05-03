import json

class JuryCleanerPromptBuilder:
    @staticmethod
    def build_jury_cleaner_prompt(target: json) -> str:
        return f"""
        You are a JSON assistant tasked with cleaning a legal claim analysis document.

        You will receive a JSON document with the following schema:
        {{
        "introduction": "string",
        "questions": [
            {{
            "question": "string (no prefix like 'Input:' or 'Output:')",
            "response": "string (≤250 characters)",
            "evidence": [
                {{
                "file_name": "string",
                "page_number": number,
                "text": "string (must be meaningful summary, not just a title or citation)"
                }}
            ]
            }},
            ...
        ]
        }}

        Your tasks:

        1. Do NOT change the structure, order, or keys.
        2. Remove any question whose "question" value contains "Input:" or "Output:".
        3. Remove any evidence item whose "text" is:
        - just a title (e.g., only author names, journal names, or DOIs),
        - lacks scientific content,
        - contains only citation metadata.
        4. For each remaining evidence[*].text:
        - Replace all characters that could break LaTeX with safe alternatives or remove them.
        - Specifically:
        • Replace “ and ” with straight double quotes (")
        • Replace ‘ and ’ with straight single quotes (')
        • Replace ellipsis (…) with three dots (...)
        • Remove control characters (e.g., �)
        • Remove subscript/superscript numbers (e.g., ₂ → 2, ⁵ → 5) or write them inline
        • Replace bullet points (•) with dashes or commas
        • Remove any non-printable characters
        - Rewrite into a readable summary of the scientific point (not citation).
        - You may shorten or paraphrase for clarity, but retain key content.
        5. Limit each question to at most 2 relevant evidence items.
        6. Make sure "response" is clear, accurate, and under 250 characters.

        ⚠️ Output Rules:
        - Return valid JSON only.
        - Do not wrap in markdown or code block.
        - Do not prepend with “Here is the JSON”.
        - Output must start with '{{' and end with '}}'.
        - The output must be directly usable with `json.loads()` in Python.

        =============== Target Document (Start) ===============
        {json.dumps(target, ensure_ascii=False, indent=2)}
        =============== Target Document (End) ================
        """
