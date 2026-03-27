.PHONY: all test benchmark lint fmt clean help

help:
	@echo "Available targets:"
	@echo "  test             - Run correctness tests for all modules"
	@echo "  test-aes         - Run AES correctness tests"
	@echo "  test-qr          - Run QR correctness tests"
	@echo "  test-http        - Run HTTP correctness tests"
	@echo "  test-dotenv      - Run dotenv correctness tests"
	@echo "  test-yaml        - Run YAML correctness tests"
	@echo "  benchmark        - Run benchmarks for all modules"
	@echo "  benchmark-aes    - Run AES benchmarks"
	@echo "  benchmark-qr     - Run QR benchmarks"
	@echo "  benchmark-http   - Run HTTP benchmarks"
	@echo "  benchmark-dotenv - Run dotenv benchmarks"
	@echo "  benchmark-yaml   - Run YAML benchmarks"
	@echo "  lint             - Run ruff check"
	@echo "  fmt              - Run ruff format"
	@echo "  clean            - Clean generated files"

test:
	pytest aes/test_aes_correctness.py qr/test_qr_correctness.py httpclient/test_http_correctness.py dotenv/test_dotenv_correctness.py yaml/test_yaml_correctness.py -v

test-aes:
	pytest aes/test_aes_correctness.py -v

test-qr:
	pytest qr/test_qr_correctness.py -v

test-http:
	pytest httpclient/test_http_correctness.py -v

test-dotenv:
	pytest dotenv/test_dotenv_correctness.py -v

test-yaml:
	pytest yaml/test_yaml_correctness.py -v

benchmark:
	pytest aes/test_aes_benchmark.py qr/test_qr_benchmark.py httpclient/test_http_benchmark.py dotenv/test_dotenv_benchmark.py yaml/test_yaml_benchmark.py -v

benchmark-aes:
	pytest aes/test_aes_benchmark.py -v

benchmark-qr:
	pytest qr/test_qr_benchmark.py -v

benchmark-http:
	pytest httpclient/test_http_benchmark.py -v

benchmark-dotenv:
	pytest dotenv/test_dotenv_benchmark.py -v

benchmark-yaml:
	pytest yaml/test_yaml_benchmark.py -v

lint:
	ruff check .

fmt:
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .benchmarks -exec rm -rf {} +
	rm -rf .ruff_cache
