import os
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("LANGSMITH_TRACING","").lower()=="true":
    os.environ.setdefault(
        "LANGSMITH_PROJECT","deepresearch-lite" )