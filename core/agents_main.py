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

def description_observer(commit_msg):
    prompt_ = f"""
    Please read the following bug report from a bug fixing commit that fixes a validation/checker bug and understand what is the root cause of the bug:
    Bug report: {commit_msg}
    Constraint: Do not explain the fixing pattern, only understand the root cause.
    <answer start>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def code_observer(root_cause,deleted_code):
    prompt_ = f"""
    You are given a buggy code and the root cause of the bug. Please try to think step by step and generate a steps to patch the bug:
    Buggy code: {deleted_code}
    Root cause: {root_cause}
    Do not generate steps for testing and commiting bug. Only production code.
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

def main():
    use_base = True
    data_path = f"data/subject_data/data_2.json"
    # for root, dirs, files in os.walk(r'data'):
    #     for file in files:
    #         if re.findall(r'(data\_)', file):
    with open(data_path) as json_file:
                    data = json.load(json_file)
                    for j, item in enumerate(data):
                        print(f"Record {j}/{len(data)}")
                        if use_base:
                            output = global_agent(item['Bug report'], item['Deleted lines'])
                        else:
                            a1 = description_observer(item['Bug report'])
                            a2 = code_observer(a1, item['Deleted lines'])
                            # a3 = reasoning(a1, a2, item['Deleted lines'])
                            output = patch_generator(a2, item['Deleted lines'])

                        data = [
                            item['Commit Link'],
                            output
                        ]
                        with open(f"output/output_2.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
                            write = csv.writer(file_writer)
                            write.writerow(data)
                        
if __name__ == '__main__':
    main()
