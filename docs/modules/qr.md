# QR 二维码

QR Code 生成与终端渲染 -- 零依赖，仅标准库，Python 3.10+。

## 概述

QR 模块提供完整的 QR Code 编码器，符合 **QR Code Model 2** 规范（ISO/IEC 18004）。支持所有版本（尺寸）从 1 到 40，全部 4 种纠错等级，以及 4 种字符编码模式。模块还包含一个便捷函数，可以使用 Unicode 半块字符直接在终端中渲染二维码。

基于 [Project Nayuki 的 QR Code 生成器库](https://www.nayuki.io/page/qr-code-generator-library)（MIT 许可证），zerodep 额外添加了终端渲染功能。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `qr.py` | 完整的 QR Code 编码器 + 终端渲染 | 无（仅标准库） |

## 如何在你的项目中使用

将单个文件复制到你的项目中：

```bash
cp qr/qr.py your_project/
```

然后导入所需的类：

```python
from qr import QrCode, QrSegment, print_qr_terminal
```

## API 参考

### `QrCode` 类

表示一个 QR Code 符号的核心类 -- 一个不可变的深色和浅色模块方阵。

#### 静态工厂函数（高级 API）

##### `QrCode.encode_text(text, ecl)`

返回表示给定 Unicode 文本字符串的 QR Code，使用指定的纠错等级。自动选择能容纳数据的最小版本，并自动选择最优编码模式（数字、字母数字或字节）。

```python
@staticmethod
def encode_text(text: str, ecl: QrCode.Ecc) -> QrCode
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 待编码的 Unicode 文本字符串。在 `Ecc.LOW` 下，738 个或更少的码位保证成功。 |
| `ecl` | `QrCode.Ecc` | 最低纠错等级。如果不增加版本即可提升纠错等级，会自动提升。 |

**返回值：** `QrCode` -- 生成的 QR Code 对象。

**异常：** `DataTooLongError` -- 如果文本过长，无法放入任何 QR Code 版本。

---

##### `QrCode.encode_binary(data, ecl)`

返回表示给定二进制数据的 QR Code，使用指定的纠错等级。始终使用字节段模式编码，最大支持 2953 字节。

```python
@staticmethod
def encode_binary(data: bytes | Sequence[int], ecl: QrCode.Ecc) -> QrCode
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `data` | `bytes \| Sequence[int]` | 待编码的二进制数据。最大 2953 字节。 |
| `ecl` | `QrCode.Ecc` | 最低纠错等级。 |

**返回值：** `QrCode` -- 生成的 QR Code 对象。

**异常：** `DataTooLongError` -- 如果数据过长。

---

#### 静态工厂函数（中级 API）

##### `QrCode.encode_segments(segs, ecl, ...)`

返回使用给定编码参数表示给定段列表的 QR Code。这个中级 API 允许自定义段序列，可以在不同模式之间切换（如字母数字和字节），以更少的空间编码文本。

```python
@staticmethod
def encode_segments(
    segs: Sequence[QrSegment],
    ecl: QrCode.Ecc,
    minversion: int = 1,
    maxversion: int = 40,
    mask: int = -1,
    boostecl: bool = True,
) -> QrCode
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `segs` | `Sequence[QrSegment]` | *（必填）* | 待编码的段列表。 |
| `ecl` | `QrCode.Ecc` | *（必填）* | 最低纠错等级。 |
| `minversion` | `int` | `1` | 最小 QR Code 版本（1--40）。 |
| `maxversion` | `int` | `40` | 最大 QR Code 版本（1--40）。 |
| `mask` | `int` | `-1` | 掩码图案（0--7），-1 表示自动选择。 |
| `boostecl` | `bool` | `True` | 是否在不增加版本的前提下自动提升纠错等级。 |

**返回值：** `QrCode` -- 生成的 QR Code 对象。

**异常：** `DataTooLongError` -- 如果段数据无法放入指定的版本范围内。

---

#### 访问器方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_version()` | `int` | 版本号，范围 [1, 40]。 |
| `get_size()` | `int` | 模块尺寸，范围 [21, 177]。等于 `version * 4 + 17`。 |
| `get_error_correction_level()` | `QrCode.Ecc` | 使用的纠错等级。 |
| `get_mask()` | `int` | 掩码图案索引，范围 [0, 7]。 |
| `get_module(x, y)` | `bool` | (x, y) 处模块的颜色。`True` = 深色，`False` = 浅色。坐标越界时返回 `False`。 |

---

### `QrCode.Ecc` 类

纠错等级枚举。实例不可变。

| 常量 | 容错率 | 说明 |
|------|--------|------|
| `QrCode.Ecc.LOW` | ~7% | 最低冗余，生成最小的二维码 |
| `QrCode.Ecc.MEDIUM` | ~15% | 平衡选择，适用于大多数场景 |
| `QrCode.Ecc.QUARTILE` | ~25% | 较高冗余 |
| `QrCode.Ecc.HIGH` | ~30% | 最高容错，生成最大的二维码 |

---

### `QrSegment` 类

QR Code 符号中的一个字符/二进制/控制数据段。不可变。

#### 静态工厂函数

| 方法 | 说明 |
|------|------|
| `QrSegment.make_bytes(data)` | 从二进制数据（`bytes` 或 `Sequence[int]`）创建段。 |
| `QrSegment.make_numeric(digits)` | 从十进制数字字符串创建段。 |
| `QrSegment.make_alphanumeric(text)` | 从字母数字文本创建段（0--9、A--Z 大写、空格、`$%*+-./:` ）。 |
| `QrSegment.make_segments(text)` | 自动为给定文本选择最高效的编码方式。 |
| `QrSegment.make_eci(assignval)` | 创建扩展通道解释（ECI）指示段。 |

#### 验证函数

| 方法 | 说明 |
|------|------|
| `QrSegment.is_numeric(text)` | 字符串是否可以用数字模式编码，是则返回 `True`。 |
| `QrSegment.is_alphanumeric(text)` | 字符串是否可以用字母数字模式编码，是则返回 `True`。 |

#### 访问器方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_mode()` | `QrSegment.Mode` | 此段的编码模式。 |
| `get_num_chars()` | `int` | 此段中的字符数。 |
| `get_data()` | `list[int]` | 段的比特数据的副本。 |

---

### `QrSegment.Mode` 类

编码模式枚举。

| 常量 | 说明 |
|------|------|
| `QrSegment.Mode.NUMERIC` | 编码十进制数字（0--9）。 |
| `QrSegment.Mode.ALPHANUMERIC` | 编码数字、大写字母和部分符号。 |
| `QrSegment.Mode.BYTE` | 编码任意二进制数据。 |
| `QrSegment.Mode.KANJI` | 编码日文汉字字符（Shift JIS）。 |
| `QrSegment.Mode.ECI` | 扩展通道解释指示符。 |

---

### `print_qr_terminal(text)`

将文本编码为 QR Code 并使用 Unicode 半块字符打印到终端。使用 `Ecc.LOW` 以获得最紧凑的输出。

```python
def print_qr_terminal(text: str) -> None
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 待编码为 QR Code 的文本。 |

---

### `DataTooLongError`

当提供的数据无法放入任何 QR Code 版本时抛出的异常。是 `ValueError` 的子类。

## 用法示例

### 快速终端二维码

```python
from qr import print_qr_terminal

print_qr_terminal("https://example.com")
```

### 指定纠错等级编码文本

```python
from qr import QrCode

qr = QrCode.encode_text("Hello, World!", QrCode.Ecc.MEDIUM)
print(f"版本: {qr.get_version()}")
print(f"尺寸: {qr.get_size()}x{qr.get_size()} 模块")
print(f"纠错等级: {qr.get_error_correction_level().ordinal}")
```

### 编码二进制数据

```python
from qr import QrCode

data = bytes(range(256))
qr = QrCode.encode_binary(data, QrCode.Ecc.LOW)
print(f"版本: {qr.get_version()}")
```

### 自定义段实现混合编码

```python
from qr import QrCode, QrSegment

# 混合数字段和字母数字段以获得更好的压缩率
seg1 = QrSegment.make_numeric("314159265")
seg2 = QrSegment.make_alphanumeric("HELLO WORLD")

qr = QrCode.encode_segments([seg1, seg2], QrCode.Ecc.MEDIUM)
```

### 限制版本范围

```python
from qr import QrCode, DataTooLongError

try:
    # 仅允许版本 1--5（小尺寸二维码）
    qr = QrCode.encode_segments(
        QrSegment.make_segments("Hello"),
        QrCode.Ecc.HIGH,
        minversion=1,
        maxversion=5,
    )
except DataTooLongError:
    print("数据过长，无法放入请求的版本范围")
```

### 导出为 SVG（手动方式）

```python
from qr import QrCode

qr = QrCode.encode_text("https://example.com", QrCode.Ecc.MEDIUM)
size = qr.get_size()
border = 4

parts = []
for y in range(size):
    for x in range(size):
        if qr.get_module(x, y):
            parts.append(f"M{x + border},{y + border}h1v1h-1z")

svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {size + border * 2} {size + border * 2}">
  <rect width="100%" height="100%" fill="white"/>
  <path d="{''.join(parts)}" fill="black"/>
</svg>"""

with open("qr.svg", "w") as f:
    f.write(svg)
```

## 注意事项

!!! info "版本范围"
    QR Code 版本从 **1**（21x21 模块）到 **40**（177x177 模块）。每个版本在每一边增加 4 个模块。库会自动选择能容纳数据的最小版本。

!!! info "自动模式选择"
    使用 `encode_text()` 或 `QrSegment.make_segments()` 时，库会自动选择最高效的编码模式：

    - **数字模式** -- 仅包含数字（0--9）的字符串
    - **字母数字模式** -- 包含数字、大写字母和少量符号的字符串
    - **字节模式** -- 其他所有字符串（编码为 UTF-8）

- **最大数据容量**（`Ecc.LOW` 下）：7,089 个数字字符、4,296 个字母数字字符或 2,953 字节。
- **掩码选择：** 自动掩码选择（`mask=-1`）会尝试所有 8 种掩码并选择罚分最低的一种。对于大型二维码，这可能会比较慢。如果追求速度，可以指定掩码（0--7）。
- **不可变性：** `QrCode` 和 `QrSegment` 实例在构造后不可变。模块数据通过 `get_module()` 只读访问。
- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型语法）。

## 性能测试

**参考库：** [`qrcode`](https://pypi.org/project/qrcode/)（纯 Python）

两个实现都是纯 Python，因此对比的是两个解释执行的代码库之间的效率差异。

### 测试输入

| 标签 | 内容 | 长度 |
|------|------|------|
| 短文本 | `"Hello"` | 5 字符 |
| URL | `"https://example.com/path?query=value&foo=bar"` | 46 字符 |
| 长文本 | `"A" * 200` | 200 字符 |

### 编码性能（均值）

| 输入 | zerodep（`qr.py`） | `qrcode` 库 | 倍率 |
|------|---------------------|-------------|------|
| 短文本（5 字符） | 3.3 ms | 1.6 ms | 慢 2.1 倍 |
| URL（46 字符） | 8.7 ms | 4.5 ms | 慢 1.9 倍 |
| 长文本（200 字符） | 18.3 ms | 10.5 ms | 慢 1.7 倍 |

### 要点总结

- **zerodep**（`qr.py`）比 `qrcode` 库**慢约 2 倍**。随着输入变长，差距逐渐缩小（从 2.1 倍到 1.7 倍）。
- 两者都是纯 Python 实现。与 AES 可以通过 ctypes 调用系统 `libcrypto` 不同，QR Code 生成没有跨平台预装的 C 库可供利用。zerodep 优先保证**正确性**和**零依赖**，而非追求极致速度。
- 对于大多数应用场景，两者都足够快——QR Code 生成很少成为性能瓶颈。即使最慢的情况（200 字符）也在 20 ms 内完成。

自行运行基准测试：

```bash
pytest qr/test_qr_benchmark.py --benchmark-only -v
```
