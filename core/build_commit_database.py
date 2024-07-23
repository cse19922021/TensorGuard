import git
import os
import json
from unidiff import PatchSet
import pandas as pd
from pydriller import Repository
import pandas as pd
from collections import Counter
import os, re, json, tiktoken, backoff, csv
from openai import OpenAI
from dotenv import load_dotenv
import time, random
from sklearn.model_selection import train_test_split

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

def write_to_csv(data, libname, mode):
    with open(f"{libname}_{mode}_statistics.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
        write = csv.writer(file_writer)
        write.writerow(data)
        
def is_buggy(input_string):
    yes_variants = {"YES", "yes", "Yes"}
    return input_string in yes_variants

def bug_detection_agent(commit_message):
    prompt_ = f"""
        You are an AI trained to detect bugs in deep learning library backend code-base based on commit messages. 
        Given a commit message, detect if it is bug or not. Please generate YES or NO.
        
        Commit message: {commit_message}
        <output>
        """
    response = completions_with_backoff(prompt_)
    return response.choices[0].message.content

# @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, model='gpt-4-turbo'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response


def is_valid_file_type(file_path):
    valid_extensions = ('.py', '.cc', '.cpp', '.cu', '.h', '.hpp', '.sh', '.cmake')
    return file_path.endswith(valid_extensions)

def get_commit_with_changes(repo_path, commit_hash, libname, idx, row):
    repo = git.Repo(repo_path)
    commit = repo.commit(commit_hash)
    parent_commit = commit.parents[0] if commit.parents else None
    # time.sleep(2)
    # response = bug_detection_agent(commit.message.strip())
    
    output_list = [libname, f"https://github.com/{libname}/{libname}/commit/{commit_hash}"]
    
    commit_info = {
            "Id": idx, 
            "commit_link": f"https://github.com/{libname}/{libname}/commit/{commit_hash}", 
            "date": commit.committed_datetime.isoformat(),
            "message": commit.message.strip(),
            "label": row['Label'],
            "changes": []
        }

    if parent_commit and row['Verify'] == 1:
        diff = repo.git.diff(parent_commit, commit, ignore_blank_lines=True, ignore_space_at_eol=True)
        patch_set = PatchSet(diff)
        if len(patch_set.modified_files) < 10:
            output_list.append(len(patch_set.modified_files))
            num_hunks = 0
            total_loc = 0

            for patched_file in patch_set:
                file_path = patched_file.path
                # if not is_valid_file_type(file_path):
                #     continue 
                
                file_name = os.path.basename(file_path)

                    # if 'test' in file_name or 'tests' in file_name:
                    #     continue            
                    
                patches = []
                whole_deleted = ""
                whole_deleted_added = ""  
                for hunk in patched_file:
                    num_hunks = num_hunks + 1
                    loc_changed = hunk.added + hunk.removed
                    total_loc = total_loc + loc_changed
                    deleted_lines, added_lines = separate_added_deleted(str(hunk))
                    # if loc_changed <= 10:
                    patch = {
                                "old_start": hunk.source_start,
                                "old_length": hunk.source_length,
                                "new_start": hunk.target_start,
                                "new_length": hunk.target_length,
                                "hunk": str(hunk)
                            }
                    whole_deleted = whole_deleted + deleted_lines
                    whole_deleted_added = whole_deleted_added + str(hunk)
                    patches.append(patch)
                            


                if patches:
                    file_change = {
                        "name": file_name,
                        "path": file_path,
                        "patches": patches,
                        "whole_deleted": whole_deleted,
                        "whole_hunk":  whole_deleted_added}
                    commit_info["changes"].append(file_change)

            output_list.append(num_hunks)
            output_list.append(total_loc)
            output_list.append(row['Label'])

    return commit_info, output_list

libname = 'PyTorch'
repo_path = f"ml_repos/{libname.lower()}/{libname.lower()}"
data = pd.read_csv(f'data/{libname}_verified.csv')
train_df, test_df = train_test_split(data, test_size=0.3, random_state=42)
data_dict = {
    'train_data': train_df,
    'test_data': test_df
}

for k, v in data_dict.items():
    for idx, row in v.iterrows():
        commit_hash = row['Commit Link'].split('/')[-1]
        print(f"Processed {commit_hash}::{idx}/{len(v)}")
        commit_data, output_list = get_commit_with_changes(repo_path, commit_hash, libname, idx, row)

        if commit_data['changes']:
            write_to_csv(output_list , libname, k)
            with open(f'{libname}_{k}.json', 'a') as f:
                json.dump(commit_data, f, indent=4)
                f.write(',')
                f.write('\n')