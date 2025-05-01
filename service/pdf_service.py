import os
import subprocess
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

def VerdictPdfService(context, output_dir="results"):
    # 이스케이프 적용
    for key in ["summary", "original_excerpt", "verdict"]:
        context[key] = escape_latex(context.get(key, ""))
    context["source_file"] = escape_latex(context.get("source_file",""))

    # 기존과 동일하게 템플릿 렌더링
    env = Environment(loader=FileSystemLoader("templates"), autoescape=False)
    tpl = env.get_template("verdict.tex.j2")
    tex_content = tpl.render(context)

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
