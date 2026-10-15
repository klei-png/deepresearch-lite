from typing import Literal
from pydantic import BaseModel
from langgraph.graph import END,START,MessagesState,StateGraph
from langgraph.types import Command


from ..models import model_for
from .supervisor import build_member
from ..tools import web_search


def make_supervisor_node(members: dict[str,object],config=None):
    """主管节点：用结构化输出觉得‘下一个交给谁’或'结束'"""
    options = list(members)+["FINISH"]

    class Route(BaseModel):
        next: Literal[tuple(options)]
        reason: str

    model = model_for("planner",config).with_structured_output(Route)
    def supervisor_node(state: MessagesState) -> Command:
        print(f"\n{'=' * 50}")
        print(f"[supervisor] 当前消息数：{len(state['messages'])}")
        print(f"[supervisor] 最后一条：{state['messages'][-1].content[:80]}")

        res = model.invoke([
            {"role":"system","content":(
                f"你是主管，成员:{list(members)}。"
                "决定下一步交给谁；任务完成时输出FINISH。给出一句话理由"
            )},
            *state["messages"],
        ])
        print(f"[supervisor] 决定：{res.next}，理由：{res.reason}")

        goto = "__end__" if res.next == "FINISH" else res.next
        return Command(
            update={"message":[{"role":"assistant","content":f"[主管] -> {res.next}:{res.reason}"}]},
            goto=goto,
        )
    return supervisor_node

def build(config=None):
    members = {
        "tech_researcher":build_member("tech_researcher","...",[web_search],config),
        "writer":build_member("writer","...",[],config),
    }
    b = StateGraph(MessagesState)
    b.add_node("supervisor",make_supervisor_node(members,config))
    for name, agent in members.items():
        b.add_node(name,agent)
        b.add_edge(name,"supervisor")
    b.add_edge(START,"supervisor")
    return b.compile()


if __name__=="__main__":
    from langchain_core.messages import HumanMessage

    cfg = {
        "configurable": {"thread_id": "v5-agents"},
        "max_concurrency": 4,
        "recursion_limit": 50,
    }
    app = build(config=cfg)

    print("=" * 70)
    print("开始执行")
    print("=" * 70)

    final_state = None
    for state in app.stream(
            {"messages": [HumanMessage(content="研究五条悟和宿傩谁更强")]},
            config=cfg,
            stream_mode="values",  # ← 每步给完整 State
    ):
        final_state = state
        last = state["messages"][-1]
        role = last.__class__.__name__
        content = getattr(last, "content", str(last))
        print(f"\n>>> [STATE 更新] 消息数={len(state['messages'])}, 最后一条=[{role}] {content[:120]}")

    print("\n" + "=" * 70)
    print(f"最终消息数：{len(final_state['messages'])}")
    print("=" * 70)
    for m in final_state["messages"]:
        role = m.__class__.__name__
        print(f"[{role}] {m.content}")