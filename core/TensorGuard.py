import pandas as pd
from collections import Counter
import os, re, json, tiktoken, backoff, csv
from openai import OpenAI
from dotenv import load_dotenv
import time, random
import tiktoken
import chromadb, sys
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
load_dotenv()
client = OpenAI(
    api_key=os.environ.get(".env")
)


class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        batch_embeddings = embedding_model.encode(input)
        return batch_embeddings.tolist()
    
def test_inference(lib, query, mode):
    embed_fn = MyEmbeddingFunction()
    client = chromadb.PersistentClient(path='./docs_db')
    collection = client.get_or_create_collection(
        name=f'basic_rag_{mode}_{lib}',
        embedding_function=embed_fn
    )

    retriever_results = collection.query(
        query_texts=[query],
        n_results=1,
    )
    return retriever_results['documents'][0]

def get_token_count(string):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(string))
    return num_tokens

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

def write_to_csv(data, output_mode, libname):
    with open(f"output/{output_mode}/{libname}_results.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
        write = csv.writer(file_writer)
        write.writerow(data)

# @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, temperature=0.2,  model='gpt-3.5-turbo'):
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response
def bug_interpretation_agent(item, exec_mode, level_mode, _shot):
    if exec_mode == 'zero':
        prompt_ = f"""
        You are an AI trained to understand the root cause of bugs in deep learning library backend code-base based on commit messages and code changes. 
        Given a commit message and code change, please explain why the code change is buggy.

        Commit message: {item['Bug report']}
        Code change:{item['Deleted lines']}{item['Added lines']} 
        <output>
        """
    else:
        prompt_ = f"""
        You are an AI trained to understand the root cause of bugs in deep learning library backend code-base based on commit messages and code changes. 
        Given a commit message and code change, please explain why the code change is buggy.

        Example One:{_shot[0]['Deleted lines']}{_shot[0]['Added lines']}
        Example Two:{_shot[1]['Deleted lines']}{_shot[1]['Added lines']}
        
        Commit message: {item['Bug report']}
        Code change:{item['Deleted lines']}{item['Added lines']} 

        <output>
        """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def bug_detection_agent(item, exec_mode, level_mode, _shot, temperature):
    if exec_mode == 'zero':
        prompt_ = f"""
        You are an AI trained to detect bugs in a deep learning library backend code-base based on commit messages and code changes. 
        Your task is to determine whether a given commit introduces a bug or not. 
        Follow the steps below to reason through the problem and arrive at a conclusion.
        
        1. Understand the commit message: Analyze the commit message to understand the context and purpose of the code change.
        Commit message: {item['Bug report']}
        
        2. Review the Code Change: Examine the deleted and added lines of code to identify the modifications made.
        Code change:{item['Deleted lines']}{item['Added lines']}
        
        3. Identify Potential Issues: Look for any missing, improper, or insufficient checkers within the code change. 
        Checkers might include error handling, input validation, boundary checks, or other safety mechanisms.
        
        4. Analyze the Impact: Consider the impact of the identified issues on the functionality and reliability of the deep learning libraries. 

        5. Make a Decision: Based on the above analysis, decide if the commit introduces a bug or not.

        6. Output the Conclusion: Generate a clear output of "YES" if the commit introduces a bug, or "NO" if it does not.
        <output>
        """
    else:
        prompt_ = f"""
        You are an AI trained to detect bugs in a deep learning library backend code-base based on commit messages and code changes. 
        Your task is to determine whether a given commit introduces a bug or not. 
        Follow the steps below to reason through the problem and arrive at a conclusion.
        
        1. Understand the commit message: Analyze the commit message to understand the context and purpose of the code change.
        Commit message: {item['Bug report']}
        
        2. Review the Code Change: Examine the deleted and added lines of code to identify the modifications made.
        Code change:{item['Deleted lines']}{item['Added lines']}
        
        3. You are also given the following examples of buggy changes:
        Example One:{_shot[0]['Deleted lines']}{_shot[0]['Added lines']}
        Example Two:{_shot[1]['Deleted lines']}{_shot[1]['Added lines']}
        
        4. Identify Potential Issues: Look for any missing, improper, or insufficient checkers within the code change. 
        Checkers might include error handling, input validation, boundary checks, or other safety mechanisms.
        
        5. Analyze the Impact: Consider the impact of the identified issues on the functionality and reliability of the deep learning libraries. 

        6. Make a Decision: Based on the above analysis, decide if the commit introduces a bug or not.

        7. Output the Conclusion: Generate a clear output of "YES" if the commit introduces a bug, or "NO" if it does not.
    
        <output>
        """
    response = completions_with_backoff(prompt_, temperature)
    return response.choices[0].message.content


def root_cause_analysis_agent(commit_message, temperature):
    prompt_ = f"""
    Please describe the root cause of the bug based on the following commit message: {commit_message}
    
    <output>
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def pattern_extraction_agent(code_removed, code_added):
    prompt_ = f"""
    Briefly summarize the core change in the following code diff and describe the general pattern
    it represents, without going into specific implementation details.
    Question:{code_removed}{code_added}
    <output>: 
    """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

def path_generation_agent(bug_explanation, _shot, code_snippet, exec_mode, level_mode, lib_name, temperature):
    #if code_snippet[0]:
    #ext_knowledge = test_inference(lib_name, bug_explanation, level_mode)
    #else:
    ext_knowledge = test_inference(lib_name, bug_explanation, level_mode)
    if exec_mode == 'zero':
        prompt_ = f"""
        You are given a bug explanation and an external knowledge for fixing a buggy code snippet. Please think 
        step by step and generate a patch to fix the bug in the code snippet. 
        Please neglect any issues related to the indentation in the code
        snippet. Fixing indentation is not the goal of this task. If you think the given pattern can be applied,
        generate the patch.

        Bug explanation: {bug_explanation}
        Code snippet: {code_snippet[0]}
        You must generate a patch, with no additional explanation.
        <output>
        """
    else:
        prompt_ = f"""
        You are given a bug explanation and an external knowledge for fixing a buggy code snippet. Please think 
        step by step and generate a patch to fix the bug in the code snippet. 
        Please neglect any issues related to the indentation in the code
        snippet. Fixing indentation is not the goal of this task. If you think the given pattern can be applied,
        generate the patch.
        
        Example One:{_shot[0]['Deleted lines']}{_shot[0]['Added lines']}
        Example Two:{_shot[1]['Deleted lines']}{_shot[1]['Added lines']}
        
        Bug explanation: {bug_explanation}
        External knowledge: {ext_knowledge}
        Code snippet: {code_snippet}
        Your must generate a patch, with no additional explanation.
        <output>
        """
    
    response = completions_with_backoff(prompt_, temperature)
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

def tensorGuard(item, exec_mode, level_mode,_shot_list, lib_name, task, temperature, use_single_agent):
    if use_single_agent:
        patch_ = single_agent(item['Bug report'], item['Deleted lines'])
    else:
        
        bug_label = bug_detection_agent(item, exec_mode, level_mode, _shot_list, temperature)
        if task == 'detection' and is_buggy(bug_label):
            output = bug_interpretation_agent(item, exec_mode, level_mode, _shot_list)
            return [item['Deleted lines'], 'Yes', output]
        elif task == 'detection' and not is_buggy(bug_label):
            return [item['Deleted lines'], 'No']
        else:
            if is_buggy(bug_label):
                bug_understanding = root_cause_analysis_agent(item['Bug report'], temperature)
                # fix_pattern = pattern_extraction_agent(item['Deleted lines'], item['Added lines'])
                if level_mode == 'patch_level':
                    patch_ = path_generation_agent(bug_understanding, _shot_list, [item['Deleted lines'], item['Added lines']], exec_mode, level_mode, lib_name, temperature)
                    output_data = ['YES', item['Deleted lines'], f"{item['Added lines']}", patch_, bug_understanding]
                else:
                    patch_ = path_generation_agent(bug_understanding, _shot_list, [item['Whole deleted'], ''], exec_mode, level_mode, lib_name, temperature)
                    output_data = ['YES', item['Deleted lines'], item['Added lines'], patch_, bug_understanding]
            else:
                output_data = ['NO', item['Deleted lines'], ]
    return output_data

def main(args):
    lib_name = args[0]
    data_path = f"data/test data/filter2/{lib_name}_test_data.json"
    rule_path = f"data/rule_set.json"
    
    if args[3] == 'zero':
        exec_type = ['zero']
    elif args[3] == 'few':
        exec_type = ['few']
    else:
        exec_type = ['zero', 'few']
    
    num_iter = args[1]
    level_mode = args[2]

    rule_data = load_json(rule_path)
    data = load_json(data_path)
    
    # data = random.sample(data, 3)
    for temp in [0.5, 0.8]:
        temperature = temp
        for exec_mode in exec_type:        
            output_mode = f"{exec_mode}_shot"
            # if exec_mode == 'few':
            #     data = filter_dataset(data)
            for i in range(num_iter):
                hisotry_file = f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{libname}_{i}_{temperature}.txt'
                if not os.path.exists(hisotry_file):
                    f1 = open(hisotry_file, 'a')
                hist = read_txt(f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{libname}_{i}_{temperature}.txt')
                for j, item in enumerate(data):
                    if item['commit_link'] not in hist:
                        write_list_to_txt(item['commit_link'], f'logs/{exec_mode}_shot/{exec_mode}_processed_commits_{libname}_{i}_{temperature}.txt')
                        for change in item['changes']:
                            if not change:
                                continue
                            if 'test' in change['path'] or 'tests' in change['path']:
                                continue
                            for k, patch in enumerate(change['patches']):
                                if not patch:
                                    continue
                                if level_mode == 'patch_level':
                                    deleted_lines, added_lines = separate_added_deleted(patch['hunk'])
                                else:
                                    deleted_lines, added_lines = separate_added_deleted(change['whole_hunk'])
                                if exec_mode == 'few':
                                    rand_num = random.randint(1, 13)
                                    _shot = [rule_data[f"entry{rand_num}"]['example1'], rule_data[f"entry{rand_num}"]['example2']]
                                    if item['commit_link'] == _shot[0]['commit_link'] or item['commit_link'] == _shot[1]['commit_link']:
                                        print('This instance is among one of the shots, so I am skipping this one!')
                                        continue
                                else:
                                    _shot = []
                                print(f"Running {exec_mode} shot: Iteration {i}::Temperature{temperature}::Commit:{j}/{len(data)}")
                                time.sleep(2)
                                
                                new_item = {
                                        'commit_link': item['commit_link'],
                                        'Bug report': item['message'],
                                        'Added lines': added_lines,
                                        'Deleted lines': deleted_lines,
                                        # 'Whole hunk': change['whole_hunk'],
                                        # 'Whole deleted': change['whole_deleted'],
                                        # 'Whole added': change['whole_added']
                                    }
                                    
                                output_data = tensorGuard(new_item, exec_mode, level_mode, _shot, lib_name, args[4], temperature, use_single_agent=False)
                                output_data.insert(0, temperature)
                                output_data.insert(1, i)
                                output_data.insert(2, item['commit_link'])
                                output_data.insert(3, exec_mode)
                                # if 'la bel' in item:
                                output_data.insert(4, change['path'])
                                output_data.insert(5, f"patch_{k}")
                                output_data.insert(6, item['label'])
                                write_to_csv(output_data, output_mode, libname)
                    else:
                        print('This instancee has been already processed!')

                            
if __name__ == '__main__':
    libname = sys.argv[1]
    num_iter = sys.argv[2]
    granularity = sys.argv[3]
    exec_mod = sys.argv[4]
    task = sys.argv[5]
    # temp = sys.argv[6]
    # libname = 'pytorch'
    # num_iter = 1
    # granularity = 'patch_level'
    # exec_mod = 'zero'
    # task = 'generation'
    args = [libname, int(num_iter), granularity, exec_mod, task]
    main(args)
