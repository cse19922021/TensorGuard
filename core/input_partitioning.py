import pandas as pd
from collections import Counter
import pymongo
import json
import os
import tiktoken
import openai
import backoff
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")

DB = pymongo.MongoClient(host='127.0.0.1', port=27017)['freefuzz-tf']


def read_txt(fname):
    with open(fname, "r") as fileReader:
        data = fileReader.read().splitlines()
    return data


def write_list_to_txt4(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')


def calculate_rule_importance(data):
    element_frequency = Counter(data['Anomaly'].values.flatten())
    total_elements = len(data['Anomaly'].values.flatten())
    element_importance = {element: frequency /
                          total_elements for element, frequency in element_frequency.items()}
    return sorted(element_importance.items(), key=lambda x: x[1], reverse=True)


def main():
    data = pd.read_csv('data/TF_RECORDS.csv', sep=',', encoding='utf-8')
    weights_ = calculate_rule_importance(data)
    unique_types = data['Category'].unique()
    unique_types = list(unique_types)
    for dtype in unique_types:
        anomalies = data.loc[data['Category'] == dtype, 'Anomaly']
        anomalies_unique = list(anomalies.unique())
        print('')


def gpt_conversation(prompt, model="gpt-3.5-turbo"):

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response


def create_prompt_fix_sugesstion():
    prompt_ = f"""
    You are an experienced software developer in API-level fuzz testing. You are great at understanding software security and bugs that are caused by feeding malicious inputs to APIs. When you don't know how to do input space partitioning, you admit that you don't know. 

    Your task is to perform input space partitioning for each parameter in {api_name}. The arguments and their values are:
    Arguments: {record}
    
    Generate as many partitions as you can for each argument.  
    
    Please output the partitions in given json format:
        
    <answer json start>,
    "Partition 1":"Explain partition 1",
    "Partition 2":"Explain partition 2",
    ...
    "Partition n":"Explain partition n",

    """

    return prompt_

def create_prompt(api_name, record):
    prompt_ = f"""
    You are an experienced software developer in API-level fuzz testing. You are great at understanding software security and bugs that are caused by feeding malicious inputs to APIs. When you don't know how to do input space partitioning, you admit that you don't know. 

    Your task is to perform input space partitioning for each parameter in {api_name}. The arguments and their values are:
    Arguments: {record}
    
    Generate as many partitions as you can for each argument.  
    
    Please output the partitions in given json format:
        
    <answer json start>,
    "Partition 1":"Explain partition 1",
    "Partition 2":"Explain partition 2",
    ...
    "Partition n":"Explain partition n",

    """

    return prompt_


def create_prompt_type_partitioning(arg_type):

    prompt_type = f"""
    You are an experienced software developer in fuzz testing as well as API-level testing. You are great at understanding software security and bugs that are caused by malicious inputs to APIs. When you don't know how to do input space partitioning, you admit that you don't know. 

    Your task is to perform input space partitioning for a {arg_type} argument. Generate as many partitions as you can.

    Please output the partitions in given json format:
    
    <answer json start>
    "Partition 1":"Python code for partition 1",
    "Partition 2":"Python code for partition 2",
    ...
    "Partition n":"Python code for partition n",

    """
    return prompt_type


def get_api_seed(api_name):
    record = DB[api_name].aggregate([{"$sample": {"size": 1}}])
    if not record.alive:
        print(f"NO SUCH API: {api_name}")
        assert (0)
    record = record.next()
    record.pop("_id")
    assert ("_id" not in record.keys())
    return record


def exec_input_sp_type():
    lib_name = 'tf'
    rules_path = f"parition_rules/{lib_name}_type_patitions.json"
    type_lists = ['ArgType.Tensor', 'ArgType.INT', 'ArgType.STR',
                  'ArgType.FLOAT', 'ArgType.LIST', 'ArgType.TUPLE']
    for arg_type in type_lists:
        prompt_ = create_prompt_type_partitioning(arg_type)
        t_count = get_token_count(prompt_)
        if t_count <= 4097:
            conversations = completions_with_backoff(prompt_)
            rule_ = conversations.choices[0].message.content

            try:
                x = json.loads(rule_)
                x.update({'Arg type': arg_type})

                with open(rules_path, "a") as json_file:
                    json.dump(x, json_file, indent=4)
                    json_file.write(',')
                    json_file.write('\n')
            except Exception as e:
                print(e)
        else:
            print("Your messages exceeded the limit.")

        print('')


def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(prompt, model='gpt-3.5-turbo'):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return response


def exec_input_sp():
    lib_name = 'torch'
    rules_path = f"parition_rules/{lib_name}_fixes.json"

    hisotry_file = f"logs/parsed_apis.txt"

    if not os.path.exists(hisotry_file):
        f1 = open(hisotry_file, 'a')

    hist = read_txt(f'logs/parsed_apis.txt')
    for api_name in DB.list_collection_names():
        if api_name not in hist:
            write_list_to_txt4(api_name, hisotry_file)
            print(api_name)

            record = get_api_seed(api_name)
            record_json = json.dumps(record)
            prompt_ = create_prompt(api_name, record_json)
            t_count = get_token_count(prompt_)
            if t_count <= 4097:
                conversations = completions_with_backoff(prompt_)
                rule_ = conversations.choices[0].message.content

                try:
                    x = json.loads(rule_)
                    x.update({'API name': api_name})
                    x.update({'API params': record_json})
                    

                    with open(rules_path, "a") as json_file:
                        json.dump(x, json_file, indent=4)
                        json_file.write(',')
                        json_file.write('\n')
                except Exception as e:
                    print(e)
            else:
                print("Your messages exceeded the limit.")


if __name__ == '__main__':
    exec_input_sp_type()
