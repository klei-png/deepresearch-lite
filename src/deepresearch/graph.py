import os
import sqlite3
import psycopg
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command,Send

from .configuration import Configuration
from .nodes.plan import plan_node
from .nodes.research import research_node,research_section_node
from .nodes.review import review_node
from .nodes.write import write_node
from .nodes.publish import publish_node
from .nodes.approve import approve_plan_node
from .nodes.research_subgraph import section_graph

from .state import ReportState


def route_after_review(state:ReportState,config:RunnableConfig) -> str:
    """条件边的路由函数：返回下一个节点名（或END）"""
    cfg = Configuration.from_runnable_config(config)
    review = state["review"]
    if review is None:
        return "finish"
    if review.passed or state["revision_round"] >= cfg.max_revision_rounds:
        return "finish"
    return "revise"

def make_checkpointer(env: str = "dev"):
    if env == "prod":
        conn = psycopg.connect(os.environ["DATABASE_URL"],autocommit=True)
        saver = PostgresSaver(conn)
        saver.setup()
        return saver
    Path("storage").mkdir(exist_ok=True)
    conn = sqlite3.connect("storage/graph.db",check_same_thread=False)
    return SqliteSaver(conn)


def fanout_research(state: ReportState) -> list[Send]:
    """把提纲里的每一节派发成一个并行的调研任务"""
    sends = [
        Send("research_section",{
            "topic": state["topic"],
            "title": sec.title,
            "queries": sec.queries
        }) for sec in state["plan"]
    ]
    return sends

def fanout_node(state: ReportState) -> dict:
    """空节点"""
    return {}

def build_graph(checkpointer=None,store=None):
    builder = StateGraph(ReportState)
    builder.add_node("plan",plan_node)
    builder.add_node("approve_plan", approve_plan_node)
    builder.add_node("fanout",fanout_node)
    # builder.add_node("research_section", research_section_node)   #并行
    builder.add_node("research_section",section_graph)  #子图
    builder.add_node("research",research_node)
    builder.add_node("write",write_node)
    builder.add_node("review",review_node)
    builder.add_node("publish",publish_node)


    builder.add_edge(START,"plan")
    builder.add_edge("plan","approve_plan")
    builder.add_edge("approve_plan","fanout")

    builder.add_conditional_edges(
        "fanout",
        fanout_research,
        ["research_section"]
    )

    # builder.add_edge("approve_plan", "research")
    builder.add_edge("research_section", "write")
    builder.add_edge("write","review")

    builder.add_conditional_edges(
        "review",
        route_after_review,
        {"finish": "publish", "revise": "approve_plan"},
    )

    builder.add_edge("publish",END)

    return builder.compile(checkpointer=make_checkpointer("dev"),store=store)
#模块级单例：被 LangGraph Server / FastAPI 直接引用（第 11、13 章）
graph = build_graph(
    checkpointer=make_checkpointer("dev"),
    store=InMemoryStore()
)



if __name__=="__main__":
    cfg = {"configurable":{"thread_id":"v4-agent"},"max_concurrency":4,"recursion_limit":50}
    res = graph.invoke({"topic":"五条悟和宿傩谁更强","messages":[]},config=cfg)
    for key in res.keys():
        print(" -",key,end=",")
    if res.get("__interrupt__"):
        for i,intr in enumerate(res.get("__interrupt__")):
            payload = intr.value
            for k,v in payload.items():
                print(f"{k}:{v}")
        res = graph.invoke(Command(resume={"action":"approve"}),config=cfg)
    print("\n正文：",res.get("draft","")[:1000])
    print("\n评分：",res.get("review").score if res.get("review") else "无")
    print("\n轮次：",res.get("revision_round"))
