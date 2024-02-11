import json
import os
import re
import requests
import random
import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from csv import writer
from mine_comments import parse_comment
import csv
import pandas as pd
import replicate
import subprocess
import tiktoken
'''
You need to put four github access token in the following dictionaries
'''
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
FIND_BETWEEN_TF = re.compile('Current behavior?((.|\n)*?)Standalone code to reproduce the issue')
FIND_BETWEEN_TORCH = re.compile('Describe the bug((.|\n)*?)Versions')
FIND_BETWEEN_MXNET = re.compile('Description((.|\n)*?)Environment')
FIND_BETWEEN_JAX = re.compile('Description((.|\n)*?)Additional system info?')

client = OpenAI(
    api_key=os.environ.get(".env")
)
url = "https://www.llama2.ai/api"
headers = {
    'Content-Type': 'text/plain'
}
replicate = replicate.Client(api_token='r8_8taKlPQzi3Liw2179bZKZZE7pbRlfS50dSisN')

def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens



def wrap_request_and_send(prompt):
    response = replicate.run(
    "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
    input={"prompt": prompt, "max_length":20, "temperature": 0.5 , "top_p": 0.9, "repetition_penalty": 1},)
    return response

def create_prompt(post):
    prompt_ = f"""
    You are an advanced github issue bot analyzer for deep learning libraries. 
    Your duty is extract five keywords related to GPU/device/hardware errors/bugs/vulnerabilities in the given TensorFlow GitHub issue wrapped by ####.

    Github issue: ####{post}####

    REMEMBER: Do not explain the bug, just extract the keywords. 
    REMEMBER: Do not start your response with ### Sure, I can help you with that ###.
    REMEMBER: If you can not extract any related keywords, just skip generate any response.
    REMEMBER: Be creative, e.g., you can mix keywords to make them more informative. For example,
    if you extract GPU and error as separate keywords, you can generate a final response as GPU error.

    Please generate the keywords as the following format:

    Keywords: keyword1, keyword2, keyword3, keyword4, keyword5.
    """
    return prompt_

def write_csv(data, target, stage=3):
    if not os.path.exists(f'output/keywords/{target}'):
        os.makedirs(f'output/keywords/{target}')

    file_path = f"output/keywords/keywords_{target}.csv"

    with open(file_path, 'a', newline='\n', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

TOKEN1 = os.getenv("GIT_TOKEN1")
TOKEN2 = os.getenv("GIT_TOKEN2")
TOKEN3 = os.getenv("GIT_TOKEN3")
TOKEN4 = os.getenv("GIT_TOKEN4")
TARGET = os.getenv('TARGET')
PATTERN_LIST = os.getenv('PATTERN_LIST')

tokens = {
    0: TOKEN1,
    1: TOKEN2,
    2: TOKEN3,
    3: TOKEN4,
}

tokens_status = {
    TOKEN1: True,
    TOKEN2: True,
    TOKEN3: True,
    TOKEN4: True,
}


def match_label(labels):
    label_flag = False
    for l in labels:
        if "bug" in l["name"]:
            label_flag = True
    return label_flag


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session 


retries = 10
now = datetime.datetime.now()

def collect_labels(object):
    labels = []
    for l in object:
        labels.append(l['name'])
    return labels

def completions_with_backoff(prompt, model='gpt-3.5-turbo-1106'):
    response = client.chat.completions.create(
        model=model,
        max_tokens=100,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response


def get_commits(
    # keyword,
    lib,
    total_issue_counter,
    last_com,
    page_number,
    potential_commits,
    current_token,
):
    page_number += 1
    total_issue_counter += 1

    print("Current page number is: {}".format(page_number))

    headers = {
            "Authorization": f"Bearer {current_token}"
        }

    params = {
            # "q": f"{keyword} in:issue",
            "q": "in:issue is:closed",
            "per_page": 100, 
        }
    
    if page_number == 1:

        issue_link = f"https://api.github.com/repos/{lib[0]}/{lib[1]}/issues"

        response = requests_retry_session().get(
            issue_link,
            params=params,
            headers=headers,
        )
    else:
        response = requests_retry_session().get(
            last_com,
            params=params,
            headers=headers
        )
        link_ = last_com

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    first_100_commits = json.loads(response.text)

    if len(first_100_commits) == 1:
        return None
    for i, commit in enumerate(first_100_commits):

        if TARGET == 'device':
            # pattern = r"(\bCheck failed\b|\bBus error\b|\bcore dumped\b|\bAborted\b|\bAborted (core dumped)\b|\bFloating Point Exception\b|\bfloating point exception\b|\bbottleneck\b|\bpoor\b|\bbslow\b|\bweakness\b|\bdefect\b|\bbug\b|\berror\b\bbinconsistent\b|\bbincorrect\b|\bbwrong\b|\bbunexpected\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bbypass\b|\binjection\b|\boverflow\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bFPE runtime\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcorrupt\b|\bcrack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\boverflow\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bsecurity\b|\bsecurity fix\b|\bsecurity issue\b|\bsecurity problem\b|\bsnprintf\b|\bundefined behavior\b|\bunderflow\b|\buninitialize\b|\buse after free\b|\buse-after-free\b|\bviolate\b|\bviolation\b|\bvsecurity\b|\bvuln\b|\bvulnerab\b)"
            pattern = r"(\bCheck failed\b|\bBus error\b|\bcore dumped\b|\bAborted\b|\bAborted (core dumped)\b|\bFloating Point Exception\b|\bfloating point exception\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bundefined behavior\b|\bunderflow\b|\buse after free\b|\buse-after-free\b)"
        else:
            pattern = r"(FutureWarning:|Warning:|warning:)"
        title_match = False
        body_match = False
        
        if lib[0] == 'tensorflow':
            body_comp = 'Current behavior?'
        elif lib[0] == 'pytorch':
            body_comp = 'Describe the bug'
        elif lib[0] == 'apache':
            body_comp = "Description"
        else:
            body_comp = "Description"

        if isinstance(commit["body"], str) and body_comp in commit['body']:
            # if re.findall(r'(from sklearn|import tensorflow as tf|import torch|from mxnet|from mxnet.gluon)', commit['body']):
                    comment_flag = parse_comment(
                        commit["comments_url"], current_token)

                    title_match_keyword = []
                    body_match_keyword = []
                    if re.findall(pattern, commit["title"]):
                        title_match_keyword.append(re.findall(pattern, commit["title"]))
                        title_match = True
                    if re.findall(pattern, commit["body"]):
                        body_match_keyword.append(re.findall(pattern, commit["body"]))
                        body_match = True

                    if lib[0] == 'tensorflow':
                        match = FIND_BETWEEN_TF.search(commit['body'])
                    elif lib[0] == 'pytorch':
                        match = FIND_BETWEEN_TORCH.search(commit['body'])
                    elif lib[0] == 'apache':
                        match = FIND_BETWEEN_MXNET.search(commit['body'])
                    else:
                        match = FIND_BETWEEN_JAX.search(commit['body'])

                    if match:
                        current_behavior = match.group(1)
                    else:
                        continue
                    # prompt_ = create_prompt(commit["body"])
                    # token_count = get_token_count(prompt_)
                    # time.sleep(3)
                    # if token_count <= 4097:
                    #     conversations = completions_with_backoff(prompt_)
                    #     res = conversations.choices[0].message.content
                    #     write_csv([res, commit['html_url']],'device')
                    #     res = wrap_request_and_send(prompt_)
                    #     full_res = ""
                    #     for item in res:
                    #         full_res += item
                    # else:
                    #     continue
                    
                    #
                    #

                    _date = commit["created_at"]
                    sdate = _date.split("-")

                    # title_match = body_match = comment_flag = True
                    if title_match or body_match or comment_flag:
                        _date = commit["created_at"]
                        sdate = _date.split("-")
                        print(
                            "Title status: {0}, Body status: {1}, Comment status: {2}".format(
                                title_match, body_match, comment_flag
                            )
                        )

                        data =  [commit["html_url"].split('/')[-3], commit["html_url"],commit["created_at"], 'No version']
                        if not os.path.exists(f"./mining/issues/{lib[1]}"):
                            os.makedirs(f"./mining/issues/{lib[1]}")
                        with open(
                                f"./mining/issues/{lib[1]}.csv",
                                "a",
                                newline="\n",
                            ) as fd:
                                writer_object = csv.writer(fd)
                                writer_object.writerow(data
                                )

        if i == len(first_100_commits) - 1:
            last_com = response.links["next"]["url"]
            # if 'next' in response.links:
            #     last_com = response.links["next"]["url"]
            # else:
            #     return
            potential_commits = []

            get_commits(
                # keyword,
                lib,
                total_issue_counter,
                last_com,
                page_number,
                potential_commits,
                current_token,
            )


def search_comit_data(c, commit_data):
    t = []

    for item in commit_data:
        temp = item.split("/")
        t.append("/" + temp[3] + "/" + temp[4] + "/")

    r_prime = c.split("/")
    x = "/" + r_prime[3] + "/" + r_prime[4] + "/"
    if any(x in s for s in t):
        return True
    else:
        return False


def select_access_token(current_token):
    x = ""
    if all(value == False for value in tokens_status.values()):
        for k, v in tokens_status.items():
            tokens_status[k] = True

    for k, v in tokens.items():
        if tokens_status[v] != False:
            x = v
            break
    current_token = x
    return current_token


def main():
    total_issue_counter = 0
    current_token = tokens[0]
    libs = [['pytorch', 'pytorch']]
    for lib in libs:
        issue_link = f"https://api.github.com/repos/{lib[0]}/{lib[1]}/issues"
    # for keyword in PATTERN_LIST.split(','):
        print(f"I am working on {lib}")
        headers = {
            "Authorization": f"Bearer {current_token}"
        }

        params = {
            #"q": f"{keyword} in:issue is:closed",
            "q": "in:issue is:closed",
            "per_page": 100,
        }

        response = requests.get(issue_link, headers=headers, params=params)

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
            
        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
            
        response_text = json.loads(response.text)
        page_number = 0
        if len(response_text) >= 100:
            last_com = response.links["last"]["url"]
            get_commits(
                    # keyword,
                    lib,
                    total_issue_counter,
                    last_com,
                    page_number,
                    response_text,
                    current_token,
                )
        else:
            if TARGET == 'device':
                # pattern = r"(\bCheck failed\b|\bBus error\b|\bcore dumped\b|\bAborted\b|\bAborted (core dumped)\b|\bFloating Point Exception\b|\bfloating point exception\b|\bbottleneck\b|\bpoor\b|\bbslow\b|\bweakness\b|\bdefect\b|\bbug\b|\berror\b\bbinconsistent\b|\bbincorrect\b|\bbwrong\b|\bbunexpected\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bbypass\b|\binjection\b|\boverflow\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bFPE runtime\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcorrupt\b|\bcrack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\boverflow\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bsecurity\b|\bsecurity fix\b|\bsecurity issue\b|\bsecurity problem\b|\bsnprintf\b|\bundefined behavior\b|\bunderflow\b|\buninitialize\b|\buse after free\b|\buse-after-free\b|\bviolate\b|\bviolation\b|\bvsecurity\b|\bvuln\b|\bvulnerab\b)"
                pattern = r"(\bCheck failed\b|\bBus error\b|\bcore dumped\b|\bAborted\b|\bAborted (core dumped)\b|\bFloating Point Exception\b|\bfloating point exception\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bundefined behavior\b|\bunderflow\b|\buse after free\b|\buse-after-free\b)"
            else:
                pattern = r"(FutureWarning:|Warning:|warning:)"

            title_match = False
            body_match = False

            for issue in response_text:
                #if re.findall(r'(from sklearn|import tensorflow as tf|import torch|from mxnet|from mxnet.gluon)', issue['body']):
                    #comment_flag = parse_comment(issue["comments_url"], current_token)
                    
                    if re.findall(pattern, issue["title"]):
                        title_match = True
                    if re.findall(pattern, issue["body"]):
                        body_match = True

                    _date = issue["created_at"]
                    sdate = _date.split("-")
                    print(sdate[0])
                    title_match = body_match = comment_flag = True
                    if title_match or body_match or comment_flag:
                        _date = issue["created_at"]
                        sdate = _date.split("-")
                        if not os.path.exists(f"./mining/issues/{lib[1]}"):
                            os.makedirs(f"./mining/issues/{lib[1]}")
                        with open(f"./mining/issues/{lib[1]}/all_issues.csv","a",newline="\n",) as fd:
                            writer_object = csv.writer(fd)
                            writer_object.writerow([issue["html_url"].split('/')[-3],issue["html_url"],issue["created_at"],])
            potential_commits = []

if __name__ == "__main__":
    main()