"""AES encryption — OpenSSL-accelerated by default, pure-Python fallback.

On import this package tries to load ``aes_openssl`` (ctypes binding to the
system *libcrypto*).  If the library is unavailable the pure-Python
implementation in ``aes`` is used instead.  The public API is identical
regardless of which backend is active.

Check :data:`BACKEND` to see which one was selected at runtime::

    >>> from aes import BACKEND
    >>> print(BACKEND)        # "openssl" or "python"
"""

from __future__ import annotations

__all__ = [
    "aes_ecb_encrypt",
    "aes_ecb_decrypt",
    "aes_cbc_encrypt",
    "aes_cbc_decrypt",
    "aes_ctr_encrypt",
    "aes_ctr_decrypt",
    "aes_gcm_encrypt",
    "aes_gcm_decrypt",
    "aes_ecb_padded_size",
    "aes128_ecb_encrypt",
    "aes128_ecb_decrypt",
    "BACKEND",
]

try:
    from .aes_openssl import (  # type: ignore[assignment]
        aes128_ecb_decrypt,
        aes128_ecb_encrypt,
        aes_cbc_decrypt,
        aes_cbc_encrypt,
        aes_ctr_decrypt,
        aes_ctr_encrypt,
        aes_ecb_decrypt,
        aes_ecb_encrypt,
        aes_ecb_padded_size,
        aes_gcm_decrypt,
        aes_gcm_encrypt,
    )

    BACKEND: str = "openssl"
except (OSError, ImportError):
    from .aes import (  # type: ignore[assignment]
        aes128_ecb_decrypt,
        aes128_ecb_encrypt,
        aes_cbc_decrypt,
        aes_cbc_encrypt,
        aes_ctr_decrypt,
        aes_ctr_encrypt,
        aes_ecb_decrypt,
        aes_ecb_encrypt,
        aes_ecb_padded_size,
        aes_gcm_decrypt,
        aes_gcm_encrypt,
    )

    BACKEND: str = "python"  # type: ignore[no-redef]
