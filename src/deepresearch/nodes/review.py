from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from ..configuration import Configuration
from ..state import ReportState,ReviewResult
from ..models import model_for
from ..prompts import REVIEW_SYSTEM

def review_node(state:ReportState,config:RunnableConfig) -> Command:
    cfg = Configuration.from_runnable_config(config)
    model = model_for("reviewer",config).with_structured_output(ReviewResult)

    res = model.invoke([
        {"role":"system","content":REVIEW_SYSTEM},
        {"role":"user","content":f"主题：{state['topic']}\n\n报告草稿：\n{state['draft'][:12000]}"},
    ])
    res.passed = res.score >= 8

    rounds = state["revision_round"] + 1
    exhausted = rounds >= cfg.max_revision_rounds

    if res.passed or exhausted:
        if exhausted and not res.passed:
            #次数用尽仍未达标：也要让它可追溯——把遗留问题写进报告
            res.issues = res.issues + ["已达最大修订轮次，以下问题未解决："] + res.issues[:3]
        return Command(update={"review":res,"revision_round":rounds},goto="__end__")
    return Command(update={"review":res,"revision_round":rounds},goto="research")
