from pydriller import Repository
import os, re, csv, pytz
from datetime import datetime, timezone


def keyword_match(commit_msg):
    flag = False
    flaky_rules = r"(\bFlaky\b|\bflaky\b|\bUnreliable\b|\bFlickering\b|\bNon-deterministic\b|\bInstableb\|\bUnstable\b|\bIntermittent\b|\bRandom\b|\bInconsistent\b|\bFailing intermittently\b|\bTest instability\b|\bTest reliability\b|\bRace condition\b|\bFalse positives\b|\bFalse negatives\b|\bRandom failures\b|\bTest unpredictability\b|\bNon-reproducible\b|\bUnpredictable\b|\bUndeterministic\b|\bUnstable tests\b|\bTest variability\b|\bInconclusive tests\b|\bTest flakiness\b|\bTest inconsistency\b|\bUnreliable tests\b|\bTest robustness\b|\bTest failures\b|\bFluctuating tests\b|\bTest randomness\b)"
    memory_related_rules_strict = r"(\bparameter validation\b|\bvalidation vulnerability\b|\bboundary\b|\bboundary validation\b|\binvalid input\b|\bvalidation bypass\b|\bchecks\b|\bcheck\b|\bdata validation\b|\binput validation\b|\bvalidation\b|\bcheck\b|\bCheck failed\b|\bBus error\b|\bcore dumped\b|\bAborted\b|\bAborted (core dumped)\b|\bFloating Point Exception\b|\bfloating point exception\b|\bbottleneck\b|\bpoor\b|\bbslow\b|\bweakness\b|\bdefect\b|\bbug\b|\berror\b\bbinconsistent\b|\bbincorrect\b|\bbwrong\b|\bbunexpected\b|\bdenial of service\b|\bDOS\b|\bremote code execution\b|\bCVE\b|\bNVD\b|\bmalicious\b|\battack\b|\bexploit\b|\bRCE\b|\badvisory\b|\binsecure\b|\bsecurity\b|\binfinite\b|\bbypass\b|\binjection\b|\boverflow\b|\bHeap buffer overflow\b|\bInteger division by zero\b|\bUndefined behavior\b|\bHeap OOB write\b|\bDivision by zero\b|\bCrashes the Python interpreter\b|\bHeap overflow\b|\bUninitialized memory accesses\b|\bHeap OOB access\b|\bHeap underflow\b|\bHeap OOB\b|\bHeap OOB read\b|\bSegmentation faults\b|\bSegmentation fault\b|\bseg fault\b|\bBuffer overflow\b|\bNull pointer dereference\b|\bFPE runtime\b|\bsegfaults\b|\bsegfault\b|\battack\b|\bcorrupt\b|\bcrack\b|\bcraft\b|\bCVE-\b|\bdeadlock\b|\bdeep recursion\b|\bdenial-of-service\b|\bdivide by 0\b|\bdivide by zero\b|\bdivide-by-zero\b|\bdivision by zero\b|\bdivision by 0\b|\bdivision-by-zero\b|\bdivision-by-0\b|\bdouble free\b|\bendless loop\b|\bleak\b|\binitialize\b|\binsecure\b|\binfo leak\b|\bnull deref\b|\bnull-deref\b|\bNULL dereference\b|\bnull function pointer\b|\bnull pointer dereference\b|\bnull-ptr\b|\bnull-ptr-deref\b|\bOOB\b|\bout of bound\b|\bout-of-bound\b|\boverflow\b|\bprotect\b|\brace\b|\brace condition\b|RCE|\bremote code execution\b|\bsanity check\b|\bsanity-check\b|\bsecurity\b|\bsecurity fix\b|\bsecurity issue\b|\bsecurity problem\b|\bsnprintf\b|\bundefined behavior\b|\bunderflow\b|\buninitialize\b|\buse after free\b|\buse-after-free\b|\bviolate\b|\bviolation\b|\bvsecurity\b|\bvuln\b|\bvulnerab\b)"
    if re.findall(flaky_rules, commit_msg):
        flag = True
    return flag

def save_commit(data, lib, target):
    if not os.path.exists(f'mining/{target}/{lib}/'):
        os.makedirs(f'mining/{target}/{lib}/')

    with open(f"mining/{target}/{lib}/{lib}.csv","a", newline="\n",) as fd:
        writer_object = csv.writer(fd)
        writer_object.writerow(data)

def clone_repo(repo_url, clone_path):
    """
    Clone a Git repository to the specified path.
    
    Parameters:
    - repo_url: URL of the Git repository to clone.
    - clone_path: Path where the repository will be cloned.
    """
    if not os.path.exists(clone_path):
        os.makedirs(clone_path)

    os.system(f'git clone {repo_url} {clone_path}')

def iterate_parse_commits(repo_path, start_date, end_date, target):
    repo = Repository(repo_path)
    for commit in repo.traverse_commits():
        commit_date = commit.committer_date
        commit_date = commit_date.replace(tzinfo=timezone.utc)

        if 2018 <= commit_date.year <= 2023:
            if keyword_match(commit.msg):
                print(commit.hash)
                commit_link = f"https://github.com/{lib}/{lib}/commit/{commit.hash}"
                data = [lib, commit_link, commit_date.strftime("%Y-%m-%d %H:%M:%S")]
                save_commit(data, lib, target)


if __name__ == "__main__":
    lib = "tensorflow"
    target = "flaky"
    repo_url = f'https://github.com/{lib}/{lib}.git'

    start_date = datetime(2018, 1, 1)
    end_date = datetime(2023, 12, 31)

    clone_path = f'repos/{lib}'
    if not os.path.exists(clone_path):
        clone_repo(repo_url, clone_path)
    
    iterate_parse_commits(clone_path, start_date, end_date, target)