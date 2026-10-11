import chunk
import json
import requests

from typing import Annotated
from bs4 import BeautifulSoup
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from ddgs import DDGS
from langchain_community.document_loaders import DirectoryLoader,TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore

from .configuration import Configuration

@tool
def web_search(
        query:str,
        max_results:Annotated[int,"返回条数，建议3-5"] = 5
) -> str:
    """
    在互联网上检索信息。
    使用场景：需要事实、数据、时间线、公司/产品信息时。
    query 用**陈述句或关键词组合**，不要写成问句，不要加"请"等礼貌用语。
    返回 JSON 字符串，包含 title / url / snippet 三个字段。
    """
    cfg = Configuration.from_runnable_config(None)
    if cfg.search_api == "mock":
        return json.dumps([{"title":"示例","url":"https://example.com",
                            "snippet":"..."}],ensure_ascii=False)
    if cfg.search_api == "tavily":
        return str(TavilySearchResults(query,max_results).invoke({"query":query}))
    try:
        ddgs = DDGS(timeout=30,proxy="http://127.0.0.1:7897")
        hits = list(ddgs.text(query,max_results=max_results))
    except Exception as e:
        return json.dumps([],ensure_ascii=False)
    return json.dumps(
        [{"title": h["title"], "url": h["href"], "snippet": h["body"]} for h in hits],
        ensure_ascii=False,
    )

def _to_text(html:str) -> str:
    """将html转换成纯文本"""
    return BeautifulSoup(html,"html.parser").get_text(" ",strip=True)

@tool
def fetch_url(url: str) -> str:
    """抓取网页正文。url必须来自web_search的结果，不要自己编造。"""
    try:
        headers = {"User-Agent":"Mozilla/5.0"}
        r = requests.get(url,timeout=10,headers=headers)
        if r.status_code != 200:
            return f"错误：HTTP{r.status_code}。请换一个来源重试。"
        return _to_text(r.text)[:8000]
    except Exception as e:
        return f"错误：{type(e).__name__}。请换一个来源重试。"

_emb = OpenAIEmbeddings(model="text-embedding-3-small")
_kb = None
def build_kb(data_dir: str = "data", persist: str | None = "storage/faiss") -> InMemoryVectorStore:
    docs = DirectoryLoader(data_dir, glob="**/*.md",loader_cls=TextLoader,loader_kwargs={"encoding":"utf-8"}).load()
    splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    vs = FAISS.from_documents(chunks, _emb)
    if persist:
        vs.save_local(persist)
    return vs
@tool
def search_knowledge(query: str) -> str:
    """
    在公式内部知识库中检索。用于回答制度、产品、历史文档相关问题。
    query写成包含关键名词的陈述句；找不到就换同义词再试，最多3次。
    """
    global _kb
    if _kb is None:
        _kb = build_kb()
    docs = _kb.similarity_search(query, k=4)
    if not docs:
        return "未检索到相关内容。请换用更概括的说法重试。"
    return "/n/n".join(
        f"[{i+1}] 来源：{d.metadata.get('source')}\n{d.page_content}"
        for i,d in enumerate(docs)
    )