import os, getpass
import dotenv

# get environment variables for OpenAI and LangSmith
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

def _load_dotenv():
    """Load environment variables from a .env file."""
    dotenv.load_dotenv()

def enable_langsmith():
    """Set up environment variables for OpenAI and LangSmith."""
    #_set_env("OPENAI_API_KEY")
    _set_env("LANGSMITH_API_KEY")
    # set langsmith tracing
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = "moviebot"

