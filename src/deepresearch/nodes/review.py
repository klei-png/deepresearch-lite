from langchain_core.runnables import RunnableConfig

from ..state import ReportState,ReviewResult
from ..models import model_for
from ..prompts import REVIEW_SYSTEM

def review_node(state:ReportState,config:RunnableConfig) -> dict:
    model = model_for("reviewer",config).with_structured_output(ReviewResult)
    res = model.invoke([
        {"role":"system","content":REVIEW_SYSTEM},
        {"role":"user","content":f"主题：{state['topic']}\n\n报告草稿：\n{state['draft'][:12000]}"},
    ])
    res.passed = res.score >= 8
    return {"review": res,"revision_round":state["revision_round"]+1}