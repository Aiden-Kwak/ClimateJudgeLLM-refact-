import json

class ClassificationPromptBuilder:
    @staticmethod
    def build_classification_prompt(judge_input: dict) -> str:
        evidence_list = []
        for question in judge_input.get("jury_results", {}).get("questions", []):
            for ev in question.get("evidence", []):
                evidence_list.append({
                    "file_name": ev.get("file_name", ""),
                    "page_number": ev.get("page_number", 0),
                    "text": ev.get("text", "")
                })

        claim = judge_input.get("claim", "")
        verdict_data = judge_input.get("verdict", {})
        verdict_summary = verdict_data.get("executive_summary", "")
        verdict_detail = verdict_data.get("verdict", "")

        classification_examples = {
            "Accurate": "The claim is well supported by strong, directly relevant evidence.",
            "Inaccurate": "The claim is directly refuted by credible evidence.",
            "Misleading": "The claim is technically correct but creates a false or deceptive impression.",
            "Overgeneralization": "The claim unjustifiably expands specific evidence to a broader or unwarranted conclusion.",
            "Unsupported": "There is insufficient or weak evidence to confirm or refute the claim."
        }

        prompt = f"""
        You are a fact-checking classification expert. Your role is to evaluate **the original claim itself**, not the quality of the arguments made by defense or prosecution.

        This claim has been debated in a courtroom-style environment where both sides cite only evidence from IPCC reports. You are now tasked with classifying the **scientific and logical validity of the claim**.

        ⚠️ CITATION AND FORMATTING RULES ⚠️
        1. Only use evidence from the list below (sourced from IPCC reports):
        {json.dumps(evidence_list, ensure_ascii=False, indent=2)}

        2. Format all chemical and scientific notation using LaTeX math mode:
        - CO₂ → CO$_2$, H₂O → H$_2$O, 10⁵ → 10$^5$
        - Never use Unicode subscripts or superscripts.

        ## Claim to Evaluate
        {claim}

        ## Judge's Verdict
        Executive Summary: {verdict_summary}

        Detailed Verdict: {verdict_detail}

        ## Classification Labels
        Choose one of the following:
        - **Accurate**: Well supported by clear and strong IPCC evidence.
        - **Inaccurate**: Clearly refuted by IPCC evidence.
        - **Misleading**: Technically true but leads to a false or exaggerated impression.
        - **Overgeneralization**: Extends limited evidence to a broad or unjustified conclusion.
        - **Unsupported**: Not enough evidence to support or refute; often speculative or vague.

        ## Evaluation Criteria (1 = poor, 5 = excellent)
        Rate the **claim itself** on the following dimensions. You are encouraged to use the full range of scores (1–5) to reflect variations in the claim’s merit.

        1. **Scientific Plausibility**  
        - **Score 5**: The claim aligns perfectly with established scientific consensus (e.g. clear IPCC position).  
        - **Score 3**: The claim partially aligns with accepted science but leaves room for debate.  
        - **Score 1**: The claim contradicts well-established scientific knowledge.

        2. **Logical Coherence**  
        - **Score 5**: The claim is internally consistent and logically sound.  
        - **Score 3**: The claim shows some logical structure but includes gaps or inconsistencies.  
        - **Score 1**: The claim contains major logical flaws or contradictions.

        3. **Scope Appropriateness**  
        - **Score 5**: The claim remains tightly within the limits of what the evidence supports.  
        - **Score 3**: The claim occasionally overreaches but is generally proportional to the evidence.  
        - **Score 1**: The claim grossly overgeneralizes or extrapolates far beyond the evidence.

        4. **Causal Justification**  
        - **Score 5**: The cause-effect relationships in the claim are well-established and clearly justified.  
        - **Score 3**: The claim suggests causation but with some ambiguity or insufficient detail.  
        - **Score 1**: The claim relies on faulty or unsupported causal reasoning.

        5. **Speculativeness**  
        - **Score 5**: The claim is entirely grounded in empirical data with little to no speculation.  
        - **Score 3**: The claim contains some speculative elements that weaken its certainty.  
        - **Score 1**: The claim is highly speculative or based on unverified assumptions.
        
        **Important:** Do not default all scores to 5. Vary the scores to accurately reflect uncertainties, logical gaps, or overgeneralizations in the **claim itself**.

        ## Instructions

        1. Read the claim and the judge's verdict carefully.
        2. Identify the most relevant IPCC evidence from the list.
        3. Evaluate the claim’s scientific and logical merit following the criteria above.
        4. Assign scores for each dimension and choose one overall classification label.
        5. Provide a 3–5 sentence justification explaining your ratings and final classification.

        ## Output Format (JSON)

        Return exactly this structure:

        {{
        "classification": "One of: Accurate, Inaccurate, Misleading, Overgeneralization, Unsupported",
        "justification": "3–5 sentence explanation of why this claim deserves this label",
        "scores": {{
            "scientific_plausibility": number (1-5),
            "logical_coherence": number (1-5),
            "scope_appropriateness": number (1-5),
            "causal_justification": number (1-5),
            "speculativeness": number (1-5)
        }},
        "key_evidence": "Exact quote from evidence list",
        "source_file": "File name of that evidence",
        "source_page": number (page number of key evidence)
        }}

        ## Classification Examples
        {json.dumps(classification_examples, ensure_ascii=False, indent=2)}

        Full Input Context:
        {json.dumps(judge_input, ensure_ascii=False, indent=2)}
        """

        return prompt
