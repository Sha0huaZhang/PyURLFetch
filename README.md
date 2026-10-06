# PyURLFetch
A Python library for implementing convenient resumable download functionality.

Extracted from MacWave's package download flow. It handles `.partial` files and
HTTP Range requests for resuming, optional rate limiting, proxies, skipping SSL
verification, and a `rich` progress bar.

## Install

```bash
pip3 install PyURLFetch              # core (requests + urllib3)
pip3 install "PyURLFetch[progress]"  # adds the rich progress bar
```

The import name is `pyurlfetch`:

```python
import pyurlfetch
```

To try the unreleased code instead, install from the repository:

```bash
pip3 install "git+https://github.com/Sha0huaZhang/PyURLFetch.git"
```

## Usage

```python
from pyurlfetch import download_file

download_file(
    "https://example.com/archive.tar.gz",
    "archive.tar.gz",
    resume=True,
    limit_rate="1M",
)
```

The download is written to `archive.tar.gz.partial` and renamed to the target
once complete, so an interrupted download can be resumed by calling the same
function again with `resume=True`.

Failures raise an exception instead of exiting the process:

```python
from pyurlfetch import HTTPStatusError, NetworkError, UserAborted

try:
    download_file(url, dest, resume=True)
except HTTPStatusError as error:
    print(error.status_code, error.url)
except (NetworkError, UserAborted) as error:
    print("download failed:", error)
```

### Retrying

`download_file` does not prompt interactively. Control retries either with
`max_retries` or with an `on_retry(attempt, error) -> bool` callback:

```python
download_file(url, dest, max_retries=3)

download_file(url, dest, on_retry=lambda attempt, error: input("retry? [y/N] ") == "y")
```
