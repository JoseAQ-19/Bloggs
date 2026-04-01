import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
token = os.getenv("MODELS_TOKEN_CEU")
client = OpenAI(api_key=token, base_url="https://models.inference.ai.azure.com")

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ],
        temperature=0.7,
        max_tokens=4096,
        timeout=180
    )
    print(response.choices[0].message.content)
except Exception as e:
    print("API ERROR:", e)
