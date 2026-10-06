from itertools import chain

from langchain_core.prompts import ChatPromptTemplate
from .configuration import Configuration
from .models import model_for
from .prompts import REPORT_SYSTEM,REPORT_USER
from schemas import Report

def run(topic: str,config: dict|None = None) -> Report:
    cfg = Configuration.from_runnable_config(config)

    prompt = ChatPromptTemplate.from_messages([
        ("system",REPORT_SYSTEM),
        ("human",REPORT_USER)
    ])

    chain = prompt | model_for("writer",config).with_structured_output(Report)

    return chain.invoke({
        "topic": topic,
        "n_sections": cfg.max_sections(),
        "audience": "技术决策者",
        "extra": "重点关注2025年后的进展",
    })

def run_stream(topic: str,config: dict|None = None):
    cfg = Configuration.from_runnable_config(config)
    prompt = ChatPromptTemplate.from_messages([("system",REPORT_SYSTEM),("human",REPORT_USER)])
    chain = prompt | model_for("writer",config).with_structured_output(Report)
    for chunk in chain.stream({
        "topic": topic,
        "n_sections": cfg.max_sections,
        "audience": "技术决策者",
        "extra":"",
    }):
        print(chunk,end="",flush=True)

if __name__ == "__main__":
    r = run("大模型推理成本下降的趋势与影响")
    print(r.title)
    print(r.abstract)
    for s in r.sections:
        print(f"\n##{s.title}\n{s.content}")
    print("\n待验证：",r.open_questions)

    resp = model_for("writer").invoke([{"role":"user","content":"hi"}])
    print(resp.usage_metadata)

