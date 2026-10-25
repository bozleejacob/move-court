import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-6-luna"

# Keys rule: check .env in this folder first, then one level above.
_here = Path(__file__).resolve().parent
_local_env = _here / ".env"
_parent_env = _here.parent / ".env"

if _local_env.exists():
    load_dotenv(_local_env)
elif _parent_env.exists():
    load_dotenv(_parent_env)

_api_key = os.environ.get("PORTKEY_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError(
        "No PORTKEY_API_KEY or OPENAI_API_KEY found in .env (checked this folder "
        "and one level above)."
    )

_base_url = "https://api.portkey.ai/v1" if os.environ.get("PORTKEY_API_KEY") else None

client = OpenAI(api_key=_api_key, base_url=_base_url) if _base_url else OpenAI(api_key=_api_key)


class UsageTracker:
    """Accumulates token usage across every LLM call in a run, for the tokenomics report."""

    def __init__(self):
        self.calls = []

    def record(self, label, usage):
        self.calls.append(
            {
                "label": label,
                "input_tokens": getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", 0),
            }
        )

    @property
    def total_input(self):
        return sum(c["input_tokens"] for c in self.calls)

    @property
    def total_output(self):
        return sum(c["output_tokens"] for c in self.calls)

    def as_rows(self):
        return self.calls
