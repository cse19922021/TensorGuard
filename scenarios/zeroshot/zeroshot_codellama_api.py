
import replicate, subprocess

# subprocess.call(['export REPLICATE_API_TOKEN=r8_8taKlPQzi3Liw2179bZKZZE7pbRlfS50dSisN'], shell=True)
replicate = replicate.Client(api_token='r8_8taKlPQzi3Liw2179bZKZZE7pbRlfS50dSisN')
output = replicate.run(
    "meta/codellama-7b-python:d9bd1215ec38c8730425c2696940090b014fd46c1007139bb023cef44c1f113c",
    input={"prompt": "Hi, I am hungry."}
)

for item in output:
    # https://replicate.com/meta/codellama-7b-python/api#output-schema
    print(item, end="")

