# controller/main_controller.py

import os
import json
from dotenv import load_dotenv

from model.llm_model import LLMModel
from service.rag_service import RagIndexService
from service.qa_service import QAService
from service.jury_service import JuryService
from service.lawyer_service import LawyerService
from service.prosecutor_service import ProsecutorService
from service.judge_service import JudgeService
from view.console_view import ConsoleView
from view.file_view import FileView
from service.pdf_service import VerdictPdfService
from service.jury_clean_service import JuryCleanService

class MainController:
    def __init__(self):
        load_dotenv()
        self.llm = LLMModel(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.rag = RagIndexService(
            embedding_model="text-embedding-3-small",
            response_model="gpt-3.5-turbo",
            openai_key=os.getenv("OPENAI_API_KEY")
        )
        self.qa         = QAService(self.llm)
        self.jury       = JuryService(self.rag)
        self.lawyer     = LawyerService(self.llm)
        self.prosecutor = ProsecutorService(self.llm)
        self.judge      = JudgeService(self.llm)
        self.jury_clean = JuryCleanService(self.llm)

    def run(self, claim: str, data_folder: str):
        # Ensure output dirs exist
        os.makedirs("results", exist_ok=True)
        os.makedirs("reply_brief", exist_ok=True)

        # 1) 질문 생성
        ConsoleView.print_info("세부 질문 생성 중...")
        questions = self.qa.generate_questions(claim)

        # 2) 리소스 임베딩
        ConsoleView.print_info(f"리소스 임베딩 중... 폴더={data_folder}")
        resource = self.rag.embed_resources(data_folder)

        # 3) 배심원단 평가
        ConsoleView.print_info("배심원단 평가 중...")
        jury_results = self.jury.evaluate(questions, resource, claim)
        FileView.write_json("jury_results.json", jury_results)

        # 3-1) 정제
        ConsoleView.print_info("배심원단 평가 정제 중...") # gpt-3.5-turbo / gpt-4o-mini
        jury_clean_response = self.jury_clean._clean("jury_results.json", model_type="gpt-3.5-turbo")

        # 1차 전처리: 코드블럭 제거, 여는 괄호부터 닫는 괄호까지 추출
        import re

        match = re.search(r"\{.*\}", jury_clean_response, re.DOTALL)
        if not match:
            ConsoleView.print_info("[ERROR] 정제된 결과에 JSON 구조가 없습니다. 원본을 유지합니다.")
            print(jury_clean_response)
        else:
            json_str = match.group(0)
            try:
                jury_clean_results = json.loads(json_str)
                FileView.write_json("jury_results.json", jury_clean_results)
            except json.JSONDecodeError as e:
                ConsoleView.print_info("[ERROR] 정제된 결과가 올바른 JSON 형식이 아닙니다. 원본을 유지합니다.")
                print("JSONDecodeError:", e)
                print(json_str)


        # 4) 변호사 의견
        ConsoleView.print_info("변호사 의견 생성 중...")
        lawyer_text = self.lawyer.analyze(
            "jury_results.json", 
            claim, 
            model_type="gpt-3.5-turbo"
        )
        FileView.write_text(
            os.path.join("results", "lawyer_results.txt"), 
            lawyer_text
        )

        # 5) 검사 의견
        ConsoleView.print_info("검사 의견 생성 중...")
        prosecutor_text = self.prosecutor.analyze(
            "jury_results.json",
            claim,
            model_type="gpt-3.5-turbo"
        )
        FileView.write_text(
            os.path.join("results", "prosecutor_results.txt"), 
            prosecutor_text
        )

        # 6) 검사 / 변호사 상호 반박 브리프
        ConsoleView.print_info("검사가 변호사의 의견을 검토 중...")
        prosecutor_reply = self.prosecutor.reply_brief(
            lawyer_reply_path=os.path.join("results", "lawyer_results.txt"),
            claim=claim,
            model_type="gpt-3.5-turbo"
        )
        FileView.write_text(
            os.path.join("reply_brief", "prosecutor_reply_brief.txt"),
            prosecutor_reply
        )

        ConsoleView.print_info("변호사가 검사의 리플라이 브리프를 검토 중...")
        lawyer_reply = self.lawyer.reply_brief(
            prosecutor_reply_path=os.path.join("reply_brief", "prosecutor_reply_brief.txt"),
            claim=claim,
            model_type="gpt-3.5-turbo"
        )
        FileView.write_text(
            os.path.join("reply_brief", "lawyer_reply_brief.txt"),
            lawyer_reply
        )

        # 7) 판사 의견
        ConsoleView.print_info("판사 의견 생성 중...")
        judge_input = self.judge.prepare_input(
            jury_path="jury_results.json",
            lawyer_results_path=os.path.join("results", "lawyer_results.txt"),
            prosecutor_results_path=os.path.join("results", "prosecutor_results.txt"),
            lawyer_reply_path=os.path.join("reply_brief", "lawyer_reply_brief.txt"),
            prosecutor_reply_path=os.path.join("reply_brief", "prosecutor_reply_brief.txt")
        )
        FileView.write_json("judge_input.json", judge_input)

        verdict = self.judge.decide(
            "judge_input.json", 
            model_type="gpt-3.5-turbo"
        )
        FileView.write_text("judge_verdict.txt", verdict)

        # 8) 판결문 PDF 생성
        ConsoleView.print_info("판결문 PDF 생성 중...")

        # verdict 텍스트를 JSON으로 파싱
        try:
            verdict_json = json.loads(verdict)
        except json.JSONDecodeError:
            ConsoleView.print_info("[WARN] Judge response is not JSON. 기본값 사용.")
            verdict_json = {}

        # JSON 스키마에 맞춰 꺼내기
        summary              = verdict_json.get("summary", "")
        original_excerpt     = verdict_json.get("original_excerpt", summary)
        source_file          = verdict_json.get("source_file", "")
        source_page          = verdict_json.get("source_page", "")
        background           = verdict_json.get("background", [])
        original_defense     = verdict_json.get("original_defense", [])
        defense_rebuttal     = verdict_json.get("defense_rebuttal", [])
        original_prosecution = verdict_json.get("original_prosecution", [])
        prosecution_rebuttal = verdict_json.get("prosecution_rebuttal", [])
        sources              = verdict_json.get("sources", [])
        verdict_text         = verdict_json.get("verdict", verdict)
        classification       = verdict_json.get("classification", "")

        context = {
            "executive_summary":    verdict_json.get("executive_summary", ""),
            "summary":              summary,
            "original_excerpt":     original_excerpt,
            "source_file":          source_file,
            "source_page":          source_page,
            "background":           background,
            "original_defense":     original_defense,
            "defense_rebuttal":     defense_rebuttal,
            "original_prosecution": original_prosecution,
            "prosecution_rebuttal": prosecution_rebuttal,
            "sources":              sources,
            "verdict":              verdict_text,
            "classification":       classification
        }


        VerdictPdfService(context)
