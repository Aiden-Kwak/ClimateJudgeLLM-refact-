import json

class LawyerPromptBuilder:
    @staticmethod
    def build_analysis_prompt(document: dict, claim: str) -> str:
        return f"""
        You are a skilled defense attorney specializing in logical analysis and argumentation.
        Your role is to critically evaluate the document provided and construct arguments that strongly favor the client’s position.

        The client’s claim is: "{claim}"

        Provided Document (Start):
        {json.dumps(document, ensure_ascii=False, indent=4)}
        Provided Document (End)
        """

    @staticmethod
    def build_reply_brief_prompt(prosecutor_brief: str, claim: str) -> str:
        return f"""
        You are a skilled defense attorney tasked with constructing a reply brief to refute the prosecutor’s arguments and strengthen the client’s position.

        The prosecutor’s reply brief is:
        {prosecutor_brief}

        The client’s claim is: "{claim}"
        """