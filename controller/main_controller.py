# controller/main_controller.py

import os
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
