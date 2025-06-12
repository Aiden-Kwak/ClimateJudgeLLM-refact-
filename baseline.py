import os
import json
import time
import argparse
from typing import List, Dict, Any, Tuple
import numpy as np
from dotenv import load_dotenv

from openai import OpenAI
import faiss

# 환경 설정
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_CLAIM = os.getenv("CLAIM", "기후 변화는 인간 활동에 의해 가속화되고 있다.")
client = OpenAI(api_key=OPENAI_API_KEY)

# 임베딩 및 RAG 관련 함수
def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """텍스트의 임베딩 벡터를 반환합니다."""
    response = client.embeddings.create(
        input=text.replace("\n", " "),
        model=model
    )
    return response.data[0].embedding

def load_existing_index() -> Tuple[faiss.IndexFlatIP, List[Dict[str, Any]]]:
    """기존 ClimateJudgeLLM의 FAISS 인덱스와 메타데이터를 로드합니다."""
    index_path = "rscFilesIndex/faiss_index.bin"
    metadata_path = "rscFilesIndex/metadata.json"
    
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError(f"인덱스 파일({index_path})이나 메타데이터 파일({metadata_path})이 존재하지 않습니다.")
    
    print("기존 인덱스 로딩 중...")
    index = faiss.read_index(index_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print(f"인덱스 로드 완료: {index.ntotal}개 벡터, 차원: {index.d}")
    print(f"메타데이터 로드 완료: {len(metadata)}개 항목")
    
    return index, metadata

def retrieve_documents(query: str, index: faiss.IndexFlatIP, metadata: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
    """쿼리와 관련된 상위 k개 문서를 검색합니다."""
    query_embedding = get_embedding(query)
    query_embedding_np = np.array([query_embedding], dtype=np.float32)
    
    # 검색 수행
    scores, indices = index.search(query_embedding_np, k)
    
    # 결과 구성
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(metadata):  # 유효한 인덱스 확인
            doc = metadata[idx].copy()
            doc["score"] = float(scores[0][i])
            results.append(doc)
    
    return results

# LLM 평가 함수
def evaluate_claim_traditional(claim: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """전통적인 방식으로 주장을 평가합니다 (RAG 없음)."""
    prompt = f"""당신은 기후 변화 주장을 평가하는 전문가입니다. 다음 기후 관련 주장을 평가하고 정확성을 판단하세요:

주장: "{claim}"

다음 카테고리 중 하나로 분류하세요:
- 정확함 (Accurate): 주장이 과학적 증거로 강력하게 뒷받침됨
- 부정확함 (Inaccurate): 주장이 신뢰할 수 있는 증거에 의해 직접 반박됨
- 오해의 소지가 있음 (Misleading): 주장이 기술적으로는 맞지만 잘못된 인상을 줌
- 과잉 일반화 (Overgeneralization): 주장이 특정 증거를 더 넓은 결론으로 부당하게 확대함
- 근거 부족 (Unsupported): 주장을 확인하거나 반박할 증거가 부족함

JSON 형식으로 다음 정보를 제공해주세요:
1. 분류 (classification)
2. 신뢰도 (confidence) - 0에서 1 사이의 값
3. 이유 (rationale) - 평가 근거 설명
4. 권장 출처 (suggested_sources) - 이 주장을 더 잘 평가하기 위해 참고할만한 자료 유형

응답은 반드시 유효한 JSON 형식이어야 합니다.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a climate science expert evaluating claims for accuracy."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        result["model"] = model
        result["method"] = "traditional"
        return result
    except json.JSONDecodeError:
        return {
            "error": "응답을 JSON으로 파싱할 수 없습니다",
            "raw_response": response.choices[0].message.content,
            "model": model,
            "method": "traditional"
        }

def evaluate_claim_rag(claim: str, index: faiss.IndexFlatIP, metadata: List[Dict[str, Any]], model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """RAG 방식으로 주장을 평가합니다."""
    # 관련 문서 검색
    relevant_docs = retrieve_documents(claim, index, metadata, k=5)
    
    # 문맥 구성
    context = "\n\n".join([
        f"출처: {doc.get('source', 'Unknown')}, 페이지: {doc.get('page', 0)}\n{doc.get('text', doc.get('content', ''))}" 
        for doc in relevant_docs
    ])
    
    prompt = f"""당신은 기후 변화 주장을 평가하는 전문가입니다. 다음 기후 관련 주장을 제공된 문맥 정보를 기반으로 평가하세요:

주장: "{claim}"

문맥 정보:
{context}

제공된 문맥 정보만을 기반으로 평가하세요. 문맥에 관련 정보가 없다면 "근거 부족"으로 분류하세요.

다음 카테고리 중 하나로 분류하세요:
- 정확함 (Accurate): 주장이 제공된 문맥의 증거로 강력하게 뒷받침됨
- 부정확함 (Inaccurate): 주장이 제공된 문맥의 증거에 의해 직접 반박됨
- 오해의 소지가 있음 (Misleading): 주장이 기술적으로는 맞지만 잘못된 인상을 줌
- 과잉 일반화 (Overgeneralization): 주장이 특정 증거를 더 넓은 결론으로 부당하게 확대함
- 근거 부족 (Unsupported): 제공된 문맥에서 주장을 확인하거나 반박할 증거가 부족함

JSON 형식으로 다음 정보를 제공해주세요:
1. 분류 (classification)
2. 신뢰도 (confidence) - 0에서 1 사이의 값
3. 이유 (rationale) - 평가 근거 설명
4. 사용한 증거 (evidence_used) - 평가에 사용된 가장 중요한 증거 인용

응답은 반드시 유효한 JSON 형식이어야 합니다.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a climate science expert evaluating claims based on provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        result["model"] = model
        result["method"] = "rag"
        # 사용된 문서 정보 추가
        result["retrieved_documents"] = [
            {
                "source": doc.get("source", "Unknown"), 
                "page": doc.get("page", 0), 
                "score": doc.get("score", 0.0)
            } 
            for doc in relevant_docs
        ]
        return result
    except json.JSONDecodeError:
        return {
            "error": "응답을 JSON으로 파싱할 수 없습니다",
            "raw_response": response.choices[0].message.content,
            "model": model,
            "method": "rag"
        }

# 메인 함수
def run_baseline_test(claim: str, models: List[str]) -> Dict[str, Any]:
    """주어진 주장에 대해 다양한 모델과 방법으로 베이스라인 테스트를 실행합니다."""
    results = {}
    
    # 기존 인덱스 및 메타데이터 로드
    index, metadata = load_existing_index()
    
    for model in models:
        print(f"\n{model} 평가 시작...")
        
        # 전통적 방식 평가
        start_time = time.time()
        traditional_result = evaluate_claim_traditional(claim, model)
        traditional_time = time.time() - start_time
        traditional_result["execution_time"] = traditional_time
        
        # RAG 방식 평가
        start_time = time.time()
        rag_result = evaluate_claim_rag(claim, index, metadata, model)
        rag_time = time.time() - start_time
        rag_result["execution_time"] = rag_time
        
        results[f"{model}_traditional"] = traditional_result
        results[f"{model}_rag"] = rag_result
        
        print(f"  전통적 방식: {traditional_result.get('classification', 'N/A')}, 신뢰도: {traditional_result.get('confidence', 'N/A')}")
        print(f"  RAG 방식: {rag_result.get('classification', 'N/A')}, 신뢰도: {rag_result.get('confidence', 'N/A')}")
    
    # 결과 저장
    timestamp = int(time.time())
    with open(f"baseline_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="기후 주장에 대한 베이스라인 평가")
    parser.add_argument("--claim", type=str, default=DEFAULT_CLAIM, help="평가할 기후 관련 주장 (기본값: 환경변수 CLAIM)")
    parser.add_argument("--models", type=str, nargs="+", default=["gpt-3.5-turbo", "gpt-4o"], 
                        help="사용할 모델 목록")
    
    args = parser.parse_args()
    
    print("====== 기후 주장 베이스라인 평가 시작 ======")
    print(f"주장: {args.claim}")
    print(f"사용 모델: {args.models}")
    
    results = run_baseline_test(args.claim, args.models)
    
    print("\n====== 평가 완료 ======")
    print(f"결과가 JSON 파일로 저장되었습니다.") 