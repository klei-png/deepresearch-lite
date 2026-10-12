from langgraph.types import Command, interrupt

from ..state import ReportState, SectionPlan

def approve_plan_node(state: ReportState) -> Command:
    """纯人工节点，只负责暂停与接受修改"""
    decision = interrupt({
        "stage":"plan",
        "message":"请确认或编辑报告提纲",
        "plan":[s.model_dump() for s in state["plan"]]
    })

    if decision.get("action") == "edit":
        new_plan = [SectionPlan(**s) for s in decision["plan"]]
        return Command(update={"plan":new_plan},goto="research")
    if decision.get("action") == "reject":
        return Command(update={"plan":[]},goto="__end__")
    return Command(goto="research")
