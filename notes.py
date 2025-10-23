from openai import OpenAI
client = OpenAI(api_key="123", base_url="http://ailadgx-gpu40.utsarr.net:2530/v1")
response = client.chat.completions.create(
    model="Qwen/Qwen3-VL-8B-Instruct-FP8",
    messages=[{"role": "user", "content": "Write me an essay that is 200 tokens long"}]
)
content = response.choices[0].message.content

# Remove everything between <think> and </think>
import re
clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
print(clean_content)

'''
The 8B struggles with mixed use, the MOE didn't.
'''


