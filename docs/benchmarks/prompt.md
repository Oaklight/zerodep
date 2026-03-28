# Prompt Benchmark

No benchmark is provided for the Prompt module.

!!! info "Why No Benchmark?"
    The `prompt` module provides interactive CLI prompts (confirm, select, text) using raw terminal I/O. It is an **interactive module where performance is irrelevant** -- execution time is entirely dominated by user input latency, not code execution.

    While [questionary](https://pypi.org/project/questionary/) offers similar functionality, benchmarking interactive terminal prompts is not meaningful since the bottleneck is always human response time.
