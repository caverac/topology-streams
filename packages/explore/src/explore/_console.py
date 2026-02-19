"""Shared Rich console instances."""

from __future__ import annotations

from rich.console import Console

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)
