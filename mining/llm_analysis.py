import pandas as pd
from csv import writer
import os, subprocess, re, csv
from git import Repo
from datetime import datetime
from datetime import datetime, timezone
from openai import OpenAI
import backoff, time
import openai
import tiktoken
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ.get(".env")
)

@backoff.on_exception(backoff.expo, openai.RateLimitError)
def completions_with_backoff(prompt, model='gpt-4-0125-preview'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response

def stage_1_prompting(item, libname):
    prompt_ = f"""
    You are a chatbot responsible for classifying a commit message that fixing bugs in {libname} backend implementation.
    Your task is to classify if the commit is fixing an improper/missing validation/checker bug. Please generate binary response, i.e., yes or no.

    Here is the commit message:
    Commit message: {item}

    Result: <your response>

    """

    return prompt_

def stage_2_prompting(item, libname):
    prompt_ = f"""
    You are an advanced chatbot responsible for analyzing a commit message that fixing bugs in {libname} backend implementation.
    Your task is to perform analysis on the bug fixing commit that fixing an improper/missing validation/checker bug.

    Here is the commit message:
    Commit message: {item}
    
    Before you do analysis, please make sure that the commit message is really a bug related to missing/improper/redundant validation/checker bug. If it is not, do not analyze.
    
    Your analysis should contain the following factors:

    Root cause: <What is the root cause of the bug>
    Impact of the bug: <what is the impact of the bug>
    Fixing pattern: <how the bug is fixed>
    Fixing element: <what element is the developer fixing?>

    STRONG CONSTRAINT: Do not generate long description, only generate high level titles.
    STRONG CONSTRAINT: If you do not know the answer, generate UNKNOWN for each factor. 
    Result: <your response>

    """

    return prompt_

def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens

def write_list_to_txt4(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')

def save_commit(data, lib):
    if not os.path.exists(f'data/commits/{lib}/'):
        os.makedirs(f'data/commits/{lib}/')
    with open(f"data/commits/{lib}/{lib}.csv","a", newline="\n",) as fd:
        writer_object = csv.writer(fd)
        writer_object.writerow(data)

def read_txt(fname):
    with open(fname, "r") as fileReader:
        data = fileReader.read()
    return data

def analysis():
    data = pd.read_csv('mining/commits/pytorch/pytorch.csv')
    THIS_PROJECT = os.getcwd()
    REPO_LIST = ["https://github.com/pytorch/pytorch"]
    r_prime = REPO_LIST[0].split("/")
    repo = Repo(THIS_PROJECT + "/ml_repos_cloned/" + r_prime[3] + "/" + r_prime[4])

    hisotry_file = f'logs/{r_prime[3]}_parsed_commits.txt'

    if not os.path.exists(hisotry_file):
        f1 = open(hisotry_file, 'a')

    hist = read_txt(f'logs/{r_prime[3]}_parsed_commits.txt')

    for idx, row in data.iterrows():
        if row.iloc[2] == 2:
            com = repo.commit(row.iloc[0].split('/')[-1])
            if com.hexsha not in hist:
                print("Analyzed commits: {}/{}".format(idx, len(data)))
                write_list_to_txt4(com.hexsha, f'logs/{r_prime[3]}_parsed_commits.txt')
                try:
                    prompt_ = stage_2_prompting(com.message, r_prime[3])
                    t_count = get_token_count(prompt_)
                    if t_count <= 4097:
                        time.sleep(3)
                        conversations = completions_with_backoff(prompt_)
                        decision = conversations.choices[0].message.content
                        decision_split = decision.split('\n')
                        filtered_list = list(filter(None, decision_split))
                    
                    commit_link = REPO_LIST[0] + "/commit/" + com.hexsha
                    commit_date = com.committed_date
                    dt_object = datetime.fromtimestamp(commit_date)
                    commit_date = dt_object.replace(tzinfo=timezone.utc)
                    data = [commit_link, commit_date.strftime("%Y-%m-%d %H:%M:%S"), filtered_list[0], filtered_list[1], filtered_list[2], filtered_list[3]]
                    save_commit(data, r_prime[3])
                except Exception as e:
                    print(e)

if __name__ == '__main__':
    analysis()