import os
import subprocess
import re
from jinja2 import Environment, FileSystemLoader

# 1) LaTeX 특수문자 이스케이프 함수
def escape_latex(s: str) -> str:
    if not isinstance(s, str):
        return s
    replacements = {
        '\\': r'\textbackslash{}',
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\^{}',
    }
    for orig, esc in replacements.items():
        s = s.replace(orig, esc)
    return s

# LaTeX filename 명령어 내부의 언더스코어 수정 함수
def fix_filename_underscores(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # \filename{...} 명령 내의 언더스코어 찾기
    pattern = r'\\filename\{([^}]*?_[^}]*?)\}'
    
    def fix_underscores(match):
        content = match.group(1)
        # 언더스코어를 이스케이프된 LaTeX 문법으로 변경
        fixed = content.replace('_', '\\_')
        return f'\\filename{{{fixed}}}'
    
    return re.sub(pattern, fix_underscores, s)

# 문서 내 LaTeX 문법 오류 수정 함수
def fix_latex_errors(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # 임시 마커 제거
    s = s.replace('TEMP_ESCAPED_UNDERSCORE', '\\_')
    
    # 이스케이프된 언더스코어 정규화
    s = re.sub(r'\\+_', lambda m: '\\' * (len(m.group(0)) // 2) + '_', s)
    
    # itemize 환경의 \item 명령어 수정 (이미 \\item인 경우 제외)
    s = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', 
               lambda m: re.sub(r'(?<!\\)\\item', '\\\\item', m.group(0)), 
               s, flags=re.DOTALL)
    
    # itemize 환경 내 파일명과 언더스코어 처리
    def fix_itemize_filenames(match):
        content = match.group(0)
        # filename 명령어 내 백슬래시 수 정규화
        content = re.sub(r'\\+filename\{', r'\filename{', content)
        # 언더스코어 제대로 이스케이프
        content = re.sub(r'([^\\])_', r'\1\_', content)
        # 이중 이스케이프 방지
        content = content.replace('\\_\\_', '\\_')
        return content
    
    s = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', 
               fix_itemize_filenames, 
               s, flags=re.DOTALL)
    
    # quote 환경 내 파일명과 언더스코어 처리
    def fix_quote_filenames(match):
        content = match.group(0)
        # filename 명령어 내 백슬래시 수 정규화
        content = re.sub(r'\\+filename\{', r'\filename{', content)
        # allowbreak 명령어 제거
        content = content.replace(r'\allowbreak', ' ')
        # 언더스코어 제대로 이스케이프
        content = re.sub(r'([^\\])_', r'\1\_', content)
        # 이중 이스케이프 방지
        content = content.replace('\\_\\_', '\\_')
        return content
    
    s = re.sub(r'\\begin\{quote\}(.*?)\\end\{quote\}', 
               fix_quote_filenames, 
               s, flags=re.DOTALL)
    
    # 수식 모드 관련 오류 수정
    s = s.replace('${}', '$')
    
    return s

# LaTeX 명령어의 백슬래시 수 정규화 함수
def normalize_latex_commands(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # 명령어 목록 (이런 명령어들의 백슬래시 수를 정규화)
    commands = ['item', 'begin', 'end', 'section', 'subsection', 'textit', 'textbf', 'filename']
    
    for cmd in commands:
        # 3개 이상의 백슬래시로 시작하는 명령어를 정규화 (\\\ 이상 → \)
        s = re.sub(r'\\{3,}' + cmd, r'\\' + cmd, s)
    
    return s

# 유니코드 그리스 문자 및 특수 기호를 LaTeX로 변환하는 함수
def convert_unicode_to_latex(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # 이미 변환된 문자는 무시
    if '$\\' in s:
        return s
    
    # 그리스 문자 및 특수 유니코드 문자 변환 맵핑
    unicode_map = {
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
    
    # 가장 긴 패턴부터 먼저 치환
    patterns = sorted(unicode_map.keys(), key=len, reverse=True)
    for pattern in patterns:
        s = s.replace(pattern, unicode_map[pattern])
    
    return s

# \\filename 명령어 정규화 함수
def normalize_filename_commands(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # \\filename{...} 패턴을 찾아 \filename{...}으로 변환
    pattern = r'\\+filename\{'
    s = re.sub(pattern, r'\filename{', s)
    
    # \allowbreak 명령어 수정
    s = s.replace(r'\allowbreakar5_', r'ar5\_')
    s = s.replace(r'\allowbreakfull', r'full')
    s = re.sub(r'\\allowbreak\s+', r'', s)
    
    return s

# 특정 문제 케이스 직접 처리
def fix_known_problematic_cases(s: str) -> str:
    if not isinstance(s, str):
        return s
    
    # 알려진 문제 케이스 패턴 수정
    problematic_patterns = [
        # 예제에서 발견된 문제
        (r'\\filename\{ipcc\\_wg3\\_\\allowbreakar5\\_\\allowbreakfull.pdf\}', 
         r'\\filename{ipcc\\_wg3\\_ar5\\_full.pdf}'),
        (r'\\allowbreak\s+', r' '),
        (r'\\allowbreakar5', r'ar5'),
        (r'\\allowbreakfull', r'full')
    ]
    
    for old, new in problematic_patterns:
        s = s.replace(old, new)
    
    return s

def VerdictPdfService(context, output_dir="results"):
    # 모든 문자열 필드에 대해 LaTeX 오류 수정 처리 적용
    for key in context:
        if isinstance(context[key], str):
            # 유니코드 문자 변환
            context[key] = convert_unicode_to_latex(context[key])
            # 알려진 문제 케이스 수정
            context[key] = fix_known_problematic_cases(context[key])
            # filename 명령어 내의 언더스코어 수정
            context[key] = fix_filename_underscores(context[key])
            # filename 명령어 정규화
            context[key] = normalize_filename_commands(context[key])
            # 일반적인 LaTeX 오류 수정
            context[key] = fix_latex_errors(context[key])
            # LaTeX 명령어 정규화
            context[key] = normalize_latex_commands(context[key])
    
    # 기존과 동일하게 템플릿 렌더링
    env = Environment(loader=FileSystemLoader("templates"), autoescape=False)
    tpl = env.get_template("verdict.tex.j2")
    tex_content = tpl.render(context)

    # 생성된 TeX 파일에 대해 최종 오류 수정 (전체 문서 컨텍스트에 필요한 수정)
    tex_content = convert_unicode_to_latex(tex_content)
    tex_content = fix_known_problematic_cases(tex_content)
    tex_content = normalize_filename_commands(tex_content)
    tex_content = fix_latex_errors(tex_content)
    tex_content = normalize_latex_commands(tex_content)
    
    os.makedirs(output_dir, exist_ok=True)
    tex_path = os.path.join(output_dir, "verdict.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # pdflatex 호출 + 로그
    cwd = os.path.abspath(output_dir)
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "verdict.tex"]
    log_path = os.path.join(cwd, "verdict_build.log")
    with open(log_path, "w", encoding="utf-8") as log_file:
        try:
            subprocess.run(cmd, cwd=cwd, stdout=log_file, stderr=log_file, check=True)
        except subprocess.CalledProcessError:
            log_file.flush()
            print("\n[ERROR] pdflatex failed. Last 20 lines of log:")
            with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                lines = lf.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
            raise
    print("[INFO] PDF Generated:", os.path.join(output_dir, "verdict.pdf"))
