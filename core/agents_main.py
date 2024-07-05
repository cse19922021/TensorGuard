import pandas as pd
from collections import Counter
import os, re, json, tiktoken, backoff, csv
from openai import OpenAI
from dotenv import load_dotenv
from transformers import RobertaTokenizer, RobertaModel
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
client = OpenAI(
    api_key=os.environ.get(".env")
)

tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")

def write_to_csv(data, agent_type):
    with open(f"output/output_{agent_type}.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
        write = csv.writer(file_writer)
        write.writerow(data)

def embed_code(input_code):
    inputs = tokenizer(input_code, return_tensors="pt", max_length=512, truncation=True, padding="max_length")
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).detach().numpy()
    return embeddings
    
def calculate_similarity(src_, dest_):
    return cosine_similarity(src_, dest_)

# @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, model='gpt-3.5-turbo'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response

def pattern_extraction_agent(code_removed, code_added):
    prompt_ = f"""
    Please identify the common fixing pattern in the following code change.
    Question:{code_removed}{code_added}
    <output>: 
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def root_cause_analysis_agent(commit_message):
    prompt_ = f"""
    Please describe the root cause of the bug based on the following commit message: {commit_message}
    <output>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def path_generation_agent(bug_explanation, fixing_rules, code_snippet):
    prompt_ = f"""
    You are given bug explanation and fixing pattern for fixing the bug. Then, think 
    step by step and generate a patch for the code snippet. 
    Please ignore any indentation problems in the code
    snippet. Fixing indentation is not the goal of this task. If the
    pattern can be applied, generate the patch.

    Bug explanation: {bug_explanation}
    Rules for fixing the bug: {fixing_rules}
    Code snippet: {code_snippet}
    <output>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content


def single_agent(commit_msg, deleted_code):
    prompt_ = f"""
    Please read the following commit message and buggy code:
    Commit message: {commit_msg}
    Buggy code: {deleted_code}
    Then, think step by step and generate a patch for the code snippet. 
    Please ignore any indentation problems in the code
    snippet. Fixing indentation is not the goal of this task. If the
    pattern can be applied, generate the patch.
    <output>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def fix_checker_bug(item, use_single_agent):
    if use_single_agent:
        patch_ = single_agent(item['Bug report'], item['Deleted lines'])
        #result = codebleu(item['Added lines'], patch_)
        output_data = [item['Commit Link'], item['Added lines'], patch_]
    else:
        bug_understanding = root_cause_analysis_agent(item['Bug report'])
        fix_pattern = pattern_extraction_agent(item['Deleted lines'], item['Added lines'])
        patch_ = path_generation_agent(bug_understanding, fix_pattern, item['Deleted lines'])       
        #result = codebleu(item['Added lines'], patch_)
        output_data = [item['Commit Link'], item['Added lines'], patch_, fix_pattern]
    return output_data

    # print(f"The similarity score for records{j}::{calculate_similarity(actual_fix, patch_embed)}")

def main():
    data_path = f"data/data_1.json"
    with open(data_path) as json_file:
        data = json.load(json_file)
        for j, item in enumerate(data):
            print(f"Processing record:{j}/{len(data)}")
            output_data = fix_checker_bug(item, use_single_agent=True)
            write_to_csv(output_data, output_name = 'multi')

                            
if __name__ == '__main__':
    main()
