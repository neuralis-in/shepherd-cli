import os
import sys
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from langfuse.openai import OpenAI  # Langfuse drop-in replacement for OpenAI


def make_client() -> OpenAI:
    """Create an OpenAI client wrapped with Langfuse tracing.

    Requires these environment variables:
    - OPENAI_API_KEY: Your OpenAI API key
    - LANGFUSE_PUBLIC_KEY: Your Langfuse public key
    - LANGFUSE_SECRET_KEY: Your Langfuse secret key
    - LANGFUSE_HOST (optional): Langfuse host URL (defaults to cloud.langfuse.com)
    """
    # Load env from nearest .env (search upwards from CWD)
    load_dotenv(find_dotenv(usecwd=True))

    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Missing OPENAI_API_KEY in environment (.env)")
        sys.exit(1)

    # Langfuse credentials are read automatically from environment variables:
    # LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
    return OpenAI(api_key=api_key)


def default_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
