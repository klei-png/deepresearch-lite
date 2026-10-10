import json

from langchain_core.runnables import RunnableConfig

from ..configuration import Configuration
from ..models import model_for
from ..state import ReportState
from ..tools import web_search

def research_nodes(state: ReportState,config: RunnableConfig) -> dict:
    """按提纲逐节检索。v2 串行；v4改造为并行"""
    cfg = Configuration.from_runnable_config(config)
    extra = state.get("review").issues if state.get("review") else []
    notes: list[str] = []

    for sec in state["plan"]:
        queries = sec.queries[: cfg.max_queries_per_section]
        if extra:
            queries = queries + [f"{sec.title} {extra[0]}"]
        hits = []
        for q in queries:
            hits.append(f"###检索词：{q}\n{web_search.invoke({'query': q, 'max_results': cfg.max_search_results})}")
        notes.append(f"## 章节：{sec.title}\n" + "\n".join(hits))
    #返回增量：因为notes是add reducer
    return {"notes":notes}
