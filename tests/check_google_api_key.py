import os

import dotenv
from google import genai


def main() -> None:
    dotenv.load_dotenv(dotenv_path=".env", override=True)
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model=os.getenv("GOOGLE_MODEL_ANALYST", "gemini-2.5-flash"),
        contents="Antworte kurz auf Deutsch: API-Key funktioniert.",
    )
    print(response.text)


if __name__ == "__main__":
    main()
