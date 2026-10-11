from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .nodes.plan import plan_node
from .nodes.research import research_node
from .nodes.review import review_node
from .nodes.write import write_node

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

def build_graph(checkpointer=None,store=None):
    builder = StateGraph(ReportState)
    builder.add_node("plan",plan_node)
    builder.add_node("research",research_node)
    builder.add_node("write",write_node)
    builder.add_node("review",review_node)

    builder.add_edge(START,"plan")
    builder.add_edge("plan","research")
    builder.add_edge("research","write")
    builder.add_edge("write","review")

    builder.add_conditional_edges(
        "review",
        route_after_review,
        {"finish":END,"revise":"research"},
    )

    return builder.compile(checkpointer=checkpointer or InMemorySaver(),store=store)
#模块级单例：被 LangGraph Server / FastAPI 直接引用（第 11、13 章）
graph = build_graph()