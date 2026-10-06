import argparse
from .v0_once import run

def main():
    ap = argparse.ArgumentParser(description="DeeResearch-Lite")
    ap.add_argument("topic",help="研究主题")
    ap.add_argument("--sections",type=int,default=5)
    args = ap.parse_args()

    report = run(args.topic,config={"configurable":{"max_sections":args.sections}})
    md = f"# {report.title}\n\n> {report.abstract}\n\n"
    for s in report.sections:
        md += f"* {s.title}\n\n{s.content}\n\n"
    if report.open_questions:
        md +=  "## 待验证问题\n\n" + "\n".join(f"- {q}" for q in report.open_questions)
    print(md)
if __name__ == "__main__":
    main()