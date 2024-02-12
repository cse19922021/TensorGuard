from csv import writer
import os, subprocess, re, csv
from git import Repo
from datetime import datetime
from datetime import datetime, timezone
from openai import OpenAI
import backoff, time
import tiktoken
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ.get(".env")
)
REPO_LIST = ["https://github.com/tensorflow/tensorflow"]

THIS_PROJECT = os.getcwd()

def write_list_to_txt4(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')

def save_commit(data, lib):
    if not os.path.exists(f'mining/commits/{lib}/'):
        os.makedirs(f'mining/commits/{lib}/')

    with open(f"mining/commits/{lib}/{lib}.csv","a", newline="\n",) as fd:
        writer_object = csv.writer(fd)
        writer_object.writerow(data)

def read_txt(fname):
    with open(fname, "r") as fileReader:
        data = fileReader.read()
    return data

def completions_with_backoff(prompt, model='gpt-4-0125-preview'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response

def stage_1_prompting(item):
    prompt_ = f"""
    You are a chatbot responsible for classifying a commit message that fixing bugs in tensorflow backend implementation.
    Your task is to classify if the commit is fixing an improper/missing validation/checker bug. Please generate binary response, i.e., yes or no.

    Here is the commit message:
    Commit message: {item}

    Result: <your response>

    """

    return prompt_

def stage_2_prompting(item):
    prompt_ = f"""
    You are a chatbot responsible for analyzing a commit message that fixing bugs in pytorch backend implementation.
    Your task is to perform analysis on the bug fixing commit that fixing an improper/missing validation/checker bug.

    Here is the commit message:
    Commit message: {item}

    
    
    Result: <your response>

    """

    return prompt_

def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens

def main():

    r_prime = REPO_LIST[0].split("/")

    v = REPO_LIST[0] + ".git"

    if not os.path.exists(
        THIS_PROJECT + "/ml_repos_cloned/" + r_prime[3] + "/" + r_prime[4]
    ):
        subprocess.call(
            "git clone "
            + v
            + " "
            + THIS_PROJECT
            + "/ml_repos_cloned/"
            + r_prime[3]
            + "/"
            + r_prime[4],
            shell=True,
        )

    r = Repo(THIS_PROJECT + "/ml_repos_cloned/" + r_prime[3] + "/" + r_prime[4])

    # subprocess.check_call(
    #     "./mining/checkout.sh %s "
    #     % (THIS_PROJECT + "/ml_repos_cloned/" + r_prime[3] + "/" + r_prime[4]),
    #     shell=True,
    # )

    subprocess.run("./mining/checkout.sh", shell=True)

    hisotry_file = f'logs/{r_prime[3]}_parsed_commits.txt'

    if not os.path.exists(hisotry_file):
        f1 = open(hisotry_file, 'a')

    if r_prime[3] == 'pytorch':
        max_count = 69389
        branch_name = 'main'
    else:
        max_count = 159725
        branch_name = "master"

    all_commits = list(r.iter_commits(branch_name, max_count=max_count))
    hist = read_txt(f'logs/{r_prime[3]}_parsed_commits.txt')

    rules = r"(\bchecker\b|\bvalidating\b|\bcheckers\b|\bchecking\b|\bparameter validation\b|\bvalidation vulnerability\b|\bboundary\b|\bboundary validation\b|\binvalid input\b|\bvalidation bypass\b|\bchecks\b|\bcheck\b|\bdata validation\b|\binput validation\b|\bvalidation\b|\bcheck\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bbypass\b|\binjection\b|\boverflow\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bFPE runtime\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcorrupt\b|\bcrack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\boverflow\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bsecurity\b|\bsecurity fix\b|\bsecurity issue\b|\bsecurity problem\b|\bsnprintf\b|\bundefined behavior\b|\bunderflow\b|\buninitialize\b|\buse after free\b|\buse-after-free\b|\bviolate\b|\bviolation\b|\bvsecurity\b|\bvuln\b|\bvulnerab\b)"
    try:
        temp = []
        for i, com in enumerate(all_commits):
            if com.hexsha not in hist:
                write_list_to_txt4(com.hexsha, f'logs/{r_prime[3]}_parsed_commits.txt')
                _date = datetime.fromtimestamp(com.committed_date)

                security_match = re.findall(rules, com.message)

                print("Analyzed commits: {}/{}".format(i, len(all_commits)))
                
                if security_match and "typo" not in com.message:
                    if 2016 <= _date.year <= 2024:
                        prompt_ = stage_1_prompting(com.message)
                        t_count = get_token_count(prompt_)
                        if t_count <= 4097:
                            time.sleep(3)
                            conversations = completions_with_backoff(prompt_)
                            decision = conversations.choices[0].message.content

                        commit_link = REPO_LIST[0] + "/commit/" + com.hexsha
                        commit_date = com.committed_date
                        dt_object = datetime.fromtimestamp(commit_date)
                        commit_date = dt_object.replace(tzinfo=timezone.utc)
                        data = [commit_link, commit_date.strftime("%Y-%m-%d %H:%M:%S"), decision]
                        save_commit(data, r_prime[3])
            else:
                print('This commit has been already analyzed!')

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()