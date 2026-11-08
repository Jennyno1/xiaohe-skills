"""Host-path resolution for content-research scripts.

Runtime-specific host paths must not be written into the package. Each path is
resolved in this order (first hit wins):

1. an explicit environment variable (set by the installer / adapter for the
   target runtime),
2. the documented default below, which preserves current Hermes behaviour.

Keeping the defaults in ONE module means a runtime only has to export two
variables to relocate everything, instead of patching N scripts.
"""

import os
from pathlib import Path


def hermes_home() -> Path:
    """Host state directory (scripts, .env, caches). Default: ~/.hermes."""
    return Path(os.environ.get("CONTENT_RESEARCH_HERMES_HOME") or (Path.home() / ".hermes"))


def output_home() -> Path:
    """Generated-output root (reports, archives). Default: ~/hermes-output."""
    return Path(os.environ.get("CONTENT_RESEARCH_OUTPUT_HOME") or (Path.home() / "hermes-output"))
