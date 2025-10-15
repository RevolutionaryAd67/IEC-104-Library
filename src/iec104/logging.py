"""Logging helpers providing structured context."""

from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from typing import Any, cast


class StructuredAdapter(logging.LoggerAdapter[logging.Logger]):
    """LoggerAdapter that preserves structured key-value context."""

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        extra_mapping = cast(Mapping[str, Any], getattr(self, "extra", {}))
        extra: dict[str, Any] = dict(extra_mapping)
        extras = kwargs.get("extra")
        if isinstance(extras, dict):
            extra.update(extras)
        mutable_kwargs: MutableMapping[str, Any] = dict(kwargs)
        mutable_kwargs["extra"] = extra
        return msg, mutable_kwargs


def get_logger(name: str, **context: Any) -> StructuredAdapter:
    """Return a structured logger adapter.

    Args:
        name: Logger name.
        **context: Additional structured context to attach to log records.

    Returns:
        A :class:`StructuredAdapter` bound to ``name``.
    """

    logger = logging.getLogger(name)
    return StructuredAdapter(logger, context)

