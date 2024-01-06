import requests

headers = {
    'Content-Type': 'text/plain'
}

url = "https://www.llama2.ai/api"
prompt_changed = 'how are you?'

payload = {"prompt":f"<s>[INST] {prompt_changed} [/INST]\n",
    "model":"meta/llama-2-70b-chat",
    "systemPrompt":"You are a helpful assistant.",
    "temperature":0.75,
    "topP":0.9,
    "maxTokens":800,
    "image":'null',
    "audio":'null'}

payload ="{\"prompt\":\"[INST] Hello [/INST]\\n\",\"model\":\"meta/llama-2-70b-chat\",\"systemPrompt\":\"You are a helpful assistant.\",\"temperature\":0.75,\"topP\":0.9,\"maxTokens\":200,\"image\":null,\"audio\":null}"
payload = payload.replace("Hello",  prompt_changed)

response = requests.request("POST", url, headers=headers, data=payload).text

print(response)
# def chat(chat_history):
#     api_url = 'YOUR_API_URL_HERE'
#     json_body = {
#         "inputs": [chat_history],
#         "parameters": {"max_new_tokens":256, "top_p":0.9, "temperature":0.6}
#     }
#     r = requests.post(api_url, json=json_body)
#     return r.json()[0]['generation']

# chat_history = [{"role": "system", "content": "You are a helpful assistant."}]
# while True:
#     print('\nPrompt: ')
#     query = input('')
#     if query == 'quit':
#         exit()
#     else:
#         chat_history.append({"role": "user", "content": query})
#         chat_message = chat(chat_history)
#         print(chat_message['content'])
#         chat_history.append(chat_message)