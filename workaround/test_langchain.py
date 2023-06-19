from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from json.decoder import JSONDecodeError
import os
import openai
import json
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG_ID")
openai.api_key = os.getenv("API_KEY")


def gpt_conversation(prompt, model="gpt-3.5-turbo"):

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response


def driver():
    _prompt = f"""
    Given the following API:
        torch.nn.CosineSimilarity(dim=1, eps=1e-08)
    How do you perform input space partioning on the input specification?
    """
    # _parition_response_level1 = gpt_conversation(_prompt)
    # print(_parition_response_level1.choices[0].message.content)

    chat_ = ChatOpenAI(temperature=0.0, openai_api_key=os.getenv("API_KEY"))

    _prompt_template = ChatPromptTemplate.from_template(_prompt)

    print(_prompt_template.messages[0].prompt)
    print('')


if __name__ == '__main__':
    driver()
