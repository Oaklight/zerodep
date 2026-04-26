# PNG 性能测试

zerodep png（纯 Python）与 [`Pillow`](https://pypi.org/project/Pillow/)（C 扩展）的 Apple-to-Apple 性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考实现:** Pillow 12.2.0
    - **最后更新:** 2026-04-26

## 实现方案

| 实现 | 文件/包 | 描述 |
|------|---------|------|
| **zerodep** | `png.py` | 纯 Python PNG/BMP 编解码器，使用标准库 zlib |
| **Pillow** | *（参考实现）* | 功能完整的图像库，含 C 扩展 |

## 测试图像

| 标签 | 描述 |
|------|------|
| 小型 | 64x64 RGBA（16 KB 像素） |
| 中型 | 256x256 RGBA（256 KB 像素） |
| 大型 | 1024x1024 RGBA（4 MB 像素） |

## 要点

- **Pillow 显著更快** —— 这是预期结果，因为 Pillow 使用编译的 C 扩展（libpng、zlib-ng），而 zerodep 是纯 Python 实现。核心瓶颈在于逐字节的行滤波循环。
- **PNG 解码主要是 zlib** —— `zlib.decompress` 调用（C 代码）占主导地位；纯 Python 的反滤波循环增加的开销与图像大小成正比。
- **PNG 编码受滤波限制** —— 最小和启发式对每行尝试全部 5 种滤波器，使编码比解码每像素多约 5 倍工作量。
- **BMP 很快** —— 无压缩意味着 BMP 编解码主要是内存拷贝 + 字节交换（BGR↔RGB），因此 zerodep 与 Pillow 的差距相对较小。
- **zerodep 面向不同的使用场景** —— 零依赖和单文件的权衡：
    - 生成二维码、图表或缩略图
    - 读取图像元数据或像素数据
    - 通过 PNG 行滤波器进行矩阵数据压缩
    - C 扩展不可用的环境

## 自行运行

```bash
pip install pytest pytest-benchmark Pillow numpy
pytest png/test_png_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/png.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
