import pandas as pd
from collections import Counter
import os, re, json, tiktoken, backoff, csv
from openai import OpenAI
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

def code_observer(code_removed, code_added):
    prompt_ = f"""
    Please identify the rules for fixing the validation/checker bug in the following code change:
    Question:{code_removed}{code_added}
    <output>: 
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def bugReport_observer(commit_message):
    prompt_ = f"""
    Please describe the bug based on the following commit message: {commit_message}
    <output>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def path_generator(bug_explanation, fixing_rules, code_snippet):
    prompt_ = f"""
    You are given bug explanation and rules for fixing the bug. Then, think 
    step by step and generate a patch for the code snippet. 
    Please ignore any indentation problems in the code
    snippet. Fixing indentation is not the goal of this task. If the
    pattern can be applied, generate the patch.

    Bug explanation: {bug_explanation}
    Rules for fixing the bug: {fixing_rules}
    Code snippet: {code_snippet}
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content


def patch_generator(steps, deleted_code):
    prompt_ = f"""
    Please read the step-by-step guide and buggy code to generate code patch that fixes the bug:
    Steps for patch generation: {steps}
    Deleted lines: {deleted_code}
    ATTENTION: Do not generate buggy code in the patch, only generate fixed code.
    ATTENTION: Do not generate comments that explain the generated code.
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content


def global_agent(commit_msg, deleted_code):
    prompt_ = f"""
    Please read the following bug report and buggy code from a bug fixing commit that fixes a validation/checker bug:
    Bug report: {commit_msg}
    Buggy code: {deleted_code}
    Please try to think step by step and generate code that patches the bug. 

    Constraint: Do not generate buggy code in the patch, only generate fixed code.
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content
# Please combine the knowledge you gained from the commit message and the code change and describe how to fix the code.
def main():
    use_base = False
    data_path = f"data/data_1.json"
    with open(data_path) as json_file:
        data = json.load(json_file)
        for j, item in enumerate(data):
            print(f"Record {j}/{len(data)}")
        if use_base:
            output = global_agent(item['Bug report'], item['Deleted lines'])
        else:
            a1 = code_observer(item['Deleted lines'], item['Added lines'])
            a2 = bugReport_observer(item['Bug report'])
            patch_ = path_generator(a1, a2)

        data = [item['Commit Link'], patch_]
        with open(f"output/output_2.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
            write = csv.writer(file_writer)
            write.writerow(data)
                        
if __name__ == '__main__':
    main()
