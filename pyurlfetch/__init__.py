#!/usr/bin/env python3

# __init__.py
# PyURLFetch：可恢复（断点续传）下载库的公开接口。

from .downloader import download_file
from .exceptions import (
    DownloadError,
    HTTPStatusError,
    NetworkError,
    PyURLFetchError,
    UserAborted,
)
from .ratelimit import TokenBucket, parse_rate_limit

__version__ = "0.1.0"

__all__ = [
    "download_file",
    "PyURLFetchError",
    "DownloadError",
    "HTTPStatusError",
    "NetworkError",
    "UserAborted",
    "TokenBucket",
    "parse_rate_limit",
    "__version__",
]
