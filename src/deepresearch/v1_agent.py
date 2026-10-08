from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware, ModelRetryMiddleware,ToolRetryMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from .models import model_for
from .prompts import AGENT_SYSTEM
from .schemas import Report
from .tools import web_search,search_knowledge

def build_agent(config: dict | None = None):
    return create_agent(
        model=model_for("research",config),
        tools=[search_knowledge],
        system_prompt=AGENT_SYSTEM,
        response_format=Report,
        checkpointer=InMemorySaver(),
        middleware=[
            ModelCallLimitMiddleware(run_limit=20),
            ToolCallLimitMiddleware(thread_limit=30),
            ModelRetryMiddleware(max_retries=3),
            ToolRetryMiddleware(max_retries=2)
        ],
        name="researcher",
    )

def run(topic: str, config: dict | None = None):
    agent = build_agent(config)
    cfg = config or {}
    cfg.setdefault("configurable",{}).setdefault("thread_id",f"v1-{topic[:8]}")
    result = agent.invoke(
        {"messages":[{"role":"user","content":f"请研究这个主题：{topic}"}]},
        config=cfg,
    )
    return result["structured_response"]

if __name__=="__main__":
    r = run("宿傩和五条悟谁更强")
    print(r)