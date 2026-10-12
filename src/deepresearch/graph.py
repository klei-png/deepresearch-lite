import os
import sqlite3
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore


from .configuration import Configuration
from .nodes.plan import plan_node
from .nodes.research import research_node
from .nodes.review import review_node
from .nodes.write import write_node
from .nodes.publish import publish_node
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
        cp = PostgresSaver.from_conn_string(os.environ["DATABASE_URL"])
        cp.setup()
        return cp
    return SqliteSaver.from_conn_string("storage/graph.db")

def build_graph(checkpointer=None,store=None):
    builder = StateGraph(ReportState)
    builder.add_node("plan",plan_node)
    builder.add_node("research",research_node)
    builder.add_node("write",write_node)
    builder.add_node("review",review_node)
    builder.add_node("publish",publish_node)

    builder.add_edge(START,"plan")
    builder.add_edge("plan","research")
    builder.add_edge("research","write")
    builder.add_edge("write","review")
    builder.add_edge("review","publish")
    builder.add_edge("publish",END)

    builder.add_conditional_edges(
        "review",
        route_after_review,
        {"finish":END,"revise":"research"},
    )

    return builder.compile(checkpointer=checkpointer or InMemorySaver(),store=store)
#模块级单例：被 LangGraph Server / FastAPI 直接引用（第 11、13 章）
graph = build_graph(
    checkpointer=SqliteSaver.from_conn_string("storage/graph.db"),
    store=InMemoryStore()
)



if __name__=="__main__":
    cfg = {"configurable":{"thread_id":"v2_demo"},"recursion_limit":50}
    for step in graph.stream({"topic":"Who is stronger, Satoru Gojo or Sukuna?","message":[]},config=cfg,stream_mode="updates"):
        for node, delta in step.items():
            if node == "review":
                r = delta["review"]
                print(f"评审：score={r.score} passed={r.passed} 轮次={delta.get('revision_round')}")
                print(" 问题：",r.issues[:3])
