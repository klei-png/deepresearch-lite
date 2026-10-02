from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from openai import max_retries

from .configuration import Configuration

@lru_cache(maxsize=None)
def get_model(role: str, model_string: str, temperature: float = 0.0) -> BaseChatModel:
    return init_chat_model(role, model_string, temperature,timeout=60, max_retries=2)

def model_for(role: str, config: RunnableConfig | None = None, **kwargs) -> BaseChatModel:
    cfg = Configuration.from_runnable_config(config)
    name = getattr(cfg, f"{role}_model")
    return get_model(role, name, **kwargs)