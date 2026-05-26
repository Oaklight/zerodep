# Contributing to Zerodep

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Set up pre-commit hooks: `pre-commit install`
5. Make your changes
6. Run `make lint` to check code quality
7. Run `make test` to run correctness tests
8. Commit and push
9. Open a Pull Request

## Branch Naming

Use descriptive prefixes:

- `feature/xxx` — new functionality
- `fix/xxx` — bug fix
- `refactor/xxx` — code restructuring
- `docs/xxx` — documentation updates
- `test/xxx` — test additions or changes

## Commit Messages

Keep commit messages concise and focused on *why*, not *what*. One logical change per commit.

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- Include a brief description of what changed and why
- Mention any breaking changes explicitly
- Ensure `make lint` passes before submitting
- Merge strategy: rebase

## Adding a New Module

Zerodep modules are self-contained, zero-dependency Python files. To add a new module:

1. Create a directory `<module>/` at the project root
2. Implement your module in `<module>/<module>.py` — stdlib only, no external dependencies
3. Add a PEP 723-style metadata block at the top of the file
4. Add correctness tests in `<module>/test_<module>_correctness.py`
5. Optionally add benchmarks in `<module>/test_<module>_benchmark.py`
6. Run `make manifest` to regenerate `manifest.json`
7. Submit a PR

See existing modules for reference implementations.

## AI-Assisted Contributions

Using AI tools (e.g. Claude, Cursor, Copilot) to assist with development is welcome. However:

- **No AI co-author tags in commits.** Do not add `Co-authored-by` lines for AI tools in git commit messages. This keeps the git history clean and readable.
- **Disclose in PR description.** If AI tools were used significantly in your contribution, add a brief note in the PR description (e.g. "AI was used to assist with implementation").
- **You own the code.** Contributors are fully responsible for any AI-generated code they submit — review it, test it, understand it.

## Code Style

- Python code follows `ruff` defaults
- Docstrings use Google style
- Comments and docstrings in English
- Type hints are encouraged
- Each module must use only the Python standard library

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
