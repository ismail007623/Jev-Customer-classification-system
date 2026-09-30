"""Test OpenAI key without printing secrets."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


async def main() -> None:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        text = response.choices[0].message.content or ""
        print("openai:", "OK" if text else "EMPTY")
    except Exception as exc:
        print("openai: FAIL", type(exc).__name__, str(exc)[:200])


if __name__ == "__main__":
    asyncio.run(main())
