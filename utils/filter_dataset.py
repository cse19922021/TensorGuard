import pandas as pd
import subprocess, os
from pydriller import Repository
from datetime import datetime, timezone
import csv

ROOT_DIR = os.getcwd()

def write_to_csv(data, agent_type):
    with open(f"output_{agent_type}.csv", 'a', encoding="utf-8", newline='\n') as file_writer:
        write = csv.writer(file_writer)
        write.writerow(data)

def exclude():
    pass

def check_commit_exists(all_data, a):
    df_filtered = all_data[~all_data['Commit'].isin(a)]
    return df_filtered

def is_after_september_2021(date):
    september_2021 = datetime(2021, 9, 30, tzinfo=timezone.utc)
    return date > september_2021

def extract_non_biased(buggy_data, all_data):
    counter = 0
    new_buggy_data = []
    new_clean_data = []
    for idx, row in buggy_data.iterrows():
        full_link = row['Commit'].split('/')[-1]

        if row['Library'] == 'tensorflow' or row['Library'] == 'pytorch':
            repository_path = ROOT_DIR+'/ml_repos/'+row['Library']
        else:
            repository_path = ROOT_DIR+'/ml_repos/'+row['Library']+'/'+dir.split('_')[1].split('.')[0]

        v = f"https://github.com/{row['Library']}/{row['Library']}.git"

        if not os.path.exists(repository_path):
            subprocess.call('git clone '+v+' '+repository_path, shell=True)
        
        for commit in Repository(f"ml_repos/{row['Library']}", single=full_link).traverse_commits():
            if is_after_september_2021(commit.author_date):
                counter = counter + 1
                write_to_csv([row['Commit']], 'new_bug_data')
                new_buggy_data.append(row['Commit'])
                #a.append([row["Library"], row["Commit Link"], row["Root Cause"], row["Bug report"], "Number of deleted lines"], row["Deleted lines"], row["Added lines"])

    all_data = check_commit_exists(all_data, new_buggy_data)
    sampled_df = all_data.sample(n=len(new_buggy_data), random_state=42)
    sampled_df.to_csv('new_clean_data.csv', sep=',',index=False)
    

def main():
    buggy_data = pd.read_csv('data/data_buggy.csv')
    all_data = pd.read_csv('data/NonBiasedWholeData.csv')
    extract_non_biased(buggy_data, all_data)

if __name__ == '__main__':
    main()