# PNG / BMP 图像编解码器

零依赖的 PNG 和 BMP 图像编解码器，附带矩阵压缩 API——仅使用标准库，Python 3.10+。

> **可替代:** `pypng`、`Pillow`（PNG/BMP 子集）

## 概述

`png` 模块仅使用 Python 标准库（`zlib`、`struct`）对 PNG 和 BMP 图像进行编码和解码。提供共享的 `Image` 数据类用于格式转换，以及 `matrix_to_png` / `png_to_matrix` API，利用 PNG 行滤波器实现高效的二维数值数据压缩。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `png/png.py` | PNG/BMP 编解码 + 矩阵 API | 无（仅标准库） |

### 核心特性

- **PNG 编解码** —— 通过标准库 `zlib` 编码和解码 PNG 图像
- **BMP 编解码** —— 编码和解码 24 位 RGB 及 32 位 RGBA 未压缩 BMP
- **颜色模式** —— 灰度（L）、灰度+透明度（LA）、RGB、RGBA
- **位深度** —— 每通道 8 和 16 位
- **全部 5 种行滤波器** —— None、Sub、Up、Average、Paeth，含自动选择启发式
- **tEXt 元数据** —— 读写辅助文本块
- **模式转换** —— 在 L/LA/RGB/RGBA 之间转换，支持亮度公式灰度化
- **矩阵 API** —— 将二维数值数据压缩为灰度 PNG，支持浮点数无损往返

## 在项目中使用

```bash
cp png/png.py your_project/
```

```python
from png import decode_png, encode_png, Image
```

## 使用示例

### 解码 PNG 文件

```python
from png import decode_png

img = decode_png("photo.png")
print(f"{img.width}x{img.height} {img.mode} {img.bit_depth}-bit")
print(f"像素数据: {len(img.data)} bytes")
```

### 创建并编码 PNG

```python
from png import encode_png, Image

# 创建 2x2 红色图像
pixels = bytes([255, 0, 0, 255, 0, 0, 0, 255, 0, 0, 255, 0])
img = Image(width=2, height=2, data=pixels, mode="RGB")

# 保存到文件
encode_png(img, "output.png")

# 或获取字节
png_bytes = encode_png(img)
```

### BMP 支持

```python
from png import decode_bmp, encode_bmp

# 解码 BMP
img = decode_bmp("image.bmp")

# PNG 转 BMP
from png import decode_png, encode_bmp
img = decode_png("input.png")
encode_bmp(img, "output.bmp")
```

### 模式转换

```python
from png import decode_png, convert

img = decode_png("color.png")  # RGBA
gray = convert(img, "L")       # 灰度
rgb = convert(img, "RGB")      # 去除透明度
```

### 矩阵压缩

```python
import math
from png import matrix_to_png, png_to_matrix

# 将二维浮点矩阵压缩为 PNG
matrix = [[math.sin(x * 0.1 + y * 0.2) for x in range(256)]
          for y in range(256)]
matrix_to_png(matrix, "data.png", bit_depth=16)

# 还原（整数无损，浮点数量化）
restored = png_to_matrix("data.png")
```

### 滤波策略

```python
from png import encode_png, Image

img = Image(width=100, height=100, data=pixels, mode="RGB")

# 自动选择每行最优滤波器（默认）
encode_png(img, filter_strategy="auto")

# 强制指定滤波器
encode_png(img, filter_strategy="sub")    # 适合照片
encode_png(img, filter_strategy="paeth")  # 适合渐变
encode_png(img, filter_strategy="none")   # 最快，体积最大
```

## API 参考

### 函数

| 函数 | 描述 |
|------|------|
| `decode_png(source)` | 将 PNG 文件/字节解码为 `Image` |
| `encode_png(image, dest, *, filter_strategy, compression_level)` | 将 `Image` 编码为 PNG |
| `decode_bmp(source)` | 将 BMP 文件/字节解码为 `Image` |
| `encode_bmp(image, dest)` | 将 `Image` 编码为 BMP |
| `matrix_to_png(matrix, dest, *, bit_depth, filter_strategy, compression_level)` | 将二维矩阵压缩为灰度 PNG |
| `png_to_matrix(source)` | 将灰度 PNG 解压为二维矩阵 |
| `convert(image, mode)` | 将图像转换为不同的像素模式 |

### 类

| 类 | 描述 |
|----|------|
| `Image` | 存储解码像素数据的数据类（width, height, data, mode, bit_depth, metadata） |

### 异常

| 异常 | 描述 |
|------|------|
| `ImageError` | 图像编解码错误的基类 |
| `DecodeError` | 解码失败时抛出 |
| `EncodeError` | 编码失败时抛出 |

## 支持的格式

### PNG

| 特性 | 支持情况 |
|------|---------|
| 颜色类型 | 灰度 (0)、RGB (2)、灰度+Alpha (4)、RGBA (6) |
| 位深度 | 每通道 8、16 位 |
| 行滤波器 | None、Sub、Up、Average、Paeth |
| 元数据 | tEXt 块（读/写） |
| 交错 | 不支持（Adam7） |
| 调色板 | 不支持（颜色类型 3） |

### BMP

| 特性 | 支持情况 |
|------|---------|
| 位深度 | 24 位 RGB、32 位 RGBA |
| 压缩 | 仅支持未压缩 |
| 行序 | 自底向上和自顶向下 |
| 调色板/RLE | 不支持 |

## 与 Pillow 对比

| 特性 | zerodep | Pillow |
|------|---------|--------|
| 依赖 | 无（仅标准库） | C 扩展（约 50 MB） |
| 文件大小 | 单个 .py 文件 | 完整包 |
| PNG 编解码 | 支持（8/16 位，4 种颜色类型） | 支持（全部 PNG 特性） |
| BMP 编解码 | 支持（24/32 位） | 支持（全部 BMP 变体） |
| JPEG | 不支持 | 支持 |
| 图像处理 | 仅模式转换 | 完整图像处理 |
| 矩阵压缩 | 内置 API | 通过 numpy 集成 |
| 安装 | 复制一个文件 | `pip install Pillow` |

## 性能测试

与 `Pillow` 对标测试。详见 [PNG 性能测试](../benchmarks/png.md)。
