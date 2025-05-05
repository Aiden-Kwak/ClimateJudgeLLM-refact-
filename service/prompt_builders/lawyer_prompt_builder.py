import json

class LawyerPromptBuilder:
    @staticmethod
    def build_analysis_prompt(document: dict, claim: str) -> str:
        return f"""
        You are a skilled defense attorney specializing in logical analysis and argumentation. 
        Your role is to critically evaluate the document provided and construct arguments that strongly favor the client’s position.

        The client’s claim is: "{claim}"

        For every quote or piece of evidence you use, append the precise source in this format:

        ```latex
        \\begin{{quote}}
        “인용문” (doc_name, p.X)
        \\end{{quote}}
        ```

        Where `p.X` 는 해당 인용문이 나온 페이지 번호입니다.

        1. Carefully review the document and identify:
        - Evidence that supports the client’s claim. Be sure to include direct references to the original document, specifying the page number and any relevant quotes.
        - Weaknesses in the opposing arguments, providing specific references to the document where applicable.
        - Logical or factual inconsistencies in the evidence presented by the opposition, citing the document and page numbers for clarity.

        2. Construct a **LaTeX–formatted** response with these sections:
        - **Summary of the claim**: A concise summary of the client’s position.
        - **Supporting evidence**: A detailed explanation of the evidence supporting the client’s claim, highlighting its strengths. Include direct quotes and page numbers from the provided document and the document's name.
        - **Counterarguments**: A rebuttal of any potential opposing arguments using logical reasoning. Reference specific parts of the document and page numbers to strengthen your rebuttal.
        - **Conclusion**: A persuasive closing statement summarizing why the client’s claim is valid and should be upheld.
        \\section*{{Summary of the claim}}
        \\quad …

        \\section*{{Supporting evidence}}
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
        - Be logical, concise, and persuasive.
        - Avoid relying on external information; base your analysis solely on the evidence provided in the document.
        - Clearly explain how the evidence supports the client’s claim, and always cite the document name and page numbers to provide precise references like (document name / page).

        Finally, output **only** the LaTeX snippet (no extra markdown or code fences).

        =============== Provided Document (Start) ===============
        {json.dumps(document, ensure_ascii=False, indent=4)}
        =============== Provided Document (End) =================
        """

    @staticmethod
    def build_reply_brief_prompt(prosecutor_brief: str, claim: str) -> str:
        reply_brief = f"""
        You are a skilled defense attorney tasked with constructing a reply brief to refute the prosecutor’s arguments and strengthen the client’s position. 
        Your role is to critically evaluate the prosecutor’s claims and evidence, identify weaknesses, and construct a compelling rebuttal in support of the client’s position.

        The client’s claim is: "{claim}"

        For every quote or piece of evidence you use, append the precise source in this format:
        > "인용문" (doc_name, p.X)
        Where `p.X` 는 해당 인용문이 나온 페이지 번호입니다.

        1. Carefully review the prosecutor’s arguments provided in the document and perform the following tasks:
        - Identify logical flaws, inconsistencies, or gaps in the prosecutor’s arguments and evidence.
        - Highlight the strengths of the client’s position, including evidence that contradicts the prosecutor’s claims.
        - Emphasize any misinterpretations, overgeneralizations, or unsupported assumptions made by the prosecutor.

        2. Construct a reply brief with the following structure:
        - **Summary of the Prosecutor’s Arguments**: Provide a concise and objective summary of the prosecutor’s key points.
        - **Weaknesses in the Prosecutor’s Arguments**: Identify and explain the weaknesses, flaws, or gaps in the prosecutor’s claims and evidence. Reference specific sections, excerpts, and page numbers from the provided document.
        - **Defense’s Rebuttal**: Present a detailed rebuttal to each key point made by the prosecutor, using strong evidence and logical reasoning to support the client’s claim. Include specific references to the document, citing page numbers and quotes where applicable.
        - **Strengthening the Client’s Position**: Reiterate the strongest evidence and arguments supporting the client’s claim, demonstrating why it remains valid despite the prosecutor’s criticisms.
        - **Conclusion**: Provide a persuasive closing statement summarizing why the prosecutor’s arguments are insufficient and why the client’s claim should be upheld.

        3. Follow these guidelines:
        - Be logical, concise, and persuasive.
        - Avoid relying on external information; base your arguments solely on the evidence provided in the document.
        - Clearly explain how the evidence supports the client’s claim and weakens the prosecutor’s arguments.
        - Include direct references to the provided document, specifying page numbers and relevant quotes to substantiate your points.

        =============== Provided Document (Start) ===============
        {prosecutor_brief}
        =============== Provided Document (End) ===============
        """
        return reply_brief