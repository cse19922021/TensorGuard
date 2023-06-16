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


def create_prompt(item):
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
    return _prompt


def run():
    rules_path = "rulebase/torch_rules.json"

    with open('data/torch_bug_data.json') as json_file:
        data = json.load(json_file)
        for item in data:
            prompt = create_prompt(item)
            conversations = gpt_conversation(prompt)
            rule_ = json.loads(conversations.choices[0].message.content)

            first_key = next(iter(item))
            rule_.update({'link': item[first_key]})
            print(rule_)

            with open(rules_path, "a") as json_file:
                json.dump(rule_, json_file, indent=4)
                json_file.write('\n')


if __name__ == '__main__':
    run()
