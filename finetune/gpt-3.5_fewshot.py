import pandas as pd
from collections import Counter
import json
import os
import tiktoken
import openai
import backoff
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")


trian = openai.File.create(
    file=open("fine-tuning-Qna.jsonl", "rb"),
    purpose="fine-tune"
)
print(trian)