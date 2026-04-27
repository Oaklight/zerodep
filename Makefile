.PHONY: all test benchmark lint fmt clean help manifest version-check dep-graph dep-check docs-index docs-index-check test-tabulate benchmark-tabulate test-soup benchmark-soup test-prompt test-validate benchmark-validate test-markdown benchmark-markdown test-diff benchmark-diff test-vcs test-ansi test-frontmatter benchmark-frontmatter test-cache benchmark-cache test-readability benchmark-readability benchmark-readability-compare test-jsonschema benchmark-jsonschema test-png benchmark-png

help:
	@echo "Available targets:"
	@echo "  test             - Run correctness tests for all modules"
	@echo "  test-aes         - Run AES correctness tests"
	@echo "  test-qr          - Run QR correctness tests"
	@echo "  test-http        - Run HTTP correctness tests"
	@echo "  test-dotenv      - Run dotenv correctness tests"
	@echo "  test-yaml        - Run YAML correctness tests"
	@echo "  test-jsonc       - Run JSONC correctness tests"
	@echo "  test-retry       - Run retry correctness tests"
	@echo "  test-toon        - Run TOON correctness tests"
	@echo "  test-tabulate    - Run tabulate correctness tests"
	@echo "  test-soup        - Run soup correctness tests"
	@echo "  test-prompt      - Run prompt correctness tests"
	@echo "  test-validate    - Run validate correctness tests"
	@echo "  test-markdown    - Run markdown correctness tests"
	@echo "  benchmark        - Run benchmarks for all modules"
	@echo "  benchmark-aes    - Run AES benchmarks"
	@echo "  benchmark-qr     - Run QR benchmarks"
	@echo "  benchmark-http   - Run HTTP benchmarks"
	@echo "  benchmark-dotenv - Run dotenv benchmarks"
	@echo "  benchmark-yaml   - Run YAML benchmarks"
	@echo "  benchmark-jsonc  - Run JSONC benchmarks"
	@echo "  benchmark-retry  - Run retry benchmarks"
	@echo "  benchmark-toon   - Run TOON benchmarks"
	@echo "  benchmark-tabulate - Run tabulate benchmarks"
	@echo "  benchmark-soup   - Run soup benchmarks"
	@echo "  benchmark-validate - Run validate benchmarks"
	@echo "  benchmark-markdown - Run markdown benchmarks"
	@echo "  test-diff        - Run diff correctness tests"
	@echo "  benchmark-diff   - Run diff benchmarks"
	@echo "  test-vcs         - Run VCS correctness tests"
	@echo "  test-ansi        - Run ANSI correctness tests"
	@echo "  test-frontmatter - Run frontmatter correctness tests"
	@echo "  benchmark-frontmatter - Run frontmatter benchmarks"
	@echo "  test-cache       - Run cache correctness tests"
	@echo "  benchmark-cache  - Run cache benchmarks"
	@echo "  test-readability - Run readability correctness tests"
	@echo "  benchmark-readability - Run readability benchmarks (Python)"
	@echo "  benchmark-readability-compare - Run three-way benchmark (zerodep vs lxml vs Mozilla JS)"
	@echo "  test-jsonschema  - Run jsonschema correctness tests"
	@echo "  benchmark-jsonschema - Run jsonschema benchmarks (vs allof-merge JS)"
	@echo "  test-png         - Run PNG correctness tests"
	@echo "  benchmark-png    - Run PNG benchmarks (vs Pillow)"
	@echo "  docs-index       - Generate modules/index.md for EN and ZH docs"
	@echo "  docs-index-check - Check that modules/index.md is up-to-date"
	@echo "  manifest         - Regenerate manifest.json"
	@echo "  version-check    - Check modules for uncommitted version bumps"
	@echo "  dep-graph        - Show module dependency graph"
	@echo "  dep-check        - Test changed modules and their dependents"
	@echo "  lint             - Run ruff check"
	@echo "  fmt              - Run ruff format"
	@echo "  clean            - Clean generated files"

test:
	pytest aes/test_aes_correctness.py qr/test_qr_correctness.py httpclient/test_httpclient_correctness.py dotenv/test_dotenv_correctness.py yaml/test_yaml_correctness.py jsonc/test_jsonc_correctness.py retry/test_retry_correctness.py toon/test_toon_correctness.py tabulate/test_tabulate_correctness.py soup/test_soup_correctness.py prompt/test_prompt_correctness.py validate/test_validate_correctness.py markdown/test_markdown_correctness.py diff/test_diff_correctness.py vcs/test_vcs_correctness.py ansi/test_ansi_correctness.py frontmatter/test_frontmatter_correctness.py cache/test_cache_correctness.py readability/test_readability_correctness.py jsonschema/test_jsonschema_correctness.py png/test_png_correctness.py -v

test-aes:
	pytest aes/test_aes_correctness.py -v

test-qr:
	pytest qr/test_qr_correctness.py -v

test-http:
	pytest httpclient/test_httpclient_correctness.py -v

test-dotenv:
	pytest dotenv/test_dotenv_correctness.py -v

test-yaml:
	pytest yaml/test_yaml_correctness.py -v

test-jsonc:
	pytest jsonc/test_jsonc_correctness.py -v

test-retry:
	pytest retry/test_retry_correctness.py -v

test-toon:
	pytest toon/test_toon_correctness.py -v

test-tabulate:
	pytest tabulate/test_tabulate_correctness.py -v

test-soup:
	pytest soup/test_soup_correctness.py -v

test-prompt:
	pytest prompt/test_prompt_correctness.py -v

test-validate:
	pytest validate/test_validate_correctness.py -v

test-markdown:
	pytest markdown/test_markdown_correctness.py -v

benchmark:
	pytest aes/test_aes_benchmark.py qr/test_qr_benchmark.py httpclient/test_httpclient_benchmark.py dotenv/test_dotenv_benchmark.py yaml/test_yaml_benchmark.py jsonc/test_jsonc_benchmark.py retry/test_retry_benchmark.py toon/test_toon_benchmark.py tabulate/test_tabulate_benchmark.py soup/test_soup_benchmark.py validate/test_validate_benchmark.py markdown/test_markdown_benchmark.py diff/test_diff_benchmark.py frontmatter/test_frontmatter_benchmark.py cache/test_cache_benchmark.py readability/test_readability_benchmark.py jsonschema/test_jsonschema_benchmark.py png/test_png_benchmark.py -v

benchmark-aes:
	pytest aes/test_aes_benchmark.py -v

benchmark-qr:
	pytest qr/test_qr_benchmark.py -v

benchmark-http:
	pytest httpclient/test_httpclient_benchmark.py -v

benchmark-dotenv:
	pytest dotenv/test_dotenv_benchmark.py -v

benchmark-yaml:
	pytest yaml/test_yaml_benchmark.py -v

benchmark-jsonc:
	pytest jsonc/test_jsonc_benchmark.py -v

benchmark-retry:
	pytest retry/test_retry_benchmark.py -v

benchmark-toon:
	pytest toon/test_toon_benchmark.py -v

benchmark-tabulate:
	pytest tabulate/test_tabulate_benchmark.py -v

benchmark-soup:
	pytest soup/test_soup_benchmark.py -v

benchmark-validate:
	pytest validate/test_validate_benchmark.py -v

benchmark-markdown:
	pytest markdown/test_markdown_benchmark.py -v

test-diff:
	pytest diff/test_diff_correctness.py -v

benchmark-diff:
	pytest diff/test_diff_benchmark.py -v

test-vcs:
	pytest vcs/test_vcs_correctness.py -v

test-ansi:
	pytest ansi/test_ansi_correctness.py -v

test-frontmatter:
	pytest frontmatter/test_frontmatter_correctness.py -v

benchmark-frontmatter:
	pytest frontmatter/test_frontmatter_benchmark.py -v

test-cache:
	pytest cache/test_cache_correctness.py -v

benchmark-cache:
	pytest cache/test_cache_benchmark.py -v

test-readability:
	pytest readability/test_readability_correctness.py -v

benchmark-readability:
	pytest readability/test_readability_benchmark.py -v

benchmark-readability-compare:
	cd readability && npm install --prefer-offline --no-audit 2>/dev/null; \
	python readability/benchmark_compare.py

test-jsonschema:
	pytest jsonschema/test_jsonschema_correctness.py -v

benchmark-jsonschema:
	pytest jsonschema/test_jsonschema_benchmark.py -v

test-png:
	pytest png/test_png_correctness.py -v

benchmark-png:
	pytest png/test_png_benchmark.py -v

manifest:
	python zerodep.py manifest

docs-index: manifest
	python _scripts/generate_module_index.py

docs-index-check: manifest
	python _scripts/generate_module_index.py --check

version-check:
	python zerodep.py version-check

dep-graph:
	python zerodep.py dep-graph

dep-check:
	python zerodep.py dep-check

lint:
	ruff check .

fmt:
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .benchmarks -exec rm -rf {} +
	rm -rf .ruff_cache
