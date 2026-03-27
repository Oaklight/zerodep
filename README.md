# zerodep

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，支持 Python 3.10+。

## Modules

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `aes/` | AES-128-ECB encryption (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| `qr/` | QR Code generation with terminal rendering | `qrcode` |
| `httpclient/` | Sync + async REST client | `httpx` |

## Usage

Each module is a **self-contained single file** that you can copy directly into your project. No installation required.

## License

MIT
