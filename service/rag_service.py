from easy_rag import RagService
from typing import Any

class RagIndexService:
    def __init__(
        self,
        embedding_model: str,
        response_model: str,
        openai_key: str,
        deepseek_key: str = None,
        deepseek_url: str = None
    ):
        self.rs = RagService(
            embedding_model=embedding_model,
            response_model=response_model,
            open_api_key=openai_key,
            deepseek_api_key=deepseek_key,
            deepseek_base_url=deepseek_url
        )

    def embed_resources(self, folder_name: str, force_update: bool = False):

        return self.rs.rsc(
            folder_name,
            force_update=force_update
        )

    def query(self, resource: Any, question: str, evidence_num: int = 30):
        return self.rs.generate_response(resource, question, evidence_num=evidence_num)