#!/usr/bin/env python3
"""
Small, non-breaking helper module to create a minimal diff for PR demos.
"""

__version__ = "0.1.0"


def get_demo_summary() -> str:
    """Return a short summary string for demo purposes."""
    return f"AI Code Review POC demo, version {__version__}"


