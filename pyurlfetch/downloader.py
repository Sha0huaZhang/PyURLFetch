#!/usr/bin/env python3

# downloader.py
# 断点续传下载核心，从 MacWave 的 pkg/pkginstaller.py 抽取：
# .partial 断点续传、进度条、限速、代理、跳过 SSL 校验、超时重试策略。

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional, Union

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

try:
    import urllib3
    from urllib3.exceptions import InsecureRequestWarning
except ImportError:  # pragma: no cover
    urllib3 = None
    InsecureRequestWarning = None

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
    )
    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    RICH_AVAILABLE = False

from .exceptions import DownloadError, HTTPStatusError, NetworkError, UserAborted
from .ratelimit import TokenBucket, parse_rate_limit

DEFAULT_TIMEOUT = 30.0
DEFAULT_CHUNK_SIZE = 8192

PathLike = Union[str, os.PathLike]
RetryCallback = Callable[[int, BaseException], bool]
ProgressCallback = Callable[[int, Optional[int]], None]

__all__ = ["download_file"]


def download_file(
    url,
    dest,
    *,
    resume=False,
    limit_rate=None,
    proxy=None,
    verify=True,
    timeout=DEFAULT_TIMEOUT,
    chunk_size=DEFAULT_CHUNK_SIZE,
    max_retries=None,
    on_retry=None,
    progress=None,
    display_name=None,
    on_progress=None,
):
    """下载 url 到 dest，返回最终路径。

    下载过程写在同目录的 ``dest.partial`` 里，成功后再改名为 dest；因此中断后
    以 ``resume=True`` 再次调用即可从 ``.partial`` 断点续传。服务端不支持续传
    （返回 200 而非 206）时会自动重新下载。

    limit_rate 可以是字节/秒的数字，也可以是 "200K"/"1M"/"5M" 字符串。

    失败时抛 DownloadError 的子类，不再直接退出进程。重试策略由两个参数决定：
    ``on_retry`` 存在时由它返回是否重试（放弃则抛 UserAborted），否则最多额外
    重试 ``max_retries`` 次（None 表示不重试）。

    ``progress`` 为 None 时自动探测 rich；``on_progress(downloaded, total)``
    每写入一个分片回调一次，可用来自己渲染进度。
    """
    dest = Path(dest)
    partial = dest.with_name(dest.name + ".partial")
    dest.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(limit_rate, str):
        limit_rate = parse_rate_limit(limit_rate)
    token_bucket = TokenBucket(limit_rate) if limit_rate else None

    request_kwargs = {"stream": True, "verify": verify, "timeout": timeout}
    if not verify and urllib3 is not None:
        urllib3.disable_warnings(InsecureRequestWarning)
    if proxy:
        request_kwargs["proxies"] = {"http": proxy, "https": proxy}

    use_bar = RICH_AVAILABLE if progress is None else bool(progress) and RICH_AVAILABLE
    task_description = display_name or dest.name

    attempt = 0
    while True:
        attempt += 1
        try:
            kwargs = dict(request_kwargs)

            # 每次尝试都重新读取 .partial 的现状：重试要基于最新偏移续传，
            # 否则会拿过期偏移做 append，写出损坏的文件。
            existing_size = 0
            mode = "wb"
            if resume and partial.exists():
                existing_size = partial.stat().st_size
                if existing_size > 0:
                    kwargs["headers"] = {"Range": f"bytes={existing_size}-"}
                    mode = "ab"

            response = requests.get(url, **kwargs)

            if response.status_code == 416:
                # 已有内容 >= 服务端资源，视为已经下完。
                if partial.exists():
                    partial.replace(dest)
                return dest
            if response.status_code not in (200, 206):
                raise HTTPStatusError(response.status_code, url)

            if response.status_code == 200 and existing_size > 0:
                # 服务端不支持 Range，从头重来。
                existing_size = 0
                mode = "wb"

            total_size = int(response.headers.get("content-length", 0))
            if existing_size > 0:
                total_size += existing_size

            _stream_response(
                response,
                partial,
                mode,
                existing_size,
                total_size,
                token_bucket,
                chunk_size,
                use_bar,
                task_description,
                on_progress,
            )

            partial.replace(dest)
            return dest

        except HTTPError as error:
            status_code = error.response.status_code if error.response is not None else 1
            raise HTTPStatusError(status_code, url, str(error)) from error
        except (ConnectionError, Timeout) as error:
            if _should_retry(on_retry, max_retries, attempt, error):
                continue
            if on_retry is not None:
                raise UserAborted(f"Download of {url} aborted by the caller.") from error
            raise NetworkError(f"Failed to download {url}: {error}") from error
        except DownloadError:
            raise
        except Exception as error:
            raise DownloadError(f"Failed to download {url}: {error}") from error


def _should_retry(on_retry, max_retries, attempt, error):
    if on_retry is not None:
        return bool(on_retry(attempt, error))
    if max_retries is not None:
        return attempt <= max_retries
    return False


def _stream_response(
    response,
    path,
    mode,
    existing_size,
    total_size,
    token_bucket,
    chunk_size,
    use_bar,
    description,
    on_progress,
):
    total = total_size or None
    downloaded = existing_size

    progress = None
    task_id = None
    if use_bar:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TimeRemainingColumn(),
            console=Console(),
        )
        progress.start()
        task_id = progress.add_task(description=description, total=total)
        if existing_size > 0:
            progress.update(task_id, advance=existing_size)

    try:
        with open(path, mode) as handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                if token_bucket is not None:
                    token_bucket.consume(len(chunk))
                handle.write(chunk)
                downloaded += len(chunk)
                if progress is not None:
                    progress.update(task_id, advance=len(chunk))
                if on_progress is not None:
                    on_progress(downloaded, total)
    finally:
        if progress is not None:
            progress.stop()
