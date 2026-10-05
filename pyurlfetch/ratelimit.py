#!/usr/bin/env python3

# ratelimit.py
# 限速：把 "200K"/"1M"/"5M" 之类的字符串解析成字节/秒，并提供令牌桶。

import time

_MULTIPLIERS = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}

# 与原实现一致：单次可攒的令牌上限为 8192 字节（即一个分片）。
DEFAULT_BURST = 8192


def parse_rate_limit(rate_str):
    """把 "200K"/"1M"/"5M"/"1048576" 解析为字节/秒，无法解析时返回 None。"""
    if not isinstance(rate_str, str):
        return None
    rate_str = rate_str.upper().strip()
    if not rate_str:
        return None
    try:
        if rate_str[-1] in _MULTIPLIERS:
            return float(rate_str[:-1]) * _MULTIPLIERS[rate_str[-1]]
        return float(rate_str)
    except ValueError:
        return None


class TokenBucket:
    """按字节/秒限制写入速度的令牌桶。"""

    def __init__(self, rate, burst=DEFAULT_BURST):
        if rate <= 0:
            raise ValueError("rate must be greater than 0")
        self.rate = float(rate)
        self.burst = float(burst)
        self._tokens = 0.0
        self._last = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        self._tokens += (now - self._last) * self.rate
        self._last = now
        if self._tokens > self.burst:
            self._tokens = self.burst

    def consume(self, amount):
        """阻塞到允许写入 amount 字节为止，然后扣除对应令牌。"""
        self._refill()
        if self._tokens < amount:
            time.sleep((amount - self._tokens) / self.rate)
            self._refill()
        self._tokens -= amount
