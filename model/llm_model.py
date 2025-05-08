import requests
import json
from openai import OpenAI
from openai import APITimeoutError
import time

class LLMModel:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key
        self.max_retries = 3
        self.timeout = 30  # 30초 타임아웃

    """ 지원하지 않기로함
    def call_deepseek(self, prompt: str, model: str = "deepseek-chat"):
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            url=f"{self.deepseek_base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "system", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.9
            }
        )
        response.raise_for_status()
        return response.json()
    """

    def call_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> dict:
        client = OpenAI(api_key=self.openai_api_key, timeout=self.timeout)
        
        for attempt in range(self.max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.9
                )
                return response
            except APITimeoutError:
                if attempt == self.max_retries - 1:  # 마지막 시도였다면
                    raise  # 예외를 다시 발생시킴
                time.sleep(2 * (attempt + 1))  # 지수 백오프
                continue
            except Exception as e:
                raise  # 다른 예외는 바로 발생시킴

    @staticmethod
    def parse_response(response):
        #content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if hasattr(response, "choices"):
            choice = response.choices[0]
            content = choice.message.content.strip()
        else:
            content = response.get("choices", [{}])[0]\
                              .get("message", {})\
                              .get("content", "").strip()
        # 코드 블록 제거
        if content.startswith("```") and content.endswith("```"):
            content = content[content.find("\n") + 1:content.rfind("\n")].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return [q.strip() for q in content.split("\n") if q.strip()]