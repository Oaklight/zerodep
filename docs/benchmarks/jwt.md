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
| **zerodep** | `jwt.py` | Pure Python: `hashlib`, `hmac`, `int` arithmetic, Jacobian point math |
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

| Operation | zerodep | PyJWT[crypto] | Ratio |
|-----------|---------|---------------|-------|
| RS256 verify | 167 us | 35.4 us | 4.7x slower |
| PS256 verify | 188 us | 40.8 us | 4.6x slower |
| ES256 verify | 1,715 us | 86.2 us | 19.9x slower |
| HS256 verify | 15.0 us | 14.4 us | ~1.0x |
| HS256 sign | 10.8 us | 10.5 us | ~1.0x |

Every figure is the mean of three consecutive runs with `--benchmark-min-rounds=20`. Observed ranges across those runs: HS256 verify 14.7--15.4 us, HS256 sign 10.6--11.2 us, RS256 164.7--170.0 us, PS256 184.9--190.9 us, ES256 1,704--1,736 us.

## Where the Time Goes

- **RS256 / PS256** is one modular exponentiation with `e = 65537`, which costs ~147 us of the ~167 us total. OpenSSL uses the same square-and-multiply sequence in C, so the gap is interpreter overhead on 2048-bit multiplies, a fixed cost that does not grow with token size.
- **ES256** is two scalar multiplications on P-256, combined with Shamir's trick into one chain of two-bit steps. Instrumenting the point helpers over six sampled signatures counts **254--258 point doublings and 145--147 point additions** per verify (ES384: 384--386 doublings, 210--211 additions). The 2-bits-at-a-time loop accounts for 2 doublings and 1 addition per step, plus the 16-entry table build; the small spread comes from the scalars, because `_j_add` early-returns on the point at infinity and falls back to `_j_double` when its operands coincide. Two separate multiplications would double the doublings. Every operation is Python-level big-integer arithmetic, which is why the gap is wider than for RSA.
- **HS256** has no big-integer work; `hmac` and `hashlib` are C modules in the stdlib, so both libraries measure the same code. The difference is inside the run-to-run noise.

## Key Takeaways

- **HMAC verification and signing are on par** with PyJWT, because both call the same `hmac` implementation.
- **Asymmetric verification is 4.6-20x slower** than OpenSSL. For an OAuth resource server this is a few hundred microseconds per request after the JWKS lookup, which is usually far below the cost of the request's own database or network work -- but it is not free, and a token-per-request path at very high volume should measure it first.
- **No compiled dependency.** The module installs nothing, so it works where a wheel for `cryptography` is unavailable or unwanted.

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
