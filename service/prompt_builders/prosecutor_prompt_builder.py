import json

class ProsecutorPromptBuilder:
    @staticmethod
    def build_analysis_prompt(document: dict, claim: str) -> str:
        return f"""
        You are a prosecutor tasked with...
        Original claim: "{claim}"

        Provided Document (Start):
        {json.dumps(document, ensure_ascii=False, indent=4)}
        Provided Document (End)
        """

    @staticmethod
    def build_reply_brief_prompt(defense_brief: str, claim: str) -> str:
        return f"""
        You are a prosecutor tasked with constructing a reply brief to refute the defense’s arguments...

        Defense Reply Brief:
        {defense_brief}

        Original claim: "{claim}"
        """
