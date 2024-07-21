import pandas as pd
from collections import Counter
import os, re, json, tiktoken, backoff, csv
from openai import OpenAI
from dotenv import load_dotenv
import time, random

load_dotenv()
client = OpenAI(
    api_key=os.environ.get(".env")
)

def separate_added_deleted(github_diff):
    diff_lines = github_diff.split('\n')

    added_lines = ""
    deleted_lines = ""

    for line in diff_lines:
        if line.startswith('+'):
            added_lines += line[0:] + '\n'
        elif line.startswith('-'):
            deleted_lines += line[0:] + '\n'
    return deleted_lines, added_lines

def read_txt(fname):
    with open(fname, "r") as fileReader:
        data = fileReader.read().splitlines()
    return data

def write_list_to_txt(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')

def is_buggy(input_string):
    yes_variants = {"YES", "yes", "Yes"}
    return input_string in yes_variants

def filter_dataset(dataset):
    filtered_dataset = []
    for item in dataset:
        if item['Root Cause'] != 'Others' or item['Root Cause'] != 'others':
            filtered_dataset.append(item)
    return filtered_dataset

def load_json(data_path):
    with open(data_path) as json_file:
        data = json.load(json_file)
    return data

def write_to_csv(data, agent_type):
    with open(f"output/{agent_type}/results.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
        write = csv.writer(file_writer)
        write.writerow(data)

# @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, model='gpt-3.5-turbo'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response

def bug_detection_agent(commit_message, deleted_lines, added_lines, exec_mode, _shot):
    if exec_mode == 'zero':
        prompt_ = f"""
        You are an AI trained to detect bugs in deep learning library backend code-base based on commit messages and code changes. 
        Given a commit message and code change, detect if it is bug or not. Please generate YES or NO.
        
        Commit message: {commit_message}
        Code change:{deleted_lines}{added_lines}
        <output>
        """
    else:
        prompt_ = f"""
        You are an AI trained to detect bugs in deep learning library backend code-base based on commit messages and code changes. 
        Given a commit message and code change, detect if it is bug or not. Please generate YES or NO.
        
        Example One:{_shot[0]['Deleted lines']}{_shot[0]['Added lines']}
        Example Two:{_shot[1]['Deleted lines']}{_shot[1]['Added lines']}
        
        Commit message: {commit_message}
        Code change:{deleted_lines}{added_lines}

        <output>
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

def pattern_extraction_agent(code_removed, code_added):
    prompt_ = f"""
    Please identify the fixing pattern in the following code change.
    Question:{code_removed}{code_added}
    <output>: 
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def path_generation_agent(bug_explanation, _shot, fixing_rules, code_snippet, exec_mode):
    if exec_mode == 'zero':
        prompt_ = f"""
        You are given bug explanation and fixing pattern for fixing a buggy code snippet. Please think 
        step by step and generate a patch to fix the bug in the code snippet. 
        Please neglect any issues related to the indentation in the code
        snippet. Fixing indentation is not the goal of this task. If you think the given pattern can be applied,
        generate the patch.
        
        Bug explanation: {bug_explanation}
        Rules for fixing the bug: {fixing_rules}
        Code snippet: {code_snippet}
        Your must generate a patch, with no additional explanation.
        <output>
        """
    else:
        prompt_ = f"""
        You are given bug explanation and fixing pattern for fixing a buggy code snippet. Please think 
        step by step and generate a patch to fix the bug in the code snippet. 
        Please neglect any issues related to the indentation in the code
        snippet. Fixing indentation is not the goal of this task. If you think the given pattern can be applied, 
        generate the patch.
        
        Example One:{_shot[0]['Deleted lines']}{_shot[0]['Added lines']}
        Example Two:{_shot[1]['Deleted lines']}{_shot[1]['Added lines']}
        
        Bug explanation: {bug_explanation}
        Rules for fixing the bug: {fixing_rules}
        Code snippet: {code_snippet}
        Your must generate a patch, with no additional explanation.
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

def tensorGuard(item, exec_mode,_shot_list, use_single_agent):
    if use_single_agent:
        patch_ = single_agent(item['Bug report'], item['Deleted lines'])
    else:
        bug_label = bug_detection_agent(item['Bug report'], item['Deleted lines'], item['Added lines'], exec_mode, _shot_list)
        if is_buggy(bug_label):
            bug_understanding = root_cause_analysis_agent(item['Bug report'])
            fix_pattern = pattern_extraction_agent(item['Deleted lines'], item['Added lines'])
            patch_ = path_generation_agent(bug_understanding, _shot_list, fix_pattern, item['Deleted lines'], exec_mode)       
            output_data = [item['Deleted lines'], item['Added lines'], patch_, bug_understanding, fix_pattern]
        else:
            output_data = [item['Deleted lines'], item['Added lines'], 'No']
    return output_data

def main():
    data_path = f"tensorflow_data.json"
    rule_path = f"data/rule_set.json"
    exec_type = ['zero']
    num_iter = 1

    rule_data = load_json(rule_path)
    data = load_json(data_path)
    
    # data = random.sample(data, 3)
    for exec_mode in exec_type:        
        output_mode = f"{exec_mode}_shot"
        if exec_mode == 'few':
            data = filter_dataset(data)
        for i in range(num_iter):
            hisotry_file = f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{i}.txt'
            if not os.path.exists(hisotry_file):
                f1 = open(hisotry_file, 'a')
            hist = read_txt(f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{i}.txt')
            for j, item in enumerate(data):
                if item['commit_link'] not in hist:
                    write_list_to_txt(item['commit_link'], f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{i}.txt')
                    for change in item['changes']:
                        for patch_ in change['patches']:
                            deleted_lines, added_lines = separate_added_deleted(patch_['content'])
                            if exec_mode == 'few':
                                _shot = [rule_data[item['Root Cause']]['example1'], rule_data[item['Root Cause']]['example2']]
                                if item['commit_link'] == _shot[0]['commit_link'] or item['commit_link'] == _shot[1]['commit_link']:
                                    print('This instance is among one of the shots, so I am skipping this one!')
                                    continue
                            else:
                                _shot = []
                            print(f"Running {exec_mode} shot: Iteration {i}: Record:{j}/{len(data)}")
                            time.sleep(2)
                            new_item = {
                                'commit_link': item['commit_link'],
                                'Bug report': item['message'],
                                'Added lines': added_lines,
                                'Deleted lines': deleted_lines
                            }
                            output_data = tensorGuard(new_item, exec_mode, _shot, use_single_agent=False)
                            output_data.insert(0, i)
                            output_data.insert(1, item['commit_link'])
                            output_data.insert(2, change['path'])
                            output_data.insert(5, item['label'])
                            write_to_csv(output_data, output_mode)
                else:
                    print('This instancee has been already processed!')

                            
if __name__ == '__main__':
    main()
