# Multipart

零依赖 multipart/form-data 解析器和编码器 -- 仅使用标准库，Python 3.10+。

> **替代:** `python-multipart`

## 概述

`multipart` 模块按照 RFC 7578 / RFC 2046 标准解析和编码 `multipart/form-data` 消息体。专为 HTTP 文件上传处理设计，无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `multipart/multipart.py` | Multipart 解析器和编码器 | 无（仅标准库） |

### 主要特性

- **边界分割解析** — 基于字节级分割的快速解析，具备健壮的边界检测
- **Content-Transfer-Encoding** — 支持 `base64` 和 `quoted-printable` 解码
- **RFC 5987 filename*** — 解码扩展文件名参数（如 `filename*=UTF-8''...`）
- **安全限制** — 可配置 `max_part_size`（10 MB）、`max_parts`（1000）、`max_header_size`（16 KB）
- **冻结 dataclass 输出** — 解析结果为不可变的 `Part` 对象，提供 `.text` 和 `.is_file` 辅助属性
- **编码支持** — 从字段和文件元组构建 multipart 消息体
- **约 590 行** — 单文件，无依赖

## 在项目中使用

```bash
cp multipart/multipart.py your_project/
```

```python
from multipart import parse_multipart, encode_multipart, Part
```

## 使用示例

### 解析 Multipart 消息体

```python
from multipart import parse_multipart

body = b"--boundary\r\nContent-Disposition: form-data; name=\"field1\"\r\n\r\nvalue1\r\n--boundary--\r\n"
parts = parse_multipart(body, "multipart/form-data; boundary=boundary")

for part in parts:
    print(part.name, part.text)  # "field1" "value1"
```

### 编码字段和文件

```python
from multipart import encode_multipart

body, content_type = encode_multipart(
    fields={"username": "alice", "bio": "Hello world"},
    files={"avatar": ("photo.png", b"\x89PNG...", "image/png")},
)
# content_type: "multipart/form-data; boundary=..."
# body: 可直接作为 HTTP 请求体发送
```

### 文件上传字段

```python
from multipart import encode_multipart

# 文件可以用多种格式指定：
files = {
    "doc": b"raw bytes",                              # 自动文件名，octet-stream
    "report": ("report.pdf", pdf_bytes),               # 指定文件名
    "image": ("photo.jpg", jpg_bytes, "image/jpeg"),   # 指定文件名和 MIME 类型
}
body, content_type = encode_multipart(files=files)
```

### 往返编解码

```python
from multipart import encode_multipart, parse_multipart

# 编码
body, ct = encode_multipart(
    fields={"name": "Alice"},
    files={"doc": ("readme.txt", b"Hello!", "text/plain")},
)

# 解析回来
parts = parse_multipart(body, ct)
for part in parts:
    if part.is_file:
        print(f"文件: {part.filename}, 大小: {len(part.data)}")
    else:
        print(f"字段: {part.name} = {part.text}")
```

### 安全限制

```python
from multipart import parse_multipart

# 限制每个 part 最大 1 MB，最多 10 个 part
parts = parse_multipart(body, content_type, max_part_size=1_000_000, max_parts=10)

# 禁用限制（不建议用于不可信输入）
parts = parse_multipart(body, content_type, max_part_size=0, max_parts=0)
```

### 提取边界

```python
from multipart import extract_boundary

boundary = extract_boundary("multipart/form-data; boundary=abc123")
print(boundary)  # "abc123"

# 也支持带引号的边界
boundary = extract_boundary('multipart/form-data; boundary="my-boundary"')
print(boundary)  # "my-boundary"
```

## API 参考

### `parse_multipart(body, content_type, *, max_part_size=10MB, max_parts=1000)`

| 参数 | 类型 | 说明 |
|------|------|------|
| `body` | `bytes` | 原始请求体 |
| `content_type` | `str` | 完整 Content-Type 头或裸边界字符串 |
| `max_part_size` | `int` | 每个 part 的最大字节数（0 表示禁用） |
| `max_parts` | `int` | 最大 part 数量（0 表示禁用） |

返回 `list[Part]`。

### `encode_multipart(fields=None, files=None, *, boundary=None)`

| 参数 | 类型 | 说明 |
|------|------|------|
| `fields` | `dict \| list[tuple]` | 文本表单字段 |
| `files` | `dict \| list[tuple]` | 文件上传（格式见上文） |
| `boundary` | `str \| None` | 自定义边界（None 时自动生成） |

返回 `(body_bytes, content_type_header)`。

### `extract_boundary(content_type)`

从 Content-Type 头中提取边界字符串。返回字符串。

### `Part`（冻结 dataclass）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 表单字段名 |
| `data` | `bytes` | 原始内容字节 |
| `filename` | `str \| None` | 原始文件名（文本字段为 None） |
| `content_type` | `str` | MIME 类型（默认：`"text/plain"`） |
| `headers` | `dict[str, str]` | 所有 MIME 头（键名小写） |

属性：

- `.text` — 使用 content_type 中的 charset（或 UTF-8）将 data 解码为文本
- `.is_file` — 如果 part 有文件名则为 True

### 异常

| 异常 | 说明 |
|------|------|
| `MultipartError` | 基础异常 |
| `MultipartParseError` | 输入格式错误、缺少边界、超出限制 |
| `MultipartEncodeError` | 编码参数无效 |

## 注意事项

!!! info "RFC 合规性"
    实现 RFC 7578（multipart/form-data）和 RFC 2046（MIME multipart）。处理边界情况如前导/尾部内容、缺少最终边界、CRLF/LF 规范化。

!!! tip "Content-Transfer-Encoding"
    带有 `Content-Transfer-Encoding: base64` 或 `quoted-printable` 的 part 会自动解码。这在 HTTP 中较少见，但在邮件 MIME 中很常见。

!!! warning "内存"
    解析器将整个消息体加载到内存中。对于非常大的文件上传，请考虑使用流式解析器。

- **Python 版本**：需要 Python 3.10+。
- **性能**：解析速度比 python-multipart 快 1.4-4 倍。详见下方性能测试。

## 性能测试

详见 [Multipart 性能测试](../benchmarks/multipart.md)。
