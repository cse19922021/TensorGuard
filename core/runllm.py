from json.decoder import JSONDecodeError
import os
import openai
import backoff
import json
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")

# import dotenv

def completions_with_backoff(**kwargs):
    return openai.Completion.create(**kwargs)

def gpt_conversation(prompt, model="gpt-3.5-turbo"):

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response


def create_prompt(item, model='tf'):
    if model == 'torch':
        if "Issue link" in item.keys():
            issue_title = item["Issue title"]
            bug_description = item["Bug description"]
            sample_code = item["Sample Code"]
            api_sig = item["API Signature"]

            _prompt_specific = f"""
                Given following pieces of information:\
                    Title: {issue_title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    API Siganture: {api_sig} \
                
                The above information are artifacts collected from security-related PyTorch issues collected from Github.\
                In all issues, there is one API that is vulnerable to due the fact that attackers can feed malicious inputs.\
                Based on the information, your tasks are as follows: \
                1 - Explain the root cause of bug using the following structure:\
                    Bug due to ```explain the root cause here```, e.g., ```Bug due to feeding very large integer variable```\
                2 - Do not explain root cause in detail. The purpose is to understand the malicious arguments to DL APIs. \
                3 - Determine the type of the buggy argument \
                
                Your task is to structure the response as a JSON with the following key-value pairs:\
                
                Root Cause: Root cause explanation\
                Argument Type: Type of argument\
                    
                Note: Please note that the root causes are going to be used for building fuzzer to fuzz the backend implementation of PyTorch.\
                    
                You also need to consider the following constraints:\
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                """

        if "Commit link" in item.keys():
            bug_description = item["Bug description"]
            sample_code = item["Bug fix"]
            api_sig = item["API Signature"]

            _prompt_specific = f"""
                Given following pieces of information:\
                    Title: {issue_title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    API Siganture: {api_sig} \
                
                The above information are artifacts collected from security-related PyTorch issues collected from Github.\
                In all issues, there is one API that is vulnerable to due the fact that attackers can feed malicious inputs.\
                Based on the information, your tasks are as follows: \
                1 - Explain the root cause of bug using the following structure:\
                    Bug due to ```explain the root cause here```, e.g., ```Bug due to feeding very large integer variable```\
                2 - Do not explain root cause in detail. The purpose is to understand the malicious arguments to DL APIs. \
                3 - Determine the type of the buggy argument \
                
                Your task is to structure the response as a JSON with the following key-value pairs:\
                
                Root Cause: Root cause explanation\
                Argument Type: Type of argument\
                    
                Note: Please note that the root causes are going to be used for building fuzzer to fuzz the backend implementation of PyTorch.\
                    
                You also need to consider the following constraints:\
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                """
    else:
        Title = item["Title"]
        bug_description = item["Bug description"]
        sample_code = item["Sample Code"]
        api_sig = item["API Signature"]

        _prompt_specific = f"""
                Given following pieces of information:\
                    Title: {Title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    API Siganture: {api_sig} \
                
                The above information are artifacts collected from security-related PyTorch issues collected from Github.\
                In all issues, there is one API that is vulnerable to due the fact that attackers can feed malicious inputs.\
                Based on the information, your tasks are as follows: \
                1 - Explain the root cause of bug using the following structure:\
                    Bug due to ```explain the root cause here```, e.g., ```Bug due to feeding very large integer variable```\
                2 - Do not explain root cause in detail. The purpose is to understand the malicious arguments to DL APIs. \
                3 - Determine the type of the buggy argument \
                
                Your task is to structure the response as a JSON with the following key-value pairs:\
                
                Root Cause: Root cause explanation\
                Argument Type: Type of argument\
                    
                Note: Please note that the root causes are going to be used for building fuzzer to fuzz the backend implementation of PyTorch.\
                    
                You also need to consider the following constraints:\
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                """

    return _prompt_specific


def run():

    lib_name = 'tf'
    model_name = 'gpt-3.5-turbo'

    rules_path = f"rulebase/{lib_name}_rules_general.json"

    with open(f'data/{lib_name}_bug_data.json') as json_file:
        data = json.load(json_file)
        for item in data:
            prompt = create_prompt(item, lib_name)

            # _parition_response_level2 = gpt_conversation(
            #     prompt, model=model_name)
        
        
            _parition_response_level2 = completions_with_backoff(model=model_name, prompt)

            print(_parition_response_level2.choices[0].message.content)

            try:
                # rule_ = json.loads(conversations.choices[0].message.content)

                rule_ = {
                    'rule': _parition_response_level2.choices[0].message.content}
                _key = next(iter(item))
                rule_.update({'link': item[_key]})

                print(rule_)

                with open(rules_path, "a") as json_file:
                    json.dump(rule_, json_file, indent=4)
                    json_file.write(',')
                    json_file.write('\n')

            except JSONDecodeError as e:
                print(e)


if __name__ == '__main__':
    run()
