"""Test TypeSafe key formats without printing secrets."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from typesafe_sdk import AsyncTypeSafeClient, Choice


def _variants(raw: str) -> list[str]:
    key = raw.strip().strip('"').strip("'")
    variants = [key]
    if key.startswith("apikey_") and not key.startswith("ts-"):
        variants.append(f"ts-{key}")
    if key.startswith("ts-apikey_"):
        variants.append(key.removeprefix("ts-"))
    return list(dict.fromkeys(variants))


async def _try_key(api_key: str) -> bool:
    try:
        async with AsyncTypeSafeClient(model="jev-1.13.0", api_key=api_key) as client:
            await client.system_one(
                "charged twice for subscription",
                {
                    "category": Choice(
                        instructions="classify",
                        criteria={"billing": "payments", "technical": "bugs"},
                    )
                },
            )
        return True
    except Exception:
        return False


async def main() -> int:
    raw = os.getenv("TYPESAFE_API_KEY", "")
    if not raw:
        print("FAIL: TYPESAFE_API_KEY missing")
        return 1

    for idx, variant in enumerate(_variants(raw), start=1):
        ok = await _try_key(variant)
        print(f"variant_{idx}: {'OK' if ok else 'FAIL'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
