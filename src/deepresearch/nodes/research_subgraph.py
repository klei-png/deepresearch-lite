import operator
from langgraph.graph import END, START, StateGraph
from typing import TypedDict,Annotated


from ..tools import web_search
from ..models import model_for

class SectionState(TypedDict):
    title: str
    queries: list[str]
    raw: str
    notes: Annotated[list[str],operator.add]

def search_node(s: SectionState, config) -> dict:
    hits = [web_search.invoke({"query": q}) for q in s["queries"]]
    return {"raw":"\n".join(hits)}

def summarize_node(s: SectionState, config) -> dict:
    """用便宜模型来生成压缩结果，用于节省token"""
    model = model_for("compression",config)
    out = model.invoke([
        {"role":"system","content":"将下面的检索结果压缩成300字以内的事实要点，保留数字时间与来源"},
        {"role":"user","content":s["raw"][:12000]}
    ])
    return {"notes":[f"##{s['title']}\n{out.content}"]}

def build_section_graph():
    b = StateGraph(SectionState)
    b.add_node("search",search_node)
    b.add_node("summarize",summarize_node)

    b.add_edge(START,"search")
    b.add_edge("search","summarize")
    b.add_edge("summarize",END)
    return b.compile()

section_graph = build_section_graph()