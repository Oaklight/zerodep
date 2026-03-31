# Skills Benchmark

No benchmark is provided for the Skills module.

!!! info "Why No Benchmark?"
    The `skills` module implements the [Agent Skills](https://agentskills.io) specification -- parsing `SKILL.md` files, managing a registry, and generating system prompts. It is a **utility module with no direct third-party counterpart** to benchmark against.

    The official `skills-ref` package is a minimal reference implementation (3 functions) explicitly marked as "not for production". Skill parsing is a low-frequency operation (run once at startup), so performance comparison is not meaningful.
