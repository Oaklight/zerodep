# ANSI Benchmark

No benchmark is provided for the ANSI module.

!!! info "Why No Benchmark?"
    The `ansi` module provides ANSI escape code primitives (foreground/background colors, text styles, cursor control). It is a **utility module with no direct third-party counterpart** to benchmark against.

    The operations are trivial string concatenations and lookups -- there is no meaningful performance comparison to be made. Any ANSI library would perform equivalently since the work is dominated by terminal I/O, not escape code generation.
