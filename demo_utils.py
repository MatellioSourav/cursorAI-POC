#!/usr/bin/env python3
"""
Small utility helpers for demo purposes. Pure functions, no side effects.
"""

from typing import Iterable, List

__all__ = ["safe_multiply", "filter_even"]


def safe_multiply(a: int | float, b: int | float) -> int | float:
    """Multiply two numbers with explicit types for readability."""
    return a * b


def filter_even(values: Iterable[int]) -> List[int]:
    """Return only even integers from the provided iterable."""
    return [v for v in values if isinstance(v, int) and v % 2 == 0]


