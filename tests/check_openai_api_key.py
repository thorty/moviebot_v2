import os

from openai import OpenAI


def main() -> None:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL_FAST", "gpt-5.4-mini"),
        input="Reply with OK.",
        max_output_tokens=20,
    )
    print(response.output_text)


if __name__ == "__main__":
    main()
