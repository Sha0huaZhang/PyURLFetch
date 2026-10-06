<div align="center">
    <img src="https://pyurlfetch.macwave.org/images/logo1.svg" alt="Logo" width="256" />
    <h1>PyURLFetch</h1>
</div>

# PyURLFetch

A library for convenient resumable downloads

**English** · [简体中文](./README.zh-Hans.md)

## Official Website
[pyurlfetch.macwave.org](https://pyurlfetch.macwave.org)

## Download

[pypi.org/project/PyURLFetch](https://pypi.org/project/PyURLFetch/)

## Requirements

- Python 3.8 or later
- `requests` and `urllib3`, installed automatically
- Optional: `rich` 12.0 or later, for the progress bar

## Why PyURLFetch?

**1. Real resuming.** The download is written to `dest.partial`. Call the same
function again with `resume=True` and it continues from where it stopped, using
an HTTP Range request.

**2. Control over the transfer.** Cap the speed with `limit_rate`, route through
a proxy with `proxy`, and skip certificate verification with `verify=False`.

**3. It stays out of your way.** It never prints, never calls `sys.exit` and
never prompts for input, so it is safe to use inside another program. Progress,
retries and errors all go through callbacks and exceptions.

## Install

```bash
pip3 install PyURLFetch              # core (requests + urllib3)
pip3 install "PyURLFetch[progress]"  # adds the rich progress bar
```

The distribution name is `PyURLFetch`; the module you import is `pyurlfetch`.

## Usage

```python
from pyurlfetch import download_file

path = download_file(
    "https://example.com/archive.tar.gz",
    "archive.tar.gz",
    resume=True,
    limit_rate="1M",
)
```

The parent directory of `dest` is created automatically, and the final
`pathlib.Path` is returned.

## Resuming

Interrupted downloads are resumed by calling the same function again:

```python
download_file(url, dest, resume=True)
```

- With `resume=True`, an existing `dest.partial` is continued with a Range
  request, so the bytes already downloaded are not fetched twice.
- If the server does not support ranges (it answers `200` instead of `206`), the
  download restarts from the beginning on its own.
- If the server answers `416`, the partial file is already complete and is simply
  renamed.
- With `resume=False` (the default), an existing `.partial` is overwritten.

## Rate Limiting

`limit_rate` accepts `"200K"`, `"1M"`, `"5M"` or a plain byte count; a value that
cannot be parsed means no limit.

```python
from pyurlfetch import parse_rate_limit, TokenBucket

parse_rate_limit("1M")    # 1048576.0
parse_rate_limit("junk")  # None

bucket = TokenBucket(1024 * 1024)  # 1 MiB/s
bucket.consume(8192)               # blocks until 8192 bytes are allowed
```

## Proxy and SSL

```python
download_file(url, dest, proxy="socks5://127.0.0.1:1080")
download_file(url, dest, verify=False)   # skips SSL verification
download_file(url, dest, timeout=60)     # no response within 60 seconds
```

## Progress

With `progress` left at its default, a `rich` progress bar is shown when `rich`
is installed and nothing is printed when it is not.

```python
download_file(url, dest)                      # auto
download_file(url, dest, progress=False)      # off
download_file(url, dest, display_name="wget") # label on the bar
```

To render your own, use the callback instead:

```python
download_file(url, dest, progress=False,
              on_progress=lambda done, total: print(f"{done}/{total}"))
```

## Retrying

A download never prompts. Retries are controlled either by `max_retries` or by
an `on_retry(attempt, error)` callback that returns whether to retry:

```python
download_file(url, dest, max_retries=3)

download_file(url, dest,
              on_retry=lambda attempt, error: input("retry? [y/N] ") == "y")
```

A failed download raises rather than exiting the process:

```python
from pyurlfetch import HTTPStatusError, NetworkError, UserAborted

try:
    download_file(url, dest, resume=True)
except HTTPStatusError as error:
    print(error.status_code, error.url)
except (NetworkError, UserAborted) as error:
    print("download failed:", error)
```

## Exceptions

```
PyURLFetchError
└── DownloadError
    ├── HTTPStatusError   # non-200/206 response; .status_code, .url
    ├── NetworkError      # connection failed or timed out
    └── UserAborted       # on_retry returned False
```

## API

```python
download_file(
    url,
    dest,
    *,
    resume=False,        # continue from dest.partial using an HTTP Range request
    limit_rate=None,     # bytes/s, or "200K" / "1M" / "5M"
    proxy=None,          # http://... or socks5://...
    verify=True,         # set False to skip SSL certificate verification
    timeout=30.0,        # seconds without a response
    chunk_size=8192,
    max_retries=None,    # extra attempts; None means do not retry
    on_retry=None,       # callback(attempt, error) -> bool
    progress=None,       # None = auto (rich if installed), False = off
    display_name=None,   # label shown on the progress bar
    on_progress=None,    # callback(downloaded, total)
)
```

## License

This project is licensed under the **MIT License**.
