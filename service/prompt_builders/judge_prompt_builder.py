import json

class JudgePromptBuilder:
    @staticmethod
    def build_decision_prompt(judge_input: dict, classification_results: str = "{}") -> str:
        """
        Builds a prompt for the judge's decision-making process.
        
        Args:
            judge_input (dict): Input data for the judge
            classification_results (str): Classification results JSON string (default: "{}")
            
        Returns:
            str: The generated prompt
        """
        evidence_list = []
        # Extract evidence list
        for question in judge_input.get("jury_results", {}).get("questions", []):
            for ev in question.get("evidence", []):
                evidence_list.append({
                    "file_name": ev.get("file_name", ""),
                    "page_number": ev.get("page_number", 0),
                    "text": ev.get("text", "")
                })

        # Try to extract claim
        claim = ""
        if "claim" in judge_input:
            claim = judge_input["claim"]

        prompt = f"""
        You are a judge tasked with reviewing evidence and arguments to make a final decision.

        ⚠️ CRITICAL INSTRUCTION FOR CITATIONS AND FORMATTING ⚠️
        1. You can ONLY cite from the following evidence list:
        {json.dumps(evidence_list, ensure_ascii=False, indent=2)}

        2. IMPORTANT LaTeX Formatting Rules:
        - Use LaTeX math mode for chemical formulas and subscripts/superscripts
        - Examples:
          • CO₂ should be written as CO$_2$
          • H₂O should be written as H$_2$O
          • O₃ should be written as O$_3$
          • 10⁵ should be written as 10$^5$
        - NEVER use Unicode subscripts (₀₁₂₃₄₅₆₇₈₉) or superscripts (⁰¹²³⁴⁵⁶⁷⁸⁹)

        ## Claim to Evaluate
        {claim}

        ## Your Judicial Task:
        1. Review the evidence and arguments from both sides
        2. Identify the most relevant evidence that directly addresses the claim
        3. Analyze the logical consistency of arguments from both sides
        4. Make a final decision based on the evidence and arguments presented

        Your output must be a valid JSON with exactly these fields:
        {{
            "executive_summary": "One sentence that clearly states your final decision on the claim",
            
            "summary": "Brief summary of the key points from both sides (2-3 sentences)",
            
            "original_excerpt": "The most relevant evidence text that directly addresses the claim (MUST be an exact quote from evidence list)",
            "source_file": "The file name of the original_excerpt",
            "source_page": number (The page number of the original_excerpt),
            
            "verdict": "A comprehensive analysis that:
                      1. Logically integrates the defense and prosecution arguments
                      2. Evaluates the strength of each side's reasoning
                      3. Explains how you reached your final decision
                      4. Cites specific arguments from both sides to support your reasoning"
        }}

        ⚠️ Additional Rules:
        1. Use LaTeX math mode for ALL chemical formulas and numbers with subscripts/superscripts
        2. original_excerpt MUST be an exact match from the evidence list
        3. Focus on logical analysis and evidence-based reasoning
        4. Be explicit when evidence is insufficient
        5. Maintain judicial neutrality while explaining your decision

        Here is the full input context:
        {json.dumps(judge_input, ensure_ascii=False, indent=2)}
        """

        return prompt