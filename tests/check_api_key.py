import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def test_GPT4omini():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=256,
    )
    response = llm.invoke([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "How do I make a chat completion request?"}
    ])
    print(response.content)


def test_GPT41():
    llm = ChatOpenAI(
        model="gpt-4.1",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1,
        max_tokens=256,
    )
    response = llm.invoke([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "How do I make a chat completion request?"}
    ])
    print(response.content)


def main():
    print("...... starting main ......")
    test_GPT41()

if __name__ == "__main__":
    main()