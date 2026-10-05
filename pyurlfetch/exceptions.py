#!/usr/bin/env python3

# exceptions.py
# PyURLFetch 的异常层级：库只抛异常，不直接结束进程。

class PyURLFetchError(Exception):
    """PyURLFetch 所有异常的基类。"""


class DownloadError(PyURLFetchError):
    """下载未能完成。"""


class HTTPStatusError(DownloadError):
    """服务端返回了 200/206 之外的状态码。

    404 与其它状态码共用这一个异常，调用方用 status_code 区分。
    """

    def __init__(self, status_code, url=None, message=None):
        self.status_code = status_code
        self.url = url
        if message is None:
            if status_code == 404:
                message = f"HTTP 404 - the URL or file does not exist: {url}"
            else:
                message = f"HTTP {status_code}"
                if url:
                    message += f" for {url}"
        super().__init__(message)


class NetworkError(DownloadError):
    """连接失败或超时，且不再重试。"""


class UserAborted(DownloadError):
    """重试询问中调用方选择放弃。"""
