import os
import openai
from dotenv import load_dotenv
load_dotenv()

openai.organization = os.getenv("ORG")
openai.api_key = os.getenv("API_KEY")
model_id = "gpt-3.5-turbo"
# import dotenv


def chatgpt_conversation():
    response = openai.ChatCompletion.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "add required dependencies on top of the code."},
            {"role": "user", "content": "Generate a python test case that use torch.rand() API."},
            {"role": "user", "content": "Do not explain, just create a runnable python code."},
            {"role": "system", "content": "Generate malformed inputs also for the API."}
        ]
    )

    return response


conversations = chatgpt_conversation()
print(conversations.choices[0].message.content)
