
import json
import pandas as pd
from collections import Counter
import json
import os
import tiktoken
import openai
from openai import OpenAI
import backoff
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ.get(".env")
)

# @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, model='gpt-3.5-turbo'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response

rules_path = f"data/commit_stat_data.json"


def description_observer(commit_msg):
    prompt_ = f"""
    Please read the following commit message from a bug fixing commit that fixes a checker bug and understand what is the root cause of the bug:
    Commit message: {commit_msg}
    Constraint: Do not explain the fixing pattern, only understand the root cause.
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def code_observer(root_cause,deleted_code):
    prompt_ = f"""
    You are given deleted lines in a code change and the root cause of the bug. Please understand what the developer has done:
    Deleted code lines: {deleted_code}
    Root cause: {root_cause}
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def reasoning(root_cause, code_understanding, deleted_lines):
    prompt_ = f"""
    Please read the root cause of the bug, the code explanation, deleted lines in the code change and 
    think step by step and generate a steps to patch the bug.

    Root cause: {root_cause}
    Code explanation: {code_understanding}
    Deleted lines: {deleted_lines}

    Do not generate steps for testing and commiting bug. Only production code.
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content


def patch_generator(steps):
    prompt_ = f"""
    Please read the steps for patch generation and generate code patch that fixes the bug:
    Steps for patch generation: {steps}
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content


with open(rules_path) as json_file:
    data = json.load(json_file)
    for j, item in enumerate(data):
        if item['Changed lines'] <= 15:
            print(f"Record {j}/{len(data)}")
            a1 = description_observer(item['Commit message'])
            a2 = code_observer(a1, item['Deleted code'])
            a3 = reasoning(a1, a2, item['Deleted code'])
            output = patch_generator(a3)
            output_split = output.split('\n')
            print('')