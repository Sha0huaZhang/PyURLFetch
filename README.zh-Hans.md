# PyURLFetch
便于使用的 Python 下载库。

该库抽取自 MacWave 的软件包下载流程，负责处理 `.partial` 分片文件与用于续传的
HTTP Range 请求，以及可选的限速、代理、跳过 SSL 校验和 `rich` 进度条。

[English](./README.md) · **简体中文**

## 网页
pyurlfetch.macwave.org  
## 安装

```bash
pip3 install PyURLFetch              # 基础版（requests + urllib3）
pip3 install "PyURLFetch[progress]"  # 额外安装 rich 进度条
```

导入名为 `pyurlfetch`：

```python
import pyurlfetch
```

想改用未发布的最新代码，可从仓库安装：

```bash
pip3 install "git+https://github.com/Sha0huaZhang/PyURLFetch.git"
```

## 使用方法

```python
from pyurlfetch import download_file

download_file(
    "https://example.com/archive.tar.gz",
    "archive.tar.gz",
    resume=True,
    limit_rate="1M",
)
```

下载内容先写入 `archive.tar.gz.partial`，完成后再改名为目标文件；因此中断的下载
只需再次以 `resume=True` 调用同一个函数即可续传。

失败会抛出异常，而不是结束进程：

```python
from pyurlfetch import HTTPStatusError, NetworkError, UserAborted

try:
    download_file(url, dest, resume=True)
except HTTPStatusError as error:
    print(error.status_code, error.url)
except (NetworkError, UserAborted) as error:
    print("download failed:", error)
```

### 重试

`download_file` 不会弹出交互提示。重试由 `max_retries` 或
`on_retry(attempt, error) -> bool` 回调控制：

```python
download_file(url, dest, max_retries=3)

download_file(url, dest, on_retry=lambda attempt, error: input("retry? [y/N] ") == "y")
```
