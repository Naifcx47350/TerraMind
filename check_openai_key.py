"""Quick OpenAI API key check: lists models, sends a prompt, tries to display usage/quota details."""

import os
from pathlib import Path
from openai import OpenAI
import sys

ROOT = Path(__file__).resolve().parent


def load_api_key() -> str:
    # 1) Plain file in project root: OPENAI_API_KEY
    key_file = ROOT / "OPENAI_API_KEY"
    if key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
        if key:
            return key

    # 2) .env file (OPENAI_API_KEY=...)
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key

    raise SystemExit(
        "No API key found. Put your key in OPENAI_API_KEY (file) or .env as OPENAI_API_KEY=..."
    )


def try_get_credit_info(client):
    # Try to fetch credit info (not supported in openai package, so we do HTTP)
    import requests

    key = client.api_key
    headers = {
        "Authorization": f"Bearer {key}"
    }
    url = "https://api.openai.com/dashboard/billing/credit_grants"
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.ok:
            data = response.json()
            total = data.get("total_granted", None)
            used = data.get("total_used", None)
            remaining = data.get("total_available", None)
            print(
                f"\nBilling info: total granted: {total}, used: {used}, remaining: {remaining}")
        else:
            print(
                f"\nBilling info: Could not fetch (HTTP {response.status_code})")
    except Exception as e:
        print(f"\nBilling info: Could not fetch ({e})")


def main():
    client = OpenAI(api_key=load_api_key())

    # List available models
    try:
        response = client.models.list()
        model_names = [m.id for m in response.data]
        print("OK — OpenAI API key works.")
        print(
            f"Account can list models ({len(model_names)} models). Example models:")
        for m in model_names[:10]:
            print(" -", m)
    except Exception as e:
        print(f"Error listing models: {e}")
        sys.exit(1)

    # Send a simple prompt to the API
    try:
        # Pick a likely available chat model
        prefer = ["gpt-3.5-turbo", "gpt-3.5-turbo-1106",
                  "gpt-4", "gpt-4-turbo"]
        chat_model = next((m for m in prefer if m in model_names), None)
        if not chat_model:
            chat_model = model_names[0]
        print(f"\nSending a simple prompt to: {chat_model}")

        completion = client.chat.completions.create(
            model=chat_model,
            messages=[{"role": "user", "content": "Say hello!"}],
            max_tokens=16,
        )
        print("Sample response:",
              completion.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error sending prompt: {e}")

    # Try fetching credit info, if possible
    try:
        import requests
        try_get_credit_info(client)
    except ImportError:
        print("\nTo get billing info, install requests: pip install requests")


if __name__ == "__main__":
    main()
