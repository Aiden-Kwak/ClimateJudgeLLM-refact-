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
from service.classification_service import ClassificationService
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
        '⁹': '$^9$',
        # 그리스 문자 및 특수 유니코드 문자 추가
        'μ': '$\\mu$',
        'α': '$\\alpha$',
        'β': '$\\beta$',
        'γ': '$\\gamma$',
        'Γ': '$\\Gamma$',
        'δ': '$\\delta$',
        'Δ': '$\\Delta$',
        'ε': '$\\varepsilon$',
        'ζ': '$\\zeta$',
        'η': '$\\eta$',
        'θ': '$\\theta$',
        'Θ': '$\\Theta$',
        'ι': '$\\iota$',
        'κ': '$\\kappa$',
        'λ': '$\\lambda$',
        'Λ': '$\\Lambda$',
        'ν': '$\\nu$',
        'ξ': '$\\xi$',
        'Ξ': '$\\Xi$',
        'π': '$\\pi$',
        'Π': '$\\Pi$',
        'ρ': '$\\rho$',
        'σ': '$\\sigma$',
        'Σ': '$\\Sigma$',
        'τ': '$\\tau$',
        'υ': '$\\upsilon$',
        'φ': '$\\phi$',
        'Φ': '$\\Phi$',
        'χ': '$\\chi$',
        'ψ': '$\\psi$',
        'Ψ': '$\\Psi$',
        'ω': '$\\omega$',
        'Ω': '$\\Omega$',
        '±': '$\\pm$',
        '×': '$\\times$',
        '÷': '$\\div$',
        '∞': '$\\infty$',
        '≤': '$\\leq$',
        '≥': '$\\geq$',
        '≠': '$\\neq$',
        '≈': '$\\approx$',
        '∑': '$\\sum$',
        '∏': '$\\prod$',
        '∫': '$\\int$',
        '√': '$\\sqrt{}$',
        '∂': '$\\partial$',
        '∇': '$\\nabla$',
        '∝': '$\\propto$',
        '∈': '$\\in$',
        '∉': '$\\notin$',
        '∀': '$\\forall$',
        '∃': '$\\exists$',
        '∅': '$\\emptyset$',
        '∩': '$\\cap$',
        '∪': '$\\cup$',
        '⊂': '$\\subset$',
        '⊃': '$\\supset$',
        '⊆': '$\\subseteq$',
        '⊇': '$\\supseteq$'
    }
    
    # 가장 긴 패턴부터 먼저 치환 (예: CO₂가 C, O, ₂ 각각으로 치환되는 것 방지)
    patterns = sorted(replacements.keys(), key=len, reverse=True)
    for pattern in patterns:
        text = text.replace(pattern, replacements[pattern])
    
    return text

# LaTeX 아이템 목록을 안전하게 처리하는 함수
def sanitize_latex_items(text: str) -> str:
    if not text:
        return text
    
    # \begin{itemize}와 \end{itemize} 사이의 내용을 찾아서 처리
    item_pattern = r"\\begin\{itemize\}(.*?)\\end\{itemize\}"
    
    def process_itemize(match):
        content = match.group(1)
        # \item 태그가 백슬래시 없이 있는 경우만 수정 (이미 이스케이프된 경우 제외)
        content = re.sub(r"(?<!\\)\\item", "\\\\item", content)
        # \textit{...} 내부의 언더스코어 처리
        content = re.sub(r"\\textit\{([^}]*?)_([^}]*?)\}", 
                         lambda m: f"\\textit{{{m.group(1)}\\_\\allowbreak{m.group(2)}}}", 
                         content)
        return f"\\begin{{itemize}}{content}\\end{{itemize}}"
    
    # 정규표현식을 사용하여 itemize 환경을 찾고 처리
    text = re.sub(item_pattern, process_itemize, text, flags=re.DOTALL)
    
    return text

# 파일 경로 이름에 있는 언더스코어를 처리하는 함수
def sanitize_file_paths(text: str) -> str:
    if not text:
        return text
    
    # 파일명 패턴을 찾아서 언더스코어 이스케이프 처리
    file_pattern = r'([A-Za-z0-9]+)_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.pdf'
    textit_file_pattern = r'\\textit\{([A-Za-z0-9]+)_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.pdf\}'
    filename_pattern = r'\\filename\{([A-Za-z0-9]+)_([A-Za-z0-9]+)_([A-Za-z0-9]+)\.pdf\}'
    
    def escape_underscores_in_filename(match):
        return f"{match.group(1)}\\_\\allowbreak{match.group(2)}\\_\\allowbreak{match.group(3)}.pdf"
    
    def escape_underscores_in_textit(match):
        return f"\\textit{{{match.group(1)}\\_\\allowbreak{match.group(2)}\\_\\allowbreak{match.group(3)}.pdf}}"
    
    def escape_underscores_in_filename_cmd(match):
        return f"\\filename{{{match.group(1)}\\_\\allowbreak{match.group(2)}\\_\\allowbreak{match.group(3)}.pdf}}"
    
    # 정규표현식을 사용하여 파일명 패턴 대체
    text = re.sub(filename_pattern, escape_underscores_in_filename_cmd, text)
    text = re.sub(textit_file_pattern, escape_underscores_in_textit, text)
    text = re.sub(file_pattern, escape_underscores_in_filename, text)
    
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
        self.classification = ClassificationService(self.llm)
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
        # LaTeX 아이템 목록 및 파일경로 처리
        lawyer_text = sanitize_latex_items(lawyer_text)
        lawyer_text = sanitize_file_paths(lawyer_text)
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
        # LaTeX 아이템 목록 및 파일경로 처리
        prosecutor_text = sanitize_latex_items(prosecutor_text)
        prosecutor_text = sanitize_file_paths(prosecutor_text)
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
        # LaTeX 아이템 목록 및 파일경로 처리
        prosecutor_reply = sanitize_latex_items(prosecutor_reply)
        prosecutor_reply = sanitize_file_paths(prosecutor_reply)
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
        # LaTeX 아이템 목록 및 파일경로 처리
        lawyer_reply = sanitize_latex_items(lawyer_reply)
        lawyer_reply = sanitize_file_paths(lawyer_reply)
        FileView.write_text(
            os.path.join("reply_brief", "lawyer_reply_brief.txt"),
            lawyer_reply
        )

        # 7) 판사 입력 준비
        ConsoleView.print_info("판사 입력 준비 중...")
        judge_input = {
            "claim": claim,  # claim 추가
            "jury_results": jury_clean_results,
            "lawyer_results": lawyer_text,
            "prosecutor_results": prosecutor_text,
            "lawyer_reply_brief": lawyer_reply,
            "prosecutor_reply_brief": prosecutor_reply
        }
        FileView.write_json("judge_input.json", judge_input)
        
        # 7-1) 판사 의견 생성
        ConsoleView.print_info("판사 의견 생성 중...")
        verdict = self.judge.decide(
            "judge_input.json", 
            model_type="gpt-4.1-mini"
        )
        
        # verdict JSON 파싱 및 LaTeX 형식으로 변환
        try:
            verdict_json = json.loads(verdict)
            # 모든 텍스트 필드를 LaTeX 형식으로 변환
            for key in verdict_json:
                if isinstance(verdict_json[key], str):
                    verdict_json[key] = convert_to_latex(verdict_json[key])
                    # LaTeX 아이템 목록 및 파일경로 처리
                    verdict_json[key] = sanitize_latex_items(verdict_json[key])
                    verdict_json[key] = sanitize_file_paths(verdict_json[key])
            verdict = json.dumps(verdict_json, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            ConsoleView.print_info("[WARN] Judge response is not JSON. 기본값 사용.")
            verdict_json = {}

        FileView.write_text("judge_verdict.txt", verdict)
        
        # 7-2) 판사 판결에 대한 분류 수행
        ConsoleView.print_info("판사 판결에 대한 분류 수행 중...")
        # 판사 판결과 함께 judge_input 확장
        classification_input = judge_input.copy()
        classification_input["verdict"] = verdict_json
        FileView.write_json("classification_input.json", classification_input)
        
        # 분류 실행
        classification_results = self.classification.classify(
            "classification_input.json",
            model_type="gpt-3.5-turbo"
        )
        
        # classification_results 저장
        FileView.write_text("classification_results.txt", classification_results)

        # 8) 판결문 PDF 생성
        ConsoleView.print_info("판결문 PDF 생성 중...")
        try:
            # classification_results 파싱
            try:
                classification_json = json.loads(classification_results)
                # 텍스트 필드를 LaTeX 형식으로 변환
                if "justification" in classification_json and isinstance(classification_json["justification"], str):
                    classification_json["justification"] = convert_to_latex(classification_json["justification"])
                    classification_json["justification"] = sanitize_latex_items(classification_json["justification"])
                    classification_json["justification"] = sanitize_file_paths(classification_json["justification"])
                
                if "key_evidence" in classification_json and isinstance(classification_json["key_evidence"], str):
                    classification_json["key_evidence"] = convert_to_latex(classification_json["key_evidence"])
                    classification_json["key_evidence"] = sanitize_latex_items(classification_json["key_evidence"])
                    classification_json["key_evidence"] = sanitize_file_paths(classification_json["key_evidence"])
                
                # PDF 컨텍스트에 classification 결과 추가
                verdict_json["justification"] = classification_json.get("justification", "")
                verdict_json["scores"] = classification_json.get("scores", {})
                verdict_json["classification"] = classification_json.get("classification", verdict_json.get("classification", ""))
                # key_evidence가 있으면 original_excerpt로 사용 (만약 판사가 지정하지 않았다면)
                if "key_evidence" in classification_json and (not verdict_json.get("original_excerpt") or verdict_json.get("original_excerpt") == ""):
                    verdict_json["original_excerpt"] = classification_json.get("key_evidence", "")
                    verdict_json["source_file"] = classification_json.get("source_file", "")
                    verdict_json["source_page"] = classification_json.get("source_page", 0)
            except json.JSONDecodeError:
                ConsoleView.print_info("[WARN] Classification response is not JSON. 판사 결과만 사용.")
        except Exception as e:
            ConsoleView.print_info(f"[ERROR] PDF 준비 중 오류 발생: {e}")
            verdict_json = {}

        # .env에서 CLAIM 가져오기
        claim_text = os.getenv("CLAIM", claim)  # 기본값으로 입력 claim 사용

        # 모든 언더스코어를 \_로 변환하는 함수 개선
        def escape_all_underscores(text):
            if not isinstance(text, str):
                return text
            
            # 이미 이스케이프된 언더스코어 패턴 처리
            text = re.sub(r'\\+_', lambda m: '\\' * (len(m.group(0)) // 2) + '_', text)
            
            # 일반 언더스코어 이스케이프 (이미 이스케이프된 것은 제외)
            text = re.sub(r'(?<!\\)_', r'\\_', text)
            
            return text

        # 모든 \\section을 \section으로 변환하는 함수 개선
        def normalize_sections(text):
            if not isinstance(text, str):
                return text
            
            # 이중 백슬래시로 시작하는 LaTeX 명령어들 정규화
            latex_commands = [
                'section', 'section*', 'subsection', 'subsection*',
                'quad', 'begin', 'end', 'item', 'textit', 'textbf',
                'emph', 'it', 'bf', 'underline', 'hline', 'filename'
            ]
            
            for cmd in latex_commands:
                # 이스케이프된 이중 백슬래시 패턴을 단일 백슬래시로 변환
                text = text.replace(f'\\\\{cmd}', f'\\{cmd}')
            
            return text

        # 특수 LaTeX 문자 이스케이프 처리
        def escape_latex_special_chars(text):
            if not isinstance(text, str):
                return text
                
            # 일반 텍스트 환경에서 특수문자 이스케이프
            special_chars = ['%', '&', '$', '#', '{', '}']
            
            # 이미 이스케이프된 특수문자는 건너뜀
            for char in special_chars:
                escape_pattern = f'\\{char}'
                text = text.replace(char, escape_pattern).replace(f'{escape_pattern}{escape_pattern}', escape_pattern)
                
            return text
            
        # 판결문 컨텍스트 구성
        context = {
            "claim": normalize_sections(escape_latex_special_chars(convert_to_latex(claim_text))),
            "executive_summary": normalize_sections(escape_latex_special_chars(verdict_json.get("executive_summary", ""))),
            "summary": normalize_sections(escape_latex_special_chars(verdict_json.get("summary", ""))),
            "original_excerpt": normalize_sections(escape_latex_special_chars(verdict_json.get("original_excerpt", ""))),
            "source_file": normalize_sections(escape_all_underscores(verdict_json.get("source_file", ""))),
            "source_page": normalize_sections(str(verdict_json.get("source_page", ""))),
            "verdict": normalize_sections(escape_latex_special_chars(verdict_json.get("verdict", ""))),
            "classification": normalize_sections(escape_latex_special_chars(verdict_json.get("classification", ""))),
            # classification 추가 데이터
            "justification": normalize_sections(escape_latex_special_chars(verdict_json.get("justification", ""))),
            "scores": verdict_json.get("scores", {}),
            # appendix 데이터는 이미 처리된 상태
            "lawyer_results": normalize_sections(judge_input.get("lawyer_results", "")),
            "prosecutor_results": normalize_sections(judge_input.get("prosecutor_results", ""))
        }

        VerdictPdfService(context)
