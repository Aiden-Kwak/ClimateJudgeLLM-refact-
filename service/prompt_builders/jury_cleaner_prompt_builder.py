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
        • Replace " and " with straight double quotes (")
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
        - Do not prepend with "Here is the JSON".
        - Output must start with '{{' and end with '}}'.
        - The output must be directly usable with `json.loads()` in Python.

        =============== Target Document (Start) ===============
        {json.dumps(target, ensure_ascii=False, indent=2)}
        =============== Target Document (End) ================
        """

    @staticmethod
    def build_single_question_cleaner_prompt(question_data: dict) -> str:
        return f"""
        You are a JSON cleaning assistant. Your ONLY task is to clean and return a valid JSON object.

        ⚠️ CRITICAL OUTPUT RULES ⚠️
        1. You MUST return ONLY a valid JSON object
        2. DO NOT include any explanations, markdown formatting, or code blocks
        3. DO NOT add any text before or after the JSON
        4. Your entire response must be parseable by json.loads()
        5. Response MUST start with '{{' and end with '}}'

        Input Schema:
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
        }}

        Cleaning Rules:
        1. Remove any evidence item whose "text" is:
           - just a paper title (e.g., "Climate Change Effects on Arctic Ecosystems")
           - just author names and publication info (e.g., "Smith et al., Nature 2020")
           - just a journal citation (e.g., "Journal of Climate Science, Vol. 45")
           - just a DOI or URL
           - just a reference entry (e.g., "[1] Smith, J. (2020). Climate Change...")
           - lacks actual scientific content or findings
           - contains only metadata or bibliographic information
           - is just a section heading or figure caption without content
           
           Examples of text to remove:
           - "Smith, J., & Johnson, M. (2020). Effects of Climate Change. Nature, 580(7801)"
           - "Figure 1: Temperature changes over time"
           - "References"
           - "doi:10.1038/s41558-020-0739-7"
           - "Published in Environmental Science & Technology"

           The text MUST contain actual scientific findings, data, or meaningful content.

        2. For each remaining evidence[*].text:
           - Replace all characters that could break LaTeX with safe alternatives
           - Specifically:
             • Replace " and " with straight quotes (")
             • Replace ' and ' with straight quotes (')
             • Replace ellipsis (…) with three dots (...)
             • Remove control characters
             • Remove subscript/superscript numbers (e.g., ₂ → 2, ⁵ → 5)
             • Replace bullet points (•) with dashes or commas
             • Remove any non-printable characters
           - Rewrite into a readable summary of the scientific point
           - You may shorten or paraphrase for clarity, but retain key content

        3. Limit to at most 2 relevant evidence items
        4. Make sure "response" is clear, accurate, and under 250 characters
        5. Remove any "Input:" or "Output:" prefix from the question

        Input to clean:
        {json.dumps(question_data, ensure_ascii=False, indent=2)}

        Remember: Return ONLY the cleaned JSON object with no additional text or formatting.
        """
