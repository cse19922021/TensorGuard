

import tiktoken


def get_token_count(string):

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    num_tokens = len(encoding.encode(string))

    return num_tokens


prompt = ''' prompt '''

print(get_token_count(prompt))
