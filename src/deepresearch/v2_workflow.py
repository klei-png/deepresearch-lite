from .graph import build_graph
from .state import ReportState

def run(topic: str,config: dict|None = None) -> ReportState:
    g = build_graph()
    cfg = config or {}
    cfg.setdefault("configurable",{}).setdefault("thread_id",f"v2-{topic[:8]}")
    return g.invoke({"topic":topic,"messages":[]},config=cfg)

if __name__=="__main__":
    g = build_graph()
    print(g.get_graph().draw_ascii())