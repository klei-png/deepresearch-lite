from os import name
from platform import system

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph_supervisor import create_supervisor

from ..configuration import Configuration
from ..models import model_for
from ..nodes.write import write_node
from ..tools import web_search,search_knowledge

def build_member(name:str,system_prompt:str,tools,config=None):
    """团队成员：每个都是独立的create_agent，有自己的提示词和工具"""

    agent = create_agent(
        model = model_for("research",config),
        tools = tools,
        system_prompt = system_prompt,
        name = name
    )

    # 包一层：打印"何时被调用、输入什么、输出什么"
    def wrapped_member(state):
        print(f"\n{'=' * 60}")
        print(f"[成员被调用] {name}")
        print(f"{'=' * 60}")

        # 打印输入（最后一条消息）
        msgs = state.get("messages", [])
        if msgs:
            last = msgs[-1]
            role = last.__class__.__name__
            content = getattr(last, "content", str(last))
            print(f"  输入[{role}]：{content[:150]}")

        # 调原始 agent
        result = agent.invoke(state)

        # 打印输出（最后一条消息）
        out_msgs = result.get("messages", [])
        if out_msgs:
            last_out = out_msgs[-1]
            role = last_out.__class__.__name__
            content = getattr(last_out, "content", str(last_out))
            print(f"  输出[{role}]：{content[:200]}")

        print(f"[成员完成] {name}")
        return result

    return wrapped_member

def build_supervisor(config=None):
    cfg = Configuration.from_runnable_config(config)

    tech_researcher = build_member(
        "tech_researcher",
        "你是技术调研员，关注技术原理、架构与最新进展，输出带来源的事实要点。",
        [web_search],
        config
    )

    market_researcher = build_member(
        "market_researcher",
        "你是市场分析师，关注市场规模、玩家、商业模式与成本，输出带数字的事实要点。",
        [web_search],
        config
    )

    kb_researcher = build_member(
        "kb_researcher",
        "你是内部知识库检索员，优先使用search_knowledge 回答公司已有资料相关问题。",
        [search_knowledge],
        config
    )

    writer = build_member(
        "writer",
        "你是报告撰写者，把各方要点整合成结构清晰的Markdown报告，标注来源，禁止编造。",
        [],
        config
    )

    workflow = create_supervisor(
        [tech_researcher,market_researcher,kb_researcher,writer],
        model = model_for("planner",config),
        prompt = (
            "你是研究团队的主管。\n"
            "流程：先派 1~2 个研究员并行调研 → 收集要点 → 交给 writer 成稿。\n"
            "规则：不要自己做调研；每次只派一个成员；成员返回后判断是否还需要补充调研；\n"
            "所有事实必须有来源，没有来源的要求重新调研。\n"
            "报告章节不超过 {max_sections} 节。"
        ),
        output_mode="last_message",
        supervisor_name="research_supervisor",
    )
    return workflow.compile()
