.PHONY: all test benchmark lint fmt clean help manifest version-check dep-graph dep-check release-check docs-index docs-index-check test-cli test-tabulate benchmark-tabulate test-soup benchmark-soup test-prompt test-validate benchmark-validate test-markdown benchmark-markdown test-diff benchmark-diff test-vcs test-ansi test-frontmatter benchmark-frontmatter test-cache benchmark-cache test-readability benchmark-readability benchmark-readability-compare test-jsonschema benchmark-jsonschema test-png benchmark-png test-httpserver benchmark-httpserver test-websocket benchmark-websocket test-cdp benchmark-cdp test-multipart benchmark-multipart test-s3 benchmark-s3 test-profiler benchmark-profiler benchmark-cold-start test-semantic_search benchmark-semantic_search test-sse benchmark-sse

PYTHON ?= python
PYTEST = $(PYTHON) -m pytest

help:
	@echo "Available targets:"
	@echo "  test             - Run all module tests (use the project env; excludes benchmarks)"
	@echo "  test-aes         - Run AES correctness tests"
	@echo "  test-qr          - Run QR correctness tests"
	@echo "  test-http        - Run HTTP correctness tests"
	@echo "  test-dotenv      - Run dotenv correctness tests"
	@echo "  test-yaml        - Run YAML correctness tests"
	@echo "  test-jsonx       - Run JSONX correctness tests"
	@echo "  test-retry       - Run retry correctness tests"
	@echo "  test-toon        - Run TOON correctness tests"
	@echo "  test-tabulate    - Run tabulate correctness tests"
	@echo "  test-soup        - Run soup correctness tests"
	@echo "  test-prompt      - Run prompt correctness tests"
	@echo "  test-validate    - Run validate correctness tests"
	@echo "  test-markdown    - Run markdown correctness tests"
	@echo "  test-sse         - Run SSE correctness tests"
	@echo "  test-cli         - Run zerodep CLI tests"
	@echo "  benchmark        - Run all module benchmarks"
	@echo "  benchmark-aes    - Run AES benchmarks"
	@echo "  benchmark-qr     - Run QR benchmarks"
	@echo "  benchmark-http   - Run HTTP benchmarks"
	@echo "  benchmark-dotenv - Run dotenv benchmarks"
	@echo "  benchmark-yaml   - Run YAML benchmarks"
	@echo "  benchmark-jsonx  - Run JSONX benchmarks"
	@echo "  benchmark-retry  - Run retry benchmarks"
	@echo "  benchmark-toon   - Run TOON benchmarks"
	@echo "  benchmark-tabulate - Run tabulate benchmarks"
	@echo "  benchmark-soup   - Run soup benchmarks"
	@echo "  benchmark-validate - Run validate benchmarks"
	@echo "  benchmark-markdown - Run markdown benchmarks"
	@echo "  benchmark-sse    - Run SSE benchmarks (vs httpx-sse)"
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
	@echo "  test-httpserver  - Run httpserver correctness tests"
	@echo "  benchmark-httpserver - Run httpserver benchmarks (vs microdot, bottle)"
	@echo "  test-websocket   - Run websocket correctness tests"
	@echo "  benchmark-websocket - Run websocket benchmarks (vs websockets)"
	@echo "  test-cdp         - Run CDP correctness tests"
	@echo "  benchmark-cdp    - Run CDP benchmarks"
	@echo "  test-multipart   - Run multipart correctness tests"
	@echo "  benchmark-multipart - Run multipart benchmarks (vs python-multipart)"
	@echo "  test-s3          - Run s3 correctness tests"
	@echo "  benchmark-s3     - Run s3 benchmarks (vs boto3 + minio; uses SeaweedFS Docker or S3_TEST_ENDPOINT)"
	@echo "  test-profiler    - Run profiler correctness tests"
	@echo "  test-semantic_search - Run semantic_search correctness tests"
	@echo "  benchmark-semantic_search - Run semantic_search benchmarks (vs faiss-cpu)"
	@echo "  benchmark-profiler - Run profiler benchmarks (vs pyinstrument)"
	@echo "  benchmark-cold-start - Run cold-start (import + first-call) benchmarks"
	@echo "  docs-index       - Generate modules/index.md for EN and ZH docs"
	@echo "  docs-index-check - Check that modules/index.md is up-to-date"
	@echo "  manifest         - Regenerate manifest.json"
	@echo "  version-check    - Check modules for uncommitted version bumps"
	@echo "  release-check    - Run all pre-release checks (CI reuses this)"
	@echo "  dep-graph        - Show module dependency graph"
	@echo "  dep-check        - Test changed modules and their dependents"
	@echo "  lint             - Run ruff check"
	@echo "  fmt              - Run ruff format"
	@echo "  clean            - Clean generated files"

test:
	$(PYTEST) test_cli.py a2a/test_a2a_correctness.py acp/test_acp_correctness.py acp/test_acp_client.py acp/test_acp_opencode_integration.py aes/test_aes_correctness.py aiosqlite/test_aiosqlite_correctness.py ansi/test_ansi_correctness.py cache/test_cache_correctness.py cdp/test_cdp_correctness.py config/test_config_correctness.py config/test_config_edge.py config/test_config_inject.py depdetect/test_depdetect_correctness.py diff/test_diff_correctness.py dotenv/test_dotenv_correctness.py filelock/test_filelock_correctness.py frontmatter/test_frontmatter_correctness.py httpclient/test_httpclient_correctness.py httpclient/test_httpclient_edge.py httpclient/test_httpclient_pooling.py httpclient/test_httpclient_streaming.py httpclient/test_httpclient_timing.py httpclient/test_httpclient_truncated.py httpserver/test_httpserver_correctness.py httpserver/test_httpserver_keepalive.py httpserver/test_httpserver_rejected.py httpserver/test_httpserver_tls.py httpserver/test_httpserver_unix_socket.py jsonrpc/test_jsonrpc_correctness.py jsonschema/test_jsonschema_correctness.py jsonx/test_jsonx_correctness.py jsonx/test_jsonx_fastpath.py llmstxt/test_llmstxt_correctness.py markdown/test_markdown_correctness.py multipart/test_multipart_correctness.py multipart/test_multipart_memory.py persistdict/test_persistdict_correctness.py png/test_png_correctness.py profiler/test_profiler_correctness.py prompt/test_prompt_correctness.py protobuf/test_protobuf_correctness.py protobuf/test_protobuf_memory.py ptyx/test_ptyx_correctness.py qr/test_qr_correctness.py qr/test_qr_render.py ratelimit/test_ratelimit_correctness.py readability/test_readability_correctness.py readability/test_readability_memory.py retry/test_retry_correctness.py runner/test_runner_correctness.py runner/test_runner_edge.py s3/test_s3_correctness.py scheduler/test_scheduler_correctness.py scheduler/test_scheduler_edge.py semantic_search/test_semantic_search_correctness.py semver/test_semver_correctness.py skills/test_skills_correctness.py soup/test_soup_correctness.py soup/test_soup_memory.py sparse_search/test_sparse_search_correctness.py sse/test_sse_correctness.py sse/test_sse_inject.py structlog/test_structlog_correctness.py synctex/test_synctex_correctness.py tabulate/test_tabulate_correctness.py toon/test_toon_conformance.py toon/test_toon_correctness.py toon/test_toon_decode_errors.py useragent/test_useragent_correctness.py validate/test_validate_correctness.py vcs/test_vcs_correctness.py vcs/test_vcs_inject.py websocket/test_websocket_correctness.py xml/test_xml_correctness.py xml/test_xml_memory.py yaml/test_yaml_correctness.py yaml/test_yaml_memory.py -v -rs

test-aes:
	$(PYTEST) aes/test_aes_correctness.py -v

test-qr:
	$(PYTEST) qr/test_qr_correctness.py -v

test-http:
	$(PYTEST) httpclient/test_httpclient_correctness.py -v

test-sse:
	$(PYTEST) sse/test_sse_correctness.py sse/test_sse_inject.py -v -rs

test-cli:
	$(PYTEST) test_cli.py -v -rs

test-dotenv:
	$(PYTEST) dotenv/test_dotenv_correctness.py -v

test-yaml:
	$(PYTEST) yaml/test_yaml_correctness.py -v

test-jsonx:
	$(PYTEST) jsonx/test_jsonx_correctness.py jsonx/test_jsonx_fastpath.py -v -rs

test-retry:
	$(PYTEST) retry/test_retry_correctness.py -v

test-toon:
	$(PYTEST) toon/test_toon_correctness.py toon/test_toon_conformance.py toon/test_toon_decode_errors.py -v -rs

test-tabulate:
	$(PYTEST) tabulate/test_tabulate_correctness.py -v

test-soup:
	$(PYTEST) soup/test_soup_correctness.py -v

test-prompt:
	$(PYTEST) prompt/test_prompt_correctness.py -v

test-validate:
	$(PYTEST) validate/test_validate_correctness.py -v

test-markdown:
	$(PYTEST) markdown/test_markdown_correctness.py -v

benchmark:
	$(PYTEST) a2a/test_a2a_benchmark.py acp/test_acp_benchmark.py aes/test_aes_benchmark.py aiosqlite/test_aiosqlite_benchmark.py cache/test_cache_benchmark.py cdp/test_cdp_benchmark.py config/test_config_benchmark.py diff/test_diff_benchmark.py dotenv/test_dotenv_benchmark.py frontmatter/test_frontmatter_benchmark.py httpclient/test_httpclient_benchmark.py httpserver/test_httpserver_benchmark.py jsonrpc/test_jsonrpc_benchmark.py jsonschema/test_jsonschema_benchmark.py jsonx/test_jsonx_benchmark.py llmstxt/test_llmstxt_benchmark.py markdown/test_markdown_benchmark.py multipart/test_multipart_benchmark.py persistdict/test_persistdict_benchmark.py png/test_png_benchmark.py profiler/test_profiler_benchmark.py protobuf/test_protobuf_benchmark.py qr/test_qr_benchmark.py ratelimit/test_ratelimit_benchmark.py readability/test_readability_benchmark.py retry/test_retry_benchmark.py runner/test_runner_benchmark.py s3/test_s3_benchmark.py scheduler/test_scheduler_benchmark.py semantic_search/test_semantic_search_benchmark.py semver/test_semver_benchmark.py soup/test_soup_benchmark.py sparse_search/test_sparse_search_benchmark.py sse/test_sse_benchmark.py structlog/test_structlog_benchmark.py tabulate/test_tabulate_benchmark.py toon/test_toon_benchmark.py useragent/test_useragent_benchmark.py validate/test_validate_benchmark.py websocket/test_websocket_benchmark.py xml/test_xml_benchmark.py yaml/test_yaml_benchmark.py -v

benchmark-aes:
	$(PYTEST) aes/test_aes_benchmark.py -v

benchmark-qr:
	$(PYTEST) qr/test_qr_benchmark.py -v

benchmark-http:
	$(PYTEST) httpclient/test_httpclient_benchmark.py -v

benchmark-sse:
	$(PYTEST) sse/test_sse_benchmark.py -v

benchmark-dotenv:
	$(PYTEST) dotenv/test_dotenv_benchmark.py -v

benchmark-yaml:
	$(PYTEST) yaml/test_yaml_benchmark.py -v

benchmark-jsonx:
	$(PYTEST) jsonx/test_jsonx_benchmark.py -v

benchmark-retry:
	$(PYTEST) retry/test_retry_benchmark.py -v

benchmark-toon:
	$(PYTEST) toon/test_toon_benchmark.py -v

benchmark-tabulate:
	$(PYTEST) tabulate/test_tabulate_benchmark.py -v

benchmark-soup:
	$(PYTEST) soup/test_soup_benchmark.py -v

benchmark-validate:
	$(PYTEST) validate/test_validate_benchmark.py -v

benchmark-markdown:
	$(PYTEST) markdown/test_markdown_benchmark.py -v

test-diff:
	$(PYTEST) diff/test_diff_correctness.py -v

benchmark-diff:
	$(PYTEST) diff/test_diff_benchmark.py -v

test-vcs:
	$(PYTEST) vcs/test_vcs_correctness.py -v

test-ansi:
	$(PYTEST) ansi/test_ansi_correctness.py -v

test-frontmatter:
	$(PYTEST) frontmatter/test_frontmatter_correctness.py -v

benchmark-frontmatter:
	$(PYTEST) frontmatter/test_frontmatter_benchmark.py -v

test-cache:
	$(PYTEST) cache/test_cache_correctness.py -v

test-ptyx:
	$(PYTEST) ptyx/test_ptyx_correctness.py -v

benchmark-cache:
	$(PYTEST) cache/test_cache_benchmark.py -v

test-readability:
	$(PYTEST) readability/test_readability_correctness.py -v

benchmark-readability:
	$(PYTEST) readability/test_readability_benchmark.py -v

benchmark-readability-compare:
	cd readability && npm install --prefer-offline --no-audit 2>/dev/null; \
	python readability/benchmark_compare.py

test-jsonschema:
	$(PYTEST) jsonschema/test_jsonschema_correctness.py -v

benchmark-jsonschema:
	$(PYTEST) jsonschema/test_jsonschema_benchmark.py -v

test-png:
	$(PYTEST) png/test_png_correctness.py -v

benchmark-png:
	$(PYTEST) png/test_png_benchmark.py -v

test-httpserver:
	$(PYTEST) httpserver/test_httpserver_correctness.py -v

benchmark-httpserver:
	$(PYTEST) httpserver/test_httpserver_benchmark.py -v

test-websocket:
	$(PYTEST) websocket/test_websocket_correctness.py -v

benchmark-websocket:
	$(PYTEST) websocket/test_websocket_benchmark.py -v

test-cdp:
	$(PYTEST) cdp/test_cdp_correctness.py -v

benchmark-cdp:
	$(PYTEST) cdp/test_cdp_benchmark.py -v

test-multipart:
	$(PYTEST) multipart/test_multipart_correctness.py -v

benchmark-multipart:
	$(PYTEST) multipart/test_multipart_benchmark.py -v

test-s3:
	$(PYTEST) s3/test_s3_correctness.py -v

benchmark-s3:
	$(PYTEST) s3/test_s3_benchmark.py -v


test-profiler:
	$(PYTEST) profiler/test_profiler_correctness.py -v

benchmark-profiler:
	$(PYTEST) profiler/test_profiler_benchmark.py -v

test-semantic_search:
	$(PYTEST) semantic_search/test_semantic_search_correctness.py -v

benchmark-semantic_search:
	$(PYTEST) semantic_search/test_semantic_search_benchmark.py -v

benchmark-cold-start:
	$(PYTEST) test_cold_start.py -v

manifest:
	python zerodep.py manifest

docs-index: manifest
	python _scripts/generate_module_index.py

docs-index-check: manifest
	python _scripts/generate_module_index.py --check

version-check:
	python zerodep.py version-check

release-check:
	python zerodep.py release-check

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
