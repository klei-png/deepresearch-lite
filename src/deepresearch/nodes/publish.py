from pathlib import Path

from ..state import ReportState
from ..configuration import RunnableConfig

def publish_node(state: ReportState,config: RunnableConfig) -> dict:
    """确定性节点：把最终报告写到文件中。"""
    out = Path("outputs")
    out.mkdir(exist_ok=True)
    name = state["topic"][:30].replace("/","_")
    (out / f"{name}.md").write_text(state["draft"],encoding="utf-8")
    return {"published_path":str(out / f"{name}.md")}