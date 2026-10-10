from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from ..configuration import Configuration
from ..models import model_for
from ..prompts import PLAN_SYSTEM
from ..state import ReportState,SectionPlan

class PlanOut(BaseModel):
    sections: list[SectionPlan]


def plan_node(state: ReportState, config: RunnableConfig) -> dict:
    """生成报告提纲：决定写几节、每节查什么。"""
    cfg = Configuration.from_runnable_config(config)
    model = model_for("planner", config).with_structured_output(PlanOut)
    out = model.invoke([
        {"role":"system","content":PLAN_SYSTEM},
        {"role": "user", "content":f"主题：{state['topic']}\n最多{cfg.max_sections}节"}
    ])
    return {"plan": out.sections, "revision_round":0}
