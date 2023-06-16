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
        bug_fix = item["Bug fix"]

        _prompt = f"""
                Given following pieces of information:\
                    Title: {Title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    Bug fix: {bug_fix}
                
                Generate a malformed input generation rule for the mentioned API in the issue. The rule should be usable for fuzzing. \
                Generate the rule based on the malicious inputs explained in the title and bug description.
                Do not suggest any fix.\
                Do not explain what is the weakness in the backend.\
                Don't generate any example.
                """
    return _prompt


def run():

    lib_name = 'tf'
    model_name = 'gpt-3.5-turbo-0301'

    rules_path = f"rulebase/{lib_name}_rules_textual.json"

    with open(f'data/{lib_name}_bug_data.json') as json_file:
        data = json.load(json_file)
        for item in data:
            prompt = create_prompt(item, lib_name)
            conversations = gpt_conversation(prompt, model=model_name)

            try:
                # rule_ = json.loads(conversations.choices[0].message.content)

                # first_key = next(iter(item))
                # rule_.update({'link': item[first_key]})

                rule_ = {'rule': conversations.choices[0].message.content}
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
