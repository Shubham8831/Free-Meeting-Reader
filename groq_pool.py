# shared helper: pool of Groq API keys with automatic rotation on rate limits.
# put several keys in .env as GROQ_API_KEYS=key1,key2,key3  (GROQ_API_KEY still works too).
# when one key hits its rate/daily limit (HTTP 429), we transparently try the next.

import os
from dotenv import load_dotenv

try:
    from groq import RateLimitError
except Exception:  # very old SDKs
    RateLimitError = None

load_dotenv()


def get_keys() -> list[str]:
    """Return the ordered, de-duplicated list of Groq keys from .env."""
    keys: list[str] = []
    # primary: comma-separated list
    for k in os.getenv("GROQ_API_KEYS", "").split(","):
        k = k.strip()
        if k and k not in keys:
            keys.append(k)
    # fallback / compatibility: single key
    single = os.getenv("GROQ_API_KEY", "").strip()
    if single and single not in keys:
        keys.append(single)
    if not keys:
        raise RuntimeError("No Groq keys found. Set GROQ_API_KEYS or GROQ_API_KEY in .env")
    return keys


def _is_rate_limit(err: Exception) -> bool:
    """True if the error looks like a rate/quota limit (so we should try another key)."""
    if RateLimitError is not None and isinstance(err, RateLimitError):
        return True
    s = str(err).lower()
    return any(x in s for x in ("rate limit", "429", "quota", "too many requests"))


def run_with_rotation(call):
    """Run call(api_key). On a rate-limit error, retry with the next key.

    `call` is a function that takes one api_key string and does the Groq work.
    Raises the last rate-limit error only if EVERY key is exhausted; any other
    error is raised immediately.
    """
    keys = get_keys()
    last_err = None
    for key in keys:
        try:
            return call(key)
        except Exception as err:
            if _is_rate_limit(err):
                last_err = err
                continue  # this key is spent -> try the next one
            raise      # a real error (bad audio, auth, etc.) -> don't rotate
    raise last_err or RuntimeError("All Groq keys are rate-limited")
