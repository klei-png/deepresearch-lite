from langchain_core.runnables import RunnableConfig

from ..configuration import Configuration
from ..models import model_for
from ..prompts import WRITE_SYSTEM,REVIEW_SYSTEM
from ..schemas import Report
from ..state import ReportState,ReviewResult

def write_node(state: ReportState,config: RunnableConfig) -> dict:
    cfg = Configuration.from_runnable_config(config)
    model = model_for("writer",config).with_structured_output(Report)
    issues = ""
    if state.get("review") and state["review"].issues:
        issues =  "上次评审提出的必须修改项：\n" + "\n".join(f"- {i}" for i in state["review"].issues)
    report = model.invoke([
        {"role":"system","content":WRITE_SYSTEM},
        {"role":"user","content":(
            f"主题：{state['topic']}\n"
            f"提纲：{[s.title for s in state['plan']]}\n"
            f"调研笔记：\n{chr(10).join(state['notes'])}\n\n"
            f"{issues}\n请输出完整报告。"
        )}
    ])
    return {"draft": _to_markdown(report),"final":report}
def review_node(state:ReportState,config:RunnableConfig) -> dict:
    model = model_for("reviewer",config).with_structured_output(ReviewResult)
    res = model.invoke([
        {"role":"system","content":REVIEW_SYSTEM},
        {"role":"user","content":f"主题：{state['topic']}\n\n报告草稿：\n{state['draft'][:12000]}"},
    ])
    res.passed = res.score >= 8
    return {"review": res,"revision_round":state["revision_round"]+1}

def _to_markdown(r:Report) -> str:
    md = f"# {r.title}\n\n>{r.abstract}\n\n"
    for s in r.sections:
        md += f"## {s.title}\n\n{s.content}\n\n"
    return md