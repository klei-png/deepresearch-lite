import os
from dataclasses import dataclass, field
from typing import get_type_hints

from langchain_core.runnables import RunnableConfig,ensure_config
from numpy.distutils.misc_util import Configuration


@dataclass(kw_only=True)
class Configuration:
    """全部可调参数。优先级：configurable > 环境变量 > 默认值"""
    planner_model: str = "glm-4.7-flash"
    research_model: str = "glm-4.7-flash"
    writer_model: str = "glm-4.7-flash"
    reviewer_model: str = "glm-4.7-flash"
    compression_model: str = "glm-4.7-flash"

    #----行为参数----
    max_sections: int = 5   #最多报告几节
    max_queries_per_section: int = 3
    max_search_results: int = 2
    search_api: str = "duckduckgo"
    enable_hitl: bool = True    #大纲是否人工审批

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig | None = None) -> "Configuration":
        cfg = ensure_config(config)
        configurable = cfg.get("configurable",{})
        hints = get_type_hints(cls)
        values:dict = {}
        for f in field(cls):
            if f.name in configurable and configurable[f.name] is not None:
                raw = configurable[f.name]
            elif os.environ.get(f.name.upper()):
                raw = os.environ[f.name.upper()]
            else:
                continue
            values[f.name] = _coerce(raw, hints.get(f.name,str))
        return cls(**{k: v for k, v in values.items()})

def _coerce(raw,typ):
    if typ is bool and isinstance(raw,str):
        return raw.strip().lower() in ("1","true","yes","on")
    if typ is int and isinstance(raw,str):
        return int(raw)
    return raw