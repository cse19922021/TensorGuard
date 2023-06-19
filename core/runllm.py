from json.decoder import JSONDecodeError
import os
import openai
import json
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")

# import dotenv


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

            _prompt = f"""
                Given following pieces of information:\
                    Issue title: {issue_title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                
                Generate a malformed input generation rule for the mentioned API in the issue. The rule should be usable for fuzzing. \
                Do not suggest any fix.\
                Do not explain what is the weakness in the backend.\
                Just create a bug pattern.  \ 
                Generate the rule as a json format.
                """

        if "Commit link" in item.keys():
            bug_description = item["Bug description"]
            sample_code = item["Bug fix"]

            _prompt = f"""
                Given following pieces of information:\
                    Commit title: {bug_description} \
                    Code change: {sample_code} \
                
                Generate a malformed input generation rule for the mentioned API in the issue. The rule should be usable for fuzzing. \
                Do not suggest any fix.\
                Do not explain what is the weakness in the backend.\
                Just create a bug pattern. \ 
                Generate the rule as a json format.          
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
                
                Your task is to generate a malformed input generation rule. The rule should be usable for fuzzing. \
                To better understand how to generate the rule, please consider the following steps:\
                    
                1 - Figure out which TensorFlow API is mentioned in the ```Title``` or ```Bug description```\
                2 - Understand input specification for the API
                3 - Understand what input is causing bug, i.e., it should be explain in the ```Title``` or ```Bug description```\
                4 - Understand the impact of the bug explained in the ```Bug description```\
                5 - Understand the minimum reproduceable example that cause the bug \
                    
                Based on above steps, generate the rule based on the malicious inputs explained in the title and bug description. \
                
                Perform the rule generation based on the following constraints:
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                4 - Do not explain the input specification.\
                5 - Concisely generate the rule for fuzzing.
                """

        _prompt_general = f"""
                Given following pieces of information:\
                    Title: {Title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \

                
                Your task is to generate a malformed input generation rule. The rule should be usable for fuzzing. \
                To better understand how to generate the rule, please consider the following steps:\
                    
                1 - Figure out which TensorFlow API is mentioned in the ```Title``` or ```Bug description```\
                2 - Understand input specification for the API\
                3 - Understand what input is causing bug, i.e., it should be explain in the ```Title``` or ```Bug description```\
                4 - Understand the impact of the bug explained in the ```Bug description```\
                5 - Understand the minimum reproduceable example that cause the bug \
                    
                Based on above steps, generate the rule based on the malicious inputs explained in the title and bug description. \
                ```Your task is to generate a general rule that is applicable for other APIs as well```
                ```For example, if the bug description says the bug is due to feeding very large integer value for \
                    the paramer ```dim```, this means that we can use ```A Very Large Integer Value``` as a general\
                        rule for all APIs that have integer argument. \
                
                
                Perform the rule generation based on the following constraints:
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                4 - Do not explain the input specification.\
                5 - Concisely generate the rule for fuzzing.
                """

        _prompt_space_partioning = f"""
                Given following pieces of information:\
                    Title: {Title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    API Signature: {api_sig}
                    
                Your task is to perform input space paritioning, for each parition generate a set of malformed inputs based on malicious inputs that are explained in the bug \
                    description and title.
                To better understand how to generate the rule, please consider the following steps:\
                    
                1 - Understand input specification for the API\
                2 - Understand what input is causing bug, i.e., it should be explain in the ```Title``` or ```Bug description```\
                3 - Understand the impact of the bug explained in the ```Bug description```\
                4 - Understand the minimum reproduceable example that cause the bug \ 
                5 - Give output as JSON structure. 
                
                Consider the following constraints: \
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                4 - Do not explain the input specification.\
                """

    return _prompt_space_partioning


def run():

    lib_name = 'tf'
    model_name = 'gpt-3.5-turbo'

    rules_path = f"rulebase/{lib_name}_rules_general.json"

    with open(f'data/{lib_name}_bug_data.json') as json_file:
        data = json.load(json_file)
        for item in data:
            prompt = create_prompt(item, lib_name)

            Title = item["Title"]
            bug_description = item["Bug description"]
            sample_code = item["Sample Code"]
            api_sig = item["API Signature"]

            input_parition_prompt_level1 = f"""
            Perform input space paritionining given the following API signature:
            API Signature: {api_sig}
            
            Please consider the following constraints:
            1 - Do not explain anything
            2 - Just give paritions in an structured format
            """
            _parition_response_level1 = gpt_conversation(
                input_parition_prompt_level1, model=model_name)

            print()

            input_parition_prompt_level2 = f"""
            Given the following input space partitioning:\
            {_parition_response_level1.choices[0].message.content}\
            Performed on the following API:\
            API: {api_sig}\
            
            Redo the input space partitioning of the API {api_sig} based on the following bug title and bug description:\
            Bug description: {bug_description}\
            Title: {Title}\
            
            Please note that the bug description is collected from TensorFlow Security Advisory and explaining \
                a security vulnerability based on malformed inputs. \
            Rewrite the input space paritioning in such a way that it detect bug via fuzzing. \
            
            Please consider the following constraints:
            1 - Do not explain anything
            2 - Just give paritions in an structured format
            """

            _parition_response_level2 = gpt_conversation(
                input_parition_prompt_level2, model=model_name)

            print(_parition_response_level2.choices[0].message.content)
            print('')

            try:
                # rule_ = json.loads(conversations.choices[0].message.content)

                # first_key = next(iter(item))
                # rule_.update({'link': item[first_key]})

                rule_ = {
                    'rule': _parition_response_level2.choices[0].message.content}
                rule_.update({'link': item['Link']})
                print(rule_)

                with open(rules_path, "a") as json_file:
                    json.dump(rule_, json_file, indent=4)
                    json_file.write(',')
                    json_file.write('\n')

            except JSONDecodeError as e:
                print(e)


if __name__ == '__main__':
    run()
