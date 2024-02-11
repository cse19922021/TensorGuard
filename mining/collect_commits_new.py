from csv import writer
import os, subprocess, re, csv
from git import Repo
from datetime import datetime
from datetime import datetime, timezone

REPO_LIST = ["https://github.com/pytorch/pytorch"]

THIS_PROJECT = os.getcwd()

def save_commit(data, lib):
    if not os.path.exists(f'mining/commits/{lib}/'):
        os.makedirs(f'mining/commits/{lib}/')

    with open(f"mining/{lib}/{lib}.csv","a", newline="\n",) as fd:
        writer_object = csv.writer(fd)
        writer_object.writerow(data)

def read_txt(fname):
    with open(fname, "r") as fileReader:
        data = fileReader.read()
    return data

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

    if r_prime[3] == 'pytorch':
        max_count = 69389
        branch_name = 'main'
    else:
        max_count = 159725
        branch_name = "master"
        
    all_commits = list(r.iter_commits(branch_name, max_count=69389))

    rules = r"(\bchecker\b|\bvalidating\b|\bcheckers\b|\bchecking\b|\bparameter validation\b|\bvalidation vulnerability\b|\bboundary\b|\bboundary validation\b|\binvalid input\b|\bvalidation bypass\b|\bchecks\b|\bcheck\b|\bdata validation\b|\binput validation\b|\bvalidation\b|\bcheck\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bbypass\b|\binjection\b|\boverflow\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bFPE runtime\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcorrupt\b|\bcrack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\boverflow\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bsecurity\b|\bsecurity fix\b|\bsecurity issue\b|\bsecurity problem\b|\bsnprintf\b|\bundefined behavior\b|\bunderflow\b|\buninitialize\b|\buse after free\b|\buse-after-free\b|\bviolate\b|\bviolation\b|\bvsecurity\b|\bvuln\b|\bvulnerab\b)"
    try:
        temp = []
        for i, com in enumerate(all_commits):

            _date = datetime.fromtimestamp(com.committed_date)

            security_match = re.findall(rules, com.message)

            print("Analyzed commits: {}/{}".format(i, len(all_commits)))
            if security_match and "typo" not in com.message:
                if 2016 <= _date.year <= 2021:
                    print("got one!")
                    commit_link = REPO_LIST[0] + "/commit/" + com.hexsha
                    commit_date = com.committed_date
                    commit_date = commit_date.replace(tzinfo=timezone.utc)
                    data = [commit_link, commit_date.strftime("%Y-%m-%d %H:%M:%S")]
                    temp.append(commit_link)
                    save_commit(data, 'tensorflow')

    except Exception as e:
        print(e.message)

    # with open(f"./mining/commits/{r_prime[4]}/{r_prime[4]}.txt", "a") as f:
    #     for item in temp:
    #         f.write("%s\n" % item)


if __name__ == "__main__":
    main()