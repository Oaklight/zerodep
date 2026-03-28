# VCS Benchmark

No benchmark is provided for the VCS module.

!!! info "Why No Benchmark?"
    The `vcs` module is a **subprocess-based wrapper** around Git, SVN, Mercurial, and Jujutsu CLI tools. All operations shell out to the underlying VCS binary.

    Performance is entirely dominated by process startup and CLI execution time rather than Python wrapper code. Benchmarking the wrapper overhead would not produce actionable results.
