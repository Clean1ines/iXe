Deployment & Operations Manual — Parser

1. Environment
	•	Platform: Linux (Ubuntu 22.04)
	•	Requirements:
	•	python>=3.10
	•	playwright (pip install playwright) + playwright install chromium
	•	pip packages from requirements.txt
	•	Hardware: 2 vCPU, 4GB RAM (development); prod: 4 vCPU, 8GB.

2. Dockerfile (recommended)

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m playwright install chromium
COPY . .
ENTRYPOINT ["python", "src/parser/cli.py"]

3. Runbook (typical tasks)

Start parsing

# activate venv or run docker
python src/parser/cli.py --proj AC437B... --start-page 1 --end-page 100 --out data/json/ --throttle 1 --concurrency 2

Resume

python src/parser/cli.py --resume --out data/json/

Debugging a failing page
	•	Inspect debug_pages/page_<n>.html and debug_pages/page_<n>_log.json.
	•	Re-run single page:

python -c "from parser import cli; cli.parse_page(page=42, proj='AC...')"

4. Monitoring & Metrics
	•	Export metrics to Prometheus:
	•	fetch_success_rate (counter)
	•	render_latency_ms (histogram)
	•	images_download_failures (counter)
	•	Logs: structured JSON to STDOUT and file logs/parser.log.

5. Backups & retention
	•	data/json/ and data/assets/ — rsync nightly to archive bucket.
	•	Keep last 30 days of debug_pages/.

6. Recovery
	•	If process was interrupted: CLI uses state/last_run.json containing last_page, last_offset — resume.
	•	If Playwright crash: restart process; implement supervisor (systemd service) to auto-restart with backoff.

7. CI/CD
	•	GitHub Actions:
	•	on: pull_request run lint, unit tests.
	•	on: push to main run integration and build image.
	•	Artifacts: data/json/sample_100.jsonl uploaded to run artifact storage.

8. Security & Ethics
	•	Adhere robots.txt; default behavior is respect_robots=True.
	•	Logging PII: none expected. Sanitize logs.
