from __future__ import annotations

import random
import time
from typing import Callable, Type, Tuple


def retry(
    exceptions: Tuple[Type[BaseException], ...],
    attempts: int = 3,
    base_delay: float = 0.25,
    max_delay: float = 2.0,
) -> Callable:
    """
    Decorator simples de retry com backoff exponencial + jitter.
    """
    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            delay = base_delay
            for i in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if i == attempts - 1:
                        raise
                    time.sleep(min(max_delay, delay + random.random() * 0.1))
                    delay *= 2
        return wrapper
    return decorator
