from json.decoder import JSONDecodeError
import os
import openai
import backoff
import tiktoken
import json
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")

template_string = """
                Observations: Given following pieces of information:\
                    Title: {_title} \
                    Bug description: {bug_description} \
                    Minimum reproduceable example: {sample_code} \
                    API Siganture: {api_sig} \
                    Code change: {code_change}
                
                Explanations: The above information are artifacts collected from security-related PyTorch issues collected from Github.\
                In all records, there is atleast one API that is vulnerable to due the fact that attackers can feed malicious inputs.\
                
                Tasks: Your tasks are as follows: \
                1 - First, throughly parse the bug description to understand what is the root cause of the bug.\
                2 - Second, throughly parse the minimum reproduceable example and try to find the malicious parameter.\
                3 - If the bug description is not informative enough, try to understand the root cause by parsing the source code.\
                4 - Explain the root cause of bug using the following structure:\
                    Bug due to ```root cause here```, e.g., ```Bug due to feeding very large integer variable```\
                5 - Explain the root cause in one sentence.
                6 - Do not explain the impact of the bugs. Do not explain the results of the bugs, just explain the root cause.\
                7 - Do not explain root cause in detail. The purpose is to understand the malicious arguments to DL APIs. \
                8 - Determine the type of the buggy argument.\
                9 - You should only consider the following torch types: Tensor, Integer, String, Float, Null, Tuple,\
                    List, Bool, TORCH_VARIABLE, TORCH_DTYPE, TORCH_OBJECT, TF_VARIABLE, TF_DTYPE, TF_OBJECT
                    
                Note: Please note that the root causes are going to be used for building fuzzer to fuzz the backend implementation of PyTorch.\
                    
                Constraints: You also need to consider the following constraints:\
                1 - Do not suggest any fix.\
                2 - Do not explain what is the weakness in the backend.\
                3 - Do not generate any example. \
                    
                Output:
                5 - Your task is to structure the output as JSON with the following keys:\
                    Root Cause\
                    Argument Type\
                    
                {formatted_response}
                """


chat_ = ChatOpenAI(temperature=0.0, openai_api_key=os.getenv("API_KEY"))

_prompt_template = ChatPromptTemplate.from_template(template=template_string)


def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def completions_with_backoff(model, prompt):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response


def gpt_conversation(prompt, model="gpt-3.5-turbo"):

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response


def _formatOutput():
    _root_case_schema = ResponseSchema(
        name='Root Cause', description='Root cause explanation')
    _arg_type_schema = ResponseSchema(name='Argument Type',
                                      description='The type of buggy argument')

    response_schemas = [_root_case_schema, _arg_type_schema]
    output_parser = StructuredOutputParser.from_response_schemas(
        response_schemas)
    format_instructions = output_parser.get_format_instructions()
    return format_instructions, output_parser


def run_llm(item, formatted_response, model='tf'):

    if model == 'torch':
        if "Issue link" in item.keys():
            issue_title = item["Issue title"]
            bug_description = item["Bug description"]
            sample_code = item["Sample Code"]
            api_sig = item["API Signature"]

            torch_issue_message = _prompt_template.format_messages(
                _title=issue_title,
                bug_description=bug_description,
                sample_code=sample_code,
                code_change="",
                api_sig=api_sig,
                formatted_response=formatted_response
            )

            t_count = get_token_count(torch_issue_message[0].content)
            if t_count <= 4097:
                response_ = chat_(torch_issue_message)
                return response_
            else:
                return False

        if "Commit link" in item.keys():
            bug_description = item["Bug description"]
            api_sig = item["API Signature"]
            code_change = item['Code change']
            torch_commit_message = _prompt_template.format_messages(
                _title="",
                bug_description=bug_description,
                sample_code="",
                code_change=code_change,
                api_sig=api_sig,
                formatted_response=formatted_response
            )

            t_count = get_token_count(torch_commit_message[0].content)
            if t_count <= 4097:
                response_ = chat_(torch_commit_message)
                return response_
            else:
                return False

    else:
        Title = item["Title"]
        bug_description = item["Bug description"]
        sample_code = item["Sample Code"]
        api_sig = item["API Signature"]
        code_change = item['Code change']

        tf_message = _prompt_template.format_messages(
            _title=Title,
            bug_description=bug_description,
            sample_code=sample_code,
            code_change=code_change,
            api_sig=api_sig,
            formatted_response=formatted_response
        )

        t_count = get_token_count(tf_message[0].content)
        if t_count <= 4097:
            response_ = chat_(tf_message)
            return response_
        else:
            return False


def run():

    lib_name = 'tf'
    model_name = 'gpt-3.5-turbo'

    rules_path = f"rulebase/{lib_name}_rules_general.json"

    with open(f'data/{lib_name}_bug_data.json') as json_file:
        data = json.load(json_file)
        for j, item in enumerate(data):
            print(f"Record {j}/{len(data)}")
            formatted_response, output_parser = _formatOutput()
            response_ = run_llm(item, formatted_response, lib_name)

            try:
                if response_:
                    output_dict = output_parser.parse(response_.content)

                    # _key = next(iter(item))
                    output_dict.update({'link': item['Link']})

                    with open(rules_path, "a") as json_file:
                        json.dump(output_dict, json_file, indent=4)
                        json_file.write(',')
                        json_file.write('\n')
                else:
                    print("Your messages exceeded the limit.")
            except JSONDecodeError as e:
                print(e)


if __name__ == '__main__':
    run()
