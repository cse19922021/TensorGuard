from pydriller import Repository
import re, os, sys, json
import pandas as pd
import subprocess

ROOT_DIR = os.getcwd()
REG_CHANGED = re.compile(".*@@ -(\d+),(\d+) \+(\d+),(\d+) @@.*")
REG_LOC_FLAWFINDER = re.compile('\:(\d+)\:')
REG_RATS = re.compile('<vulnerability>')
REG_CPP_CHECK_LOC = re.compile('line=\"(\d+)\"')
REG_CPP_CHECK = re.compile('error id=')
FIND_CWE_IDENTIFIER = re.compile('CWE-(\d+)')
FIND_RATS_VUL_TYPE = re.compile('<type.*>((.|\n)*?)<\/type>')


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

def get_patches(splitted_lines):
    change_info = {}
    i = 0
    for line in splitted_lines:
        if REG_CHANGED.match(line):
            i += 1
            deletedStart = int(REG_CHANGED.search(line).group(1))
            deletedLines = int(REG_CHANGED.search(line).group(2))
            addStart = int(REG_CHANGED.search(line).group(3))
            addedLines = int(REG_CHANGED.search(line).group(4))
                        
            start = deletedStart
            if(start == 0):
                start += 1
    
            end = addStart+addedLines-1
            change_info[i] = [deletedStart, deletedStart+deletedLines]

    super_temp = []
    j = 0
    indices = []
    while j < len(splitted_lines):
        if re.findall(r'(@@)',splitted_lines[j]):
            indices.append(j)
        j += 1

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
            for row in range(indices[i]+1, indices[j]):
                temp.append(splitted_lines[row])
            super_temp.append(temp)
            if j == len(indices)-1:
                temp = [] 
                for row in range(indices[j]+1, len(splitted_lines)):
                    temp.append(splitted_lines[row])
                super_temp.append(temp)
                break
            i+= 1
            j+= 1
    return super_temp, change_info

def get_diff_header(diff):
    code_lines = diff.split('\n')
    [super_temp, change_info] = get_patches(code_lines)
    return change_info

def get_fix_file_names(commit):
    f_names = {}
    raw_name = []
    if 'test' not in commit.filename:
        diff_split = get_diff_header(commit.diff)
        if bool(commit.new_path):
            f_names[commit.new_path] = diff_split
            raw_name.append(commit.new_path)
        else:
            f_names[commit.old_path] = diff_split
            raw_name.append(commit.old_path)
    else:
        if 'test' not in commit.filename:
            diff_split = get_diff_header(commit.diff)
            if bool(commit.new_path):
                f_names[commit.new_path] = diff_split
                raw_name.append(commit.new_path)
            else:
                f_names[commit.old_path] = diff_split
                raw_name.append(commit.old_path)
    return f_names, raw_name

def changed_lines_to_list(cl):
    global_list = []
    for k, v in cl.items():
        for sk, sv in v.items():
            global_list = global_list + sv
    return global_list

def get_added_deleted_lines(mod):
    out = []
    for item in mod:
        out.append(item[1])
    return "\n".join(out)

def get_code_change(sha, libname):
    changes = []
    changed_lines = []
    before_union = []
    after_union = []
    stat = []
    try:
        for commit in Repository(f'ml_repos/{libname}', single=sha).traverse_commits():
            for modification in commit.modified_files:
                #if file_name.split('/')[-1] == modification.filename:
                cl, raw_name = get_fix_file_names(modification)
                cl_list = changed_lines_to_list(cl)
                added_lines = get_added_deleted_lines(modification.diff_parsed['added'])
                deleted_lines = get_added_deleted_lines(modification.diff_parsed['deleted'])
                changes.append(modification.diff)
                changed_lines.append(cl)
                before_union.append(modification.source_code_before.split('\n'))
                after_union.append(modification.source_code.split('\n'))
                stat.append([cl, modification.source_code_before, modification.diff_parsed['deleted']])
    except Exception as e:
        print(e)
    return stat

def slice_code_base(changed_lines, code):
    split_code = code.split('\n')
    split_code = split_code[changed_lines[0][1][0]:changed_lines[0][1][1]] 
    return "\n".join(split_code)

if __name__ == '__main__':

    # full_link = sys.argv[1]
    # file_name = sys.argv[2]

    out_buggy = {
        'code': [],
    }

    out_clean = {
        'code': []
    }

    data = pd.read_csv('data/data.csv')
    
    for idx, row in data.iterrows():
        print(row['Commit'])
        full_link = row['Commit'].split('/')[-1]
        # if row['Commit'] == 'https://github.com/tensorflow/tensorflow/commit/8a47a39d9697969206d23a523c977238717e8727':
        #     print('')

        if row['Library'] == 'tensorflow' or row['Library'] == 'pytorch':
            repository_path = ROOT_DIR+'/ml_repos/'+row['Library']
        else:
            repository_path = ROOT_DIR+'/ml_repos/'+row['Library']+'/'+dir.split('_')[1].split('.')[0]

        v = f"https://github.com/{row['Library']}/{row['Library']}.git"

        if not os.path.exists(repository_path):
            subprocess.call('git clone '+v+' '+repository_path, shell=True)

        commit_stat = get_code_change(full_link, row['Library'])
        changed_lines = [commit_stat[0][0][key] for key in commit_stat[0][0]]
        if len(changed_lines[0]) == 1:
            code = slice_code_base(changed_lines, commit_stat[0][1])
        else:
            continue
        # deleted_lines, added_lines = separate_dadded_deleted(changes[0])

        if commit_stat:
            data_ = {
                'Library': row['Library'],
                'Commit Link': row['Commit'],
                'Bug report': row['bug report'],
                'Deleted lines': commit_stat[0][1],
                'Added lines': commit_stat[0][2],
                'Changed lines': commit_stat[0][3],
                'Deleted code': commit_stat[0][4],
                'Added code': commit_stat[0][5]}
                
        with open("data/data.json", "a") as json_file:
            json.dump(data_, json_file, indent=4)
            json_file.write(',')
            json_file.write('\n')
            