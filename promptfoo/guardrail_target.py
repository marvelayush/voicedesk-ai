from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.promptfoo_harness import render_promptfoo_output


def call_api(prompt: str, options: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Promptfoo custom provider target for local guardrail regression tests."""
    del options, context
    return {"output": render_promptfoo_output(str(prompt))}
