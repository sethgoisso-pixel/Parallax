"""Thin wrapper around Nebius Token Factory (OpenAI-compatible API)."""
import os
import re

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def get_client():
    load_env()
    from openai import OpenAI
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        raise SystemExit("NEBIUS_API_KEY is not set. Copy .env.example to .env and fill it in.")
    return OpenAI(base_url=BASE_URL, api_key=key)


def strip_reasoning(text: str) -> str:
    """Remove <think>...</think> blocks some reasoning models emit."""
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def chat(client, model, system, user, temperature=0.9, max_tokens=300):
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return strip_reasoning(resp.choices[0].message.content)
