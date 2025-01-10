"""Validation utilities."""

from typing import Mapping

import bioregistry

__all__ = [
    "validate_jsonld",
]


def validate_jsonld(obj: Mapping[str, Mapping[str, str]], strict: bool = True):
    if not isinstance(obj, dict):
        raise TypeError(f"data is not a dictionary")
    context = obj.get("@context")
    if context is None:
        raise TypeError(f"data is missing a @context field")
    if not isinstance(context, dict):
        raise TypeError(f"@context is not a dictionary: {context}")
    messages = []
    for prefix, uri_prefix in context.items():
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            messages.append(
                {
                    "prefix": prefix,
                    "error": "invalid",
                    "solution": None,
                    "level": "error",
                }
            )
        elif norm_prefix != prefix:
            messages.append(
                {
                    "prefix": prefix,
                    "error": "nonstandard",
                    "solution": f"Switch to standard prefix: {norm_prefix}",
                    "level": "error" if strict else "warning",
                }
            )
    return messages
