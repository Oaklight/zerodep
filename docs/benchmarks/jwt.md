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
| RS256 verify | 167 us | 35.5 us | 4.7x slower |
| PS256 verify | 189 us | 40.1 us | 4.7x slower |
| ES256 verify | 1,735 us | 85.6 us | 20.3x slower |
| HS256 verify | 16.0 us | 14.3 us | 1.1x slower |
| HS256 sign | 11.2 us | 10.5 us | 1.1x slower |

Every figure is the mean of three consecutive runs with `--benchmark-min-rounds=20`. Observed ranges across those runs: HS256 verify 16.00--16.07 us, HS256 sign 11.05--11.55 us, RS256 161.6--171.5 us, PS256 183.4--192.2 us, ES256 1,701--1,763 us.

## Where the Time Goes

- **RS256 / PS256** is one modular exponentiation with `e = 65537`, which costs ~147 us of the ~167 us total. OpenSSL uses the same square-and-multiply sequence in C, so the gap is interpreter overhead on 2048-bit multiplies, a fixed cost that does not grow with token size.
- **ES256** is two scalar multiplications on P-256, combined with Shamir's trick into one chain of two-bit steps. The count is exactly `2 * chunks + 2` point doublings and `chunks + 19` point additions, where `chunks = ceil(max(bit_length(u1), bit_length(u2)) / 2)` comes from the two reduced ECDSA scalars. The `+ 2` is constant: two coincidences in `_shamir_mult`'s precompute -- `multiples_of_p2` adds `j2` to itself, and the first `row = _j_add(row, p1)` adds `p1` to itself -- both take `_j_add`'s `h == 0` fallback to `_j_double`. The `19` is the 16-entry table build. Measured over 6,000 sampled signatures, 258/147 is the mode (about 94%); 256/146 follows at about 6% and 254/145 at about 0.4%, with smaller `chunks` rarer still. Two separate multiplications would double the doublings. Every operation is Python-level big-integer arithmetic, which is why the gap is wider than for RSA.
- **HS256** has no big-integer work; `hmac` and `hashlib` are C modules in the stdlib, so both libraries run the same hash. The ~1 us gap left is this module's own guards: the JSON depth pre-scan costs about 0.4 us on a typical token and the key-material check about 1 us. PyJWT has no depth pre-scan.

## Key Takeaways

- **HMAC verification and signing are within about 11%** of PyJWT. Both call the same `hmac` implementation; the gap is the JSON depth pre-scan and the key-material check.
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
