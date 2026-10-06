<div align="center">
    <img src="https://pyurlfetch.macwave.org/images/logo1.svg" alt="Logo" width="256" />
    <h1>PyURLFetch</h1>
</div>

# PyURLFetch

便于使用的断点续传下载库

[English](./README.md) · **简体中文**

## 官方网站
[pyurlfetch.macwave.org](https://pyurlfetch.macwave.org)

## 下载

[pypi.org/project/PyURLFetch](https://pypi.org/project/PyURLFetch/)

## 系统要求

- Python 3.8 或更高版本
- `requests` 与 `urllib3`（会自动安装）
- 可选：`rich` 12.0 或更高版本，用于显示进度条

## 为什么选择 PyURLFetch？

**1. 真正的断点续传。** 下载内容先写入 `dest.partial`；再次以 `resume=True`
调用同一个函数，就会用 HTTP Range 请求从断点处继续。

**2. 传输过程可控。** 用 `limit_rate` 限速，用 `proxy` 走代理，用
`verify=False` 跳过证书校验。

**3. 不干扰调用方。** 它不打印、不调用 `sys.exit`、也不会索要输入，因此在其它
程序内使用是安全的。进度、重试与错误分别通过回调和异常处理。

## 安装

```bash
pip3 install PyURLFetch              # 基础版（requests + urllib3）
pip3 install "PyURLFetch[progress]"  # 额外安装 rich 进度条
```

发行名是 `PyURLFetch`，而导入的模块名是 `pyurlfetch`。

## 使用方法

```python
from pyurlfetch import download_file

path = download_file(
    "https://example.com/archive.tar.gz",
    "archive.tar.gz",
    resume=True,
    limit_rate="1M",
)
```

`dest` 的父目录会自动创建，返回值是最终的 `pathlib.Path`。

## 断点续传

中断后再次调用同一个函数即可续传：

```python
download_file(url, dest, resume=True)
```

- 带 `resume=True` 时，已存在的 `dest.partial` 会通过 Range 请求续传，
  已下载的字节不会重复拉取。
- 若服务端不支持分段（返回 `200` 而非 `206`），会自动从头重新下载。
- 若服务端返回 `416`，说明分片文件已完整，直接改名即可。
- 带 `resume=False`（默认）时，已存在的 `.partial` 会被覆盖。

## 限速

`limit_rate` 接受 `"200K"`、`"1M"`、`"5M"`，也接受纯字节数；无法解析的取值
表示不限速。

```python
from pyurlfetch import parse_rate_limit, TokenBucket

parse_rate_limit("1M")    # 1048576.0
parse_rate_limit("junk")  # None

bucket = TokenBucket(1024 * 1024)  # 1 MiB/s
bucket.consume(8192)               # 阻塞至允许写入 8192 字节
```

## 代理与 SSL

```python
download_file(url, dest, proxy="socks5://127.0.0.1:1080")
download_file(url, dest, verify=False)   # 跳过 SSL 证书校验
download_file(url, dest, timeout=60)     # 60 秒内无响应即超时
```

## 进度显示

`progress` 保持默认时：装了 `rich` 就显示进度条，没装则什么都不打印。

```python
download_file(url, dest)                      # 自动
download_file(url, dest, progress=False)      # 关闭
download_file(url, dest, display_name="wget") # 进度条上的名称
```

想自己渲染，改用回调：

```python
download_file(url, dest, progress=False,
              on_progress=lambda done, total: print(f"{done}/{total}"))
```

## 重试

下载过程不会索要输入。重试由 `max_retries` 或 `on_retry(attempt, error)`
回调控制，回调返回是否重试：

```python
download_file(url, dest, max_retries=3)

download_file(url, dest,
              on_retry=lambda attempt, error: input("retry? [y/N] ") == "y")
```

下载失败会抛异常，而不是结束进程：

```python
from pyurlfetch import HTTPStatusError, NetworkError, UserAborted

try:
    download_file(url, dest, resume=True)
except HTTPStatusError as error:
    print(error.status_code, error.url)
except (NetworkError, UserAborted) as error:
    print("download failed:", error)
```

## 异常

```
PyURLFetchError
└── DownloadError
    ├── HTTPStatusError   # 响应码非 200/206；含 .status_code、.url
    ├── NetworkError      # 连接失败或超时
    └── UserAborted       # on_retry 返回 False
```

## API

```python
download_file(
    url,
    dest,
    *,
    resume=False,        # 通过 HTTP Range 请求从 dest.partial 续传
    limit_rate=None,     # 字节/秒，或 "200K" / "1M" / "5M"
    proxy=None,          # http://... 或 socks5://...
    verify=True,         # 设为 False 可跳过 SSL 证书校验
    timeout=30.0,        # 多少秒无响应即超时
    chunk_size=8192,
    max_retries=None,    # 额外重试次数；None 表示不重试
    on_retry=None,       # 回调 (attempt, error) -> bool
    progress=None,       # None = 自动（装了 rich 就显示），False = 关闭
    display_name=None,   # 进度条上显示的名称
    on_progress=None,    # 回调 (downloaded, total)
)
```

## 许可证

本项目使用 **MIT 许可证**。
