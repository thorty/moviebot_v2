import os
import openai
from openai import OpenAI
import dotenv

dotenv.load_dotenv(dotenv_path=".env", override=True)

print("OpenAI version: ",openai.__version__)
client = OpenAI(
    api_key=os.getenv('TSYSTEMS_API_KEY'),
    base_url=os.getenv('TSYSTEMS_BASE_URL'),
)

print("==========Available models==========")
models = client.models.list()
for model in models.data:
  print(model.id)