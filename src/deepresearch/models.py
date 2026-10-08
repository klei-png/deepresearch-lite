import os
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .configuration import Configuration

@lru_cache(maxsize=None)
def get_model(role: str, model_string: str, temperature: float = 0.0) -> BaseChatModel:
    # return init_chat_model(model_string,temperature=temperature,timeout=60, max_retries=2)
    return ChatOpenAI(
        model=model_string,
        api_key=os.environ.get("QIANWEN_API_KEY"),
        base_url=os.environ.get("QIANWEN_API_BASE"),
        temperature=temperature,
        timeout=180,
        max_retries=2,
        extra_body={"enable_thinking":False}
    )

def model_for(role: str, config: RunnableConfig | None = None, **kwargs) -> BaseChatModel:
    cfg = Configuration.from_runnable_config(config)
    name = getattr(cfg, f"{role}_model")
    return get_model(role, name, **kwargs)