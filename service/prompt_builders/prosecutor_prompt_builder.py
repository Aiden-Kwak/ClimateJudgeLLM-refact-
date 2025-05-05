import json

class ProsecutorPromptBuilder:
    @staticmethod
    def build_analysis_prompt(document: dict, claim: str) -> str:
        return f"""
        You are a prosecutor tasked with critically evaluating the document provided by the jury.
        Your role is to identify weaknesses in the client’s claim and construct a compelling case against it.

        The client’s claim is: "{claim}"

        For every quote you use, wrap it in a LaTeX quote environment:
        ```latex
        \\begin{{quote}}
        “인용문” (doc_name, p.X)
        \\end{{quote}}
        ```
        Where `p.X` is the page number.

        1. Review the document and identify:
           - Evidence that weakens the client’s claim.  
           - Strengths in the opposing (defense) arguments that counter the client.  
           - Logical or factual inconsistencies in the client’s evidence.

        2. Construct a **LaTeX–formatted** response with these sections:

        \\section*{{Summary of the claim}}
        \\quad …

        \\section*{{Weaknesses in the evidence}}
        \\begin{{itemize}}
          \\item …  
            \\begin{{quote}}
            “인용문” (doc_name, p.X)
            \\end{{quote}}
          \\item …
        \\end{{itemize}}

        \\section*{{Counterarguments}}
        \\begin{{itemize}}
          \\item …  
            \\begin{{quote}}
            “인용문” (doc_name, p.X)
            \\end{{quote}}
        \\end{{itemize}}

        \\section*{{Conclusion}}
        \\quad …

        3. Follow these guidelines:
           - Base everything only on the provided document.
           - Use only LaTeX formatting (sections, itemize, quote).
           - Cite page numbers precisely.

        Finally, output **only** the LaTeX snippet (no extra markdown or code fences).

        =============== Provided Document (Start) ===============
        {json.dumps(document, ensure_ascii=False, indent=4)}
        =============== Provided Document (End) ================
        """

    @staticmethod
    def build_reply_brief_prompt(defense_brief: str, claim: str) -> str:
        reply_brief = f"""
        You are a prosecutor tasked with constructing a reply brief that critically evaluates the defense’s arguments and provides a compelling case to refute them.

        For every quote or piece of evidence you use, append the precise source in this format:
        > "인용문" (doc_name, p.X)
        Where `p.X` 는 해당 인용문이 나온 페이지 번호입니다.

        The defense’s argument is summarized in the provided document. Your role is to:
        1. Identify critical weaknesses in the defense’s argument, focusing on:
        - Logical flaws or inconsistencies in their reasoning.
        - Weak or unsupported evidence cited by the defense.
        - Misrepresentation or misinterpretation of key evidence or facts.
        2. Construct a compelling rebuttal to the defense’s argument, emphasizing:
        - Strong evidence that contradicts or undermines the defense’s position.
        - Logical reasoning that invalidates the defense’s conclusions.
        - The strengths of the prosecution’s original case.
        3. Clearly explain how the evidence and reasoning refute the defense’s claims, referencing specific sections, excerpts, and page numbers from the provided document.

        ### **Structure of the Reply Brief**
        1. **Summary of the Defense’s Argument**:
        - Provide a concise and objective summary of the key points in the defense’s argument.
        2. **Critical Weaknesses**:
        - Identify and explain the weaknesses, flaws, or gaps in the defense’s argument or evidence. Reference the original document with page numbers.
        3. **Prosecutor’s Counterarguments**:
        - Present a rebuttal to each key point in the defense’s argument. Use strong evidence from the provided document and logical reasoning to strengthen the prosecution’s case. Include direct citations (e.g., “Document A, Page 12”).
        4. **Conclusion**:
        - Summarize why the defense’s argument is invalid and reiterate the strength of the prosecution’s case.

        ### **Guidelines**:
        - Be logical, concise, and persuasive.
        - Avoid relying on external information; base your analysis solely on the evidence provided in the document.
        - Support all claims with specific references to the provided document, including page numbers and relevant excerpts.

        =============== Provided Document (Start) ===============
        {defense_brief}
        =============== Provided Document (End) ===============
        """
        return reply_brief
