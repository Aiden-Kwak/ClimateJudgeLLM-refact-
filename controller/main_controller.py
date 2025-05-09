# controller/main_controller.py

import os
import json
import re
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

def convert_to_latex(text: str) -> str:
    if not text:
        return text
    
    # 이미 LaTeX 수식이 포함된 경우 건너뛰기
    if '$_' in text or '$^' in text:
        return text
    
    # 일반적인 유니코드 하첨자/상첨자를 LaTeX 형식으로 변환
    replacements = {
        'CO₂': 'CO$_2$',
        'H₂O': 'H$_2$O',
        'O₃': 'O$_3$',
        'CH₄': 'CH$_4$',
        'N₂O': 'N$_2$O',
        '₀': '$_0$',
        '₁': '$_1$',
        '₂': '$_2$',
        '₃': '$_3$',
        '₄': '$_4$',
        '₅': '$_5$',
        '₆': '$_6$',
        '₇': '$_7$',
        '₈': '$_8$',
        '₉': '$_9$',
        '⁰': '$^0$',
        '¹': '$^1$',
        '²': '$^2$',
        '³': '$^3$',
        '⁴': '$^4$',
        '⁵': '$^5$',
        '⁶': '$^6$',
        '⁷': '$^7$',
        '⁸': '$^8$',
        '⁹': '$^9$'
    }
    
    # 가장 긴 패턴부터 먼저 치환 (예: CO₂가 C, O, ₂ 각각으로 치환되는 것 방지)
    patterns = sorted(replacements.keys(), key=len, reverse=True)
    for pattern in patterns:
        text = text.replace(pattern, replacements[pattern])
    
    return text

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
        try:
            jury_clean_results = self.jury_clean._clean("jury_results.json", model_type="gpt-3.5-turbo")
            FileView.write_json("jury_results.json", jury_clean_results)
        except Exception as e:
            ConsoleView.print_info("[ERROR] 배심원단 평가 정제 실패. 원본을 유지합니다.")
            print("Error:", e)

        # 4) 변호사 의견
        ConsoleView.print_info("변호사 의견 생성 중...")
        lawyer_text = self.lawyer.analyze(
            "jury_results.json", 
            claim, 
            model_type="gpt-3.5-turbo"
        )
        # LaTeX 형식으로 변환
        lawyer_text = convert_to_latex(lawyer_text)
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
        # LaTeX 형식으로 변환
        prosecutor_text = convert_to_latex(prosecutor_text)
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
        # LaTeX 형식으로 변환
        prosecutor_reply = convert_to_latex(prosecutor_reply)
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
        # LaTeX 형식으로 변환
        lawyer_reply = convert_to_latex(lawyer_reply)
        FileView.write_text(
            os.path.join("reply_brief", "lawyer_reply_brief.txt"),
            lawyer_reply
        )

        # 7) 판사 의견
        ConsoleView.print_info("판사 의견 생성 중...")
        judge_input = {
            "jury_results": jury_clean_results,
            "lawyer_results": lawyer_text,
            "prosecutor_results": prosecutor_text,
            "lawyer_reply_brief": lawyer_reply,
            "prosecutor_reply_brief": prosecutor_reply
        }
        FileView.write_json("judge_input.json", judge_input)

        verdict = self.judge.decide(
            "judge_input.json", 
            model_type="gpt-3.5-turbo"
        )
        
        # verdict JSON 파싱 및 LaTeX 형식으로 변환
        try:
            verdict_json = json.loads(verdict)
            # 모든 텍스트 필드를 LaTeX 형식으로 변환
            for key in verdict_json:
                if isinstance(verdict_json[key], str):
                    verdict_json[key] = convert_to_latex(verdict_json[key])
            verdict = json.dumps(verdict_json, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            ConsoleView.print_info("[WARN] Judge response is not JSON. 기본값 사용.")
            verdict_json = {}

        FileView.write_text("judge_verdict.txt", verdict)

        # 8) 판결문 PDF 생성
        ConsoleView.print_info("판결문 PDF 생성 중...")
        try:
            verdict_json = json.loads(verdict)
        except json.JSONDecodeError:
            ConsoleView.print_info("[WARN] Judge response is not JSON. 기본값 사용.")
            verdict_json = {}

        # .env에서 CLAIM 가져오기
        claim_text = os.getenv("CLAIM", "")

        # 모든 언더스코어를 \_로 변환
        def escape_all_underscores(text):
            if not isinstance(text, str):
                return text
            # 이미 \_로 변환된 부분은 건너뛰기
            return text.replace('\\_', '\_').replace('_', '\_')

        # 모든 \\section을 \section으로 변환
        def normalize_sections(text):
            if not isinstance(text, str):
                return text
            text = text.replace('\\\\section', '\\section')
            text = text.replace('\\\\section*', '\\section*')
            text = text.replace('\\\\quad', '\\quad')
            text = text.replace('\\\\begin', '\\begin')
            text = text.replace('\\\\end', '\\end')
            text = text.replace('\\\\item', '\\item')
            return text

        # 판결문 컨텍스트 구성
        context = {
            "claim": normalize_sections(convert_to_latex(claim_text)),  # Claim 추가
            "executive_summary": normalize_sections(convert_to_latex(verdict_json.get("executive_summary", ""))),
            "summary": normalize_sections(convert_to_latex(verdict_json.get("summary", ""))),
            "original_excerpt": normalize_sections(convert_to_latex(verdict_json.get("original_excerpt", ""))),
            "source_file": normalize_sections(convert_to_latex(verdict_json.get("source_file", ""))),
            "source_page": normalize_sections(convert_to_latex(str(verdict_json.get("source_page", "")))),
            "verdict": normalize_sections(convert_to_latex(verdict_json.get("verdict", ""))),
            "classification": normalize_sections(convert_to_latex(verdict_json.get("classification", ""))),
            # appendix 데이터는 이미 LaTeX 형식이므로 이스케이프 처리하지 않음
            "lawyer_results": escape_all_underscores(normalize_sections(convert_to_latex(judge_input.get("lawyer_results", "").replace("\\", "\\")))),
            "prosecutor_results": escape_all_underscores(normalize_sections(convert_to_latex(judge_input.get("prosecutor_results", "").replace("\\", "\\"))))
        }

        VerdictPdfService(context)
