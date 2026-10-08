import operator
from typing import Annotated,TypedDict
from langchain_core.messages import AnyMessage
from pydantic import BaseModel,Field
from langgraph.graph.message import add_messages

from .schemas import Report

class SectionPlan(BaseModel):
    """提纲中的一节"""
    title:str
    queries:list[str] = Field(description="为这一节准备的检索词，2-3个")

class ReviewResult(BaseModel):
    """评审结果"""
    score: int = Field(description="1-10分，8分及以上视为通过")
    issues: list[str] = Field(default_factory=list,description="必须修改的问题，按严重程度排序")
    passed: bool = False

class ReportState(TypedDict):
    # ---- 输入 ----
    topic: str
    # ---- 计划 ----
    plan: list[SectionPlan]
    # ---- 调研产物：Annotated + operator.add = "追加"语义 ----
    notes: Annotated[list[str],operator.add]
    # ---- 写作与评审 ----
    draft: str
    review: ReviewResult | None
    revision_round: int
    # ---- 输出 ----
    final: Report | None
    # ---- 对话式图才会用到（本例保留以演示 add_messages）----
    messages: Annotated[list[AnyMessage],add_messages]
