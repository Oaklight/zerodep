# JWT Benchmark

Apple-to-apple performance comparison between zerodep JWT and [`PyJWT[crypto]`](https://pypi.org/project/PyJWT/) (OpenSSL-backed via `cryptography`).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** PyJWT 2.10.1, cryptography 46.0.6
    - **Last Updated:** 2026-11-10

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep (native)** | `jwt.py` | `ctypes` -> system `libcrypto` for RSA/PS modexp and ECDSA |
| **zerodep (pure)** | `jwt.py`, `ZERODEP_JWT_BACKEND=python` | `hashlib`, `hmac`, `int` arithmetic, Jacobian point math |
| **PyJWT[crypto]** | *(reference)* | `cryptography` calling OpenSSL |

## Workloads

Each case verifies (or, for HS256, signs) a token with six claims (`sub`, `iss`, `aud`, `iat`, `exp`, `scope`) and a checked audience, so token parsing and claim validation are included on both sides. PyJWT signs every token; both libraries then verify the same compact JWS.

| Algorithm | Key |
|-----------|-----|
| RS256 | RSA 2048, `e = 65537` |
| PS256 | RSA 2048, salt length = digest length |
| ES256 | P-256 |
| HS256 | 39-byte shared secret |

## Results (Mean)

| Operation | zerodep native | zerodep pure | PyJWT[crypto] | native vs PyJWT |
|-----------|----------------|--------------|---------------|-----------------|
| RS256 verify | 57.6 us | 164.4 us | 34.8 us | 1.7x slower |
| PS256 verify | 77.3 us | 187.1 us | 40.3 us | 1.9x slower |
| ES256 verify | 102.3 us | 1,716.6 us | 85.2 us | 1.2x slower |
| HS256 verify | 16.2 us | 16.1 us | 14.5 us | 1.1x slower |
| HS256 sign | 10.9 us | 11.2 us | 10.4 us | 1.0x |

Every figure is the mean of three consecutive runs of each backend with `--benchmark-min-rounds=20`, on the same machine and in the same session. The pure column was forced with `ZERODEP_JWT_BACKEND=python`. Run-to-run spread is about 1 us on the native backend and up to about 2% on the pure backend, so the last digit is indicative rather than a bound.

## Where the Time Goes

- **RSA / PS native.** One modular exponentiation with `e = 65537` runs inside `BN_mod_exp`; padding, `DigestInfo`, JSON parsing and claim checks stay in Python. The remaining gap to PyJWT is about 23 us on RS256 and 37 us on PS256, most of it the Python-side PSS mask generation (MGF1) and the per-call key conversion.
- **RSA / PS pure.** The same algorithm with `pow()` as the modexp, which costs about 150 us of the total. That is why the pure backend is 2.1--2.9x slower than native here.
- **ES256 native.** `ECDSA_do_verify` runs the two scalar multiplications in OpenSSL; the module builds an `EC_KEY` from the JWK point on each call. The remaining ~17 us over PyJWT is that construction plus token parsing and claims.
- **ES256 pure.** Two scalar multiplications on P-256, combined with Shamir's trick into one chain of two-bit steps. The count is exactly `2 * chunks + 2` point doublings and `chunks + 19` point additions, where `chunks = ceil(max(bit_length(u1), bit_length(u2)) / 2)` comes from the two reduced ECDSA scalars. The `+ 2` is constant: two coincidences in `_shamir_mult`'s precompute -- `multiples_of_p2` adds `j2` to itself, and the first `row = _j_add(row, p1)` adds `p1` to itself -- both take `_j_add`'s `h == 0` fallback to `_j_double`. The `19` is the 16-entry table build. Measured over 6,000 sampled signatures, 258/147 is the mode (about 94%); 256/146 follows at about 6% and 254/145 at about 0.4%, with smaller `chunks` rarer still. Two separate multiplications would double the doublings. Every operation is Python-level big-integer arithmetic, which is why the pure backend is ~17x slower than native.
- **HS256** has no big-integer work in either backend; `hmac` and `hashlib` are C modules in the stdlib, so both libraries run the same hash. The gap -- about 1.6 us on verify and 0.8 us on sign -- is this module's own guards: the key-material check costs about 1 us on every HMAC call, and the JSON depth pre-scan about 0.4 us on a typical token during verification. PyJWT has no depth pre-scan.

## Key Takeaways

- **The native backend makes asymmetric verification competitive with PyJWT**: 1.7x slower on RS256, 1.9x on PS256 and 1.2x on ES256, versus 4.7x, 4.7x and 20x for the pure backend.
- **HMAC is unchanged** at about 1.1x PyJWT, because both call the same C `hmac` implementation.
- **No Python dependency.** The accelerator uses the system `libcrypto` through `ctypes`, which Python already links for `ssl` and `hashlib`. When the library or a needed symbol is missing, the module falls back to pure Python with identical results; `BACKEND` says which path ran.
- **A pure fallback remains.** `ZERODEP_JWT_BACKEND=python` forces it, for constrained images or for comparison.

## Run It Yourself

```bash
pip install pytest pytest-benchmark "PyJWT[crypto]"
pytest jwt/test_jwt_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jwt.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
