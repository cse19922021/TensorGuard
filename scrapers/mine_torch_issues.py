import json
import re
import os
import re
import subprocess
import requests
import random
import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from csv import writer
from pydriller import Repository

# (0, nimashiri2012@gmail.com, 1, cse19922021@gmail.com, 2, nshiri@yorku.ca, 3, nshiri@cse.yorku.ca)
tokens = {0: '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', 1: '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',
          2: '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', 3: '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'}

tokens_status = {'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': True, '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': True,
                 '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': True, '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': True}


def decompose_code_linens(splitted_lines):
    super_temp = []
    j = 0
    indices = []
    while j < len(splitted_lines):
        if '\n' in splitted_lines[j]:
            indices.append(j)
        j += 1

    if bool(indices) == False:
        return splitted_lines

    if len(indices) == 1:
        for i, item in enumerate(splitted_lines):
            if i != 0:
                super_temp.append(item)
        super_temp = [super_temp]
    else:
        i = 0
        j = 1
        while True:
            temp = []
            for row in range(indices[i], indices[j]):
                temp.append(splitted_lines[row+1])
            super_temp.append(temp)
            if j == len(indices)-1:
                temp = []
                for row in range(indices[j], len(splitted_lines)):
                    temp.append(splitted_lines[row])
                super_temp.append(temp)
                break
            i += 1
            j += 1

    return super_temp


def read_txt(fname):
    with open(fname, 'r') as fileReader:
        data = fileReader.read().splitlines()
    return data


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
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


retries = 10
now = datetime.datetime.now()


def search_comit_data(c, commit_data):
    t = []

    for item in commit_data:
        temp = item.split('/')
        t.append('/' + temp[3] + '/' + temp[4] + '/')

    r_prime = c.split('/')
    x = '/' + r_prime[3] + '/' + r_prime[4] + '/'
    if any(x in s for s in t):
        return True
    else:
        return False


def select_access_token(current_token):
    x = ''
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

    current_token = tokens[0]
    torch_issues = read_txt('data/torch_issues.txt')

    issue_flag = False
    commit_flag = False
    pull_flag = False

    for item in torch_issues:
        sha_str = item.split('/')[-1]
        if 'commit' in item:
            commit_base_str = "https://api.github.com/repos/pytorch/pytorch"
            branchLink = f"{commit_base_str}/commits/{sha_str}"
            commit_flag = True
        else:
            issue_base_str = "https://api.github.com/repos/pytorch/pytorch"
            branchLink = f"{issue_base_str}/issues/{sha_str}"
            issue_flag = True

        x = []

        potential_commits = []

        response = requests_retry_session().get(
            branchLink, headers={'Authorization': 'token {}'.format(current_token)})

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={'Authorization': 'token {}'.format(current_token)})

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={'Authorization': 'token {}'.format(current_token)})

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={'Authorization': 'token {}'.format(current_token)})

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={'Authorization': 'token {}'.format(current_token)})

        data_ = json.loads(response.text)

        if issue_flag:
            issue_title_ = data_['title']

            if re.findall(r'Summary((.|\n)*?)Segmentation fault in the CPU 2D kernel', data_['body']):
                issue_description = re.findall(
                    r'Summary((.|\n)*?)Segmentation fault in the CPU 2D kernel', data_['body'])[0][0]

            if re.findall(r'Bug((.|\n)*?)To Reproduce', data_['body']):
                issue_description = re.findall(
                    r'Bug((.|\n)*?)To Reproduce', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)code', data_['body']):
                issue_description = re.findall(
                    r'Describe the bug((.|\n)*?)code', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)Code example', data_['body']):
                issue_description = re.findall(
                    r'Describe the bug((.|\n)*?)Code example', data_['body'])[0][0]

            if re.findall(r'Problem((.|\n)*?)torch 1.11 and before', data_['body']):
                issue_description = re.findall(
                    r'Problem((.|\n)*?)torch 1.11 and before', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)Which results in:', data_['body']):
                issue_description = re.findall(
                    r'Describe the bug((.|\n)*?)Which results in:', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)Minimal example', data_['body']):
                issue_description = re.findall(
                    r'Describe the bug((.|\n)*?)Minimal example', data_['body'])[0][0]

            if re.findall(r'Bug((.|\n)*?)To clarify, the issue occurs when I do:', data_['body']):
                issue_description = re.findall(
                    r'Bug((.|\n)*?)To clarify, the issue occurs when I do:', data_['body'])[0][0]

            if re.findall(r'Bug((.|\n)*?)Expected behavior', data_['body']):
                issue_description = re.findall(
                    r'Bug((.|\n)*?)Expected behavior', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)Example to reproduce', data_['body']):
                issue_description = re.findall(
                    r'Describe the bug((.|\n)*?)Example to reproduce', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)To Reproduce', data_['body']):
                issue_description = re.findall(r'Describe the bug((.|\n)*?)To Reproduce',
                                               data_['body'])[0][0]

            if re.findall(r'description((.|\n)*)', data_['body']):
                issue_description = re.findall(
                    r'description((.|\n)*)', data_['body'])[0][0]

            if re.findall(r'Segmentation fault in the CPU 2D kernel((.|\n)*?)The CUDA kernels \(both 2D and 3D\)', data_['body']):
                issue_code = re.findall(
                    r'Segmentation fault in the CPU 2D kernel((.|\n)*?)The CUDA kernels \(both 2D and 3D\)', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)Environment', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)Environment', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)stdout:', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)stdout:', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)Expected behavior', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)Expected behavior', data_['body'])[0][0]

            if re.findall(r'Example to reproduce((.|\n)*?)Result', data_['body']):
                issue_code = re.findall(
                    r'Example to reproduce((.|\n)*?)Result', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)Output', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)Output', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)Error:', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)Error:', data_['body'])[0][0]

            if re.findall(r'torch 1.11 and before((.|\n)*?)torch 1.12:', data_['body']):
                issue_code = re.findall(
                    r'torch 1.11 and before((.|\n)*?)torch 1.12:', data_['body'])[0][0]

            if re.findall(r'Minimal example((.|\n)*?)leads to the following CLI output under torch 1.11.0, tested on two different systems:', data_['body']):
                issue_code = re.findall(
                    r'Minimal example((.|\n)*?)leads to the following CLI output under torch 1.11.0, tested on two different systems:', data_['body'])[0][0]

            if re.findall(r'Describe the bug((.|\n)*?)Versions', data_['body']):
                issue_code = re.findall(
                    r'Describe the bug((.|\n)*?)Versions', data_['body'])[0][0]

            if re.findall(r'Code((.|\n)*?)output', data_['body']):
                issue_code = re.findall(
                    r'Code((.|\n)*?)output', data_['body'])[0][0]

            if re.findall(r'Code example((.|\n)*?)By using this script,', data_['body']):
                issue_code = re.findall(
                    r'Code example((.|\n)*?)By using this script,', data_['body'])[0][0]

            if re.findall(r'To clarify, the issue occurs when I do:((.|\n)*?)but not for', data_['body']):
                issue_code = re.findall(
                    r'To clarify, the issue occurs when I do:((.|\n)*?)but not for', data_['body'])[0][0]

            if re.findall(r'To Reproduce((.|\n)*?)Additional context', data_['body']):
                issue_code = re.findall(
                    r'To Reproduce((.|\n)*?)Additional context', data_['body'])[0][0]

            data = {'Bug description': commit.msg,
                    'Sample Code': issue_code,
                    'Bug fix': changes}
        else:
            if not os.path.exists('repos/pytorch'):
                subprocess.call(
                    f'git clone https://github.com/pytorch/pytorch.git repos/pytorch', shell=True)

            changes = []
            try:
                for commit in Repository('repos/pytorch', single=sha_str).traverse_commits():
                    for modification in commit.modified_files:
                        changes.append(modification.diff)
            except Exception as e:
                print(e)

            data = {'Issue title': issue_title_,
                    'Bug description': issue_description,
                    'Sample Code': changes,
                    'Bug fix': ''}

            return data


if __name__ == "__main__":
    main()
