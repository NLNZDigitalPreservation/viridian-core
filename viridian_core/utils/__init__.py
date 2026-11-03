"""Compatibility package exposing `common` modules under `viridian_core`.

This package points its module search path at the sibling `common` package so
consumers can import modules such as `viridian_core.shared.config`.
"""

from pathlib import Path

# Make `viridian_core.*` resolve to modules located in `common/`.
__path__ = [str(Path(__file__).resolve().parent.parent / "common")]
