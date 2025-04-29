import os
import subprocess
from jinja2 import Environment, FileSystemLoader

def VerdictPdfService(context, output_dir="results"):
    # 1) 템플릿 렌더링
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=False
    )
    tpl = env.get_template("verdict.tex.j2")
    tex_content = tpl.render(context)

    # 2) .tex 파일 저장
    os.makedirs(output_dir, exist_ok=True)
    tex_path = os.path.join(output_dir, "verdict.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # 3) pdflatex 호출 (2번 실행해 두면 목차/참조 처리 안정된다고함)
    cwd = os.path.abspath(output_dir)
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "verdict.tex"],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

    print("[INFO] PDF Generated:", os.path.join(output_dir, "verdict.pdf"))
