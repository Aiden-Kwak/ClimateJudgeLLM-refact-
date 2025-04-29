from typing import Protocol, Union

class LLMClient(Protocol):
    # 인터페이스 역할해주려는거임. 역할은 없는데 구현요구에 대한 시그니처 선언임.
    def call_deepseek(self, prompt: str, model: str) -> Union[dict, object]:
        raise NotImplementedError 

    def call_openai(self, prompt: str, model: str) -> Union[dict, object]:
        raise NotImplementedError

class BaseAgentService:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _invoke(self, prompt: str, model_type: str) -> str:
        if model_type == "deepseek-chat":
            resp = self.llm.call_deepseek(prompt, model="deepseek-chat")
        else:
            resp = self.llm.call_openai(prompt, model=model_type)

        if hasattr(resp, "choices"):
            return resp.choices[0].message.content.strip()
        else:
            return resp["choices"][0]["message"]["content"].strip()
