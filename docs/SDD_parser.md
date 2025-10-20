System Design Document (SDD) — FIPI Parser & Content Pipeline

Версия: 1.0
Дата: 2025-10-19
Автор: (auto-generated)

1. Цель документа

Описание архитектуры парсера открытого банка ФИПИ, систем рендеринга, нормализации MathML/MathJax → LaTeX, хранения и API-выгрузки для учебного движка.

2. Краткое решение (executive summary)

Компонент парсера выполняет: (1) fetch HTML (requests / fallback Playwright), (2) render JS/MathJax (Playwright headless), (3) extract task blocks и изображения, (4) нормализует текст (cp1251 → utf-8, MathML → LaTeX), (5) сохраняет raw/html + structured JSON, (6) отдаёт по API или сохраняет в объектном хранилище.

3. Компоненты системы (high level)
	•	CLI Orchestrator (parser/cli.py) — управляющий скрипт: parse --project <proj> --pages 1..N.
	•	Fetcher (fetcher.py) — делает HTTP запросы с retries, backoff, SSL-fallback.
	•	Renderer (renderer.py) — Playwright context / headless chromium для рендеринга страниц, выполнения JS (MathJax), создание snapshot HTML.
	•	Extractor (extractor.py) — распознаёт qblocks, извлекает MathML, изображения, метаданные.
	•	Normalizer (normalizer.py) — преобразует MathML → LaTeX (и/или unicode), исправляет дублирование, whitespace normalization, cp1251 handling.
	•	ImageFetcher (images.py) — скачивает ресурсы (png/svg), сохраняет в data/assets/.
	•	Exporter (exporter.py) — сохраняет JSONL, JSON, SQL import; генерирует rendered.html preview.
	•	Storage — файловая структура: data/raw_html/, data/rendered_html/, data/assets/, data/json/.
	•	Monitoring — log + metrics exporter.

4. Sequence diagram (high-level)
	1.	CLI start → Fetcher requests init page.
	2.	Fetcher returns HTML → Renderer renders → returns rendered HTML.
	3.	Extractor parses rendered HTML → returns blocks.
	4.	Normalizer transforms blocks → writes JSON.
	5.	ImageFetcher collects images referenced → stores assets.
	6.	Exporter writes artifacts + emits metrics.

5. Контракты / интерфейсы (функциональные сигнатуры)

fetcher.py

def fetch_url(url: str, timeout: int = 10, headers: dict | None = None) -> Tuple[int, bytes]
# returns (http_status, body_bytes) or raises FetchError

renderer.py

def render_html(raw_html: bytes, base_url: str, wait_for: str | None = None, timeout: int = 10) -> str
# returns rendered HTML (utf-8 string), raises RenderTimeoutError / RenderCrashError

extractor.py

def extract_blocks(rendered_html: str) -> List[Dict]
# each dict: {block_id, guid, raw_html, mathml_chunks, images, meta}

normalizer.py

def normalize_block(block: Dict) -> Dict
# returns structured problem dict (see problem_schema_v1.0)

exporter.py

def save_problem(problem: Dict, out_dir: str) -> str
# returns path to saved json

6. Data flows и форматы
	•	Input: URL / raw HTML.
	•	Intermediate: rendered_html (UTF-8), DOM snapshots.
	•	Output: problem_schema_v1.0 JSON (см. ICD), images saved as files with stable naming proj_guid_index.ext.

7. Надёжность и fallback
	•	Primary fetch: requests with system CA certs.
	•	If SSL verification fails or requests can’t execute JS, fallback: Playwright navigate page and grab page.content() (рендеринг JS/MathJax).
	•	Timeout стратегия: retry up to 3 times with exponential backoff (0.5s, 1s, 2s).
	•	Throttling: default global rate ≤ 1 req/сек (configurable).

8. Performance targets
	•	P95 render latency per page: ≤ 3s (single Playwright context).
	•	Throughput: 20 pages/minute on a modest VM (2 vCPU, 4GB RAM) with pooling contexts.
	•	Memory per context: < 400 MB.

9. Error handling и классы ошибок
	•	FetchError, RenderTimeoutError, ParseError, ImageDownloadError, NormalizationError.
	•	Персистентные ошибки логируются и создают debug dump в debug_pages/.

10. Deployment considerations
	•	Runable as CLI in CI, containerized via Dockerfile, with optional GPU not required.
	•	Secrets: none (public scraping), but store Playwright browser in CI artifacts.

11. Security & compliance
	•	Respect robots.txt (configurable); include --ignore-robots flag with explicit consent.
	•	Rate-limit to avoid DOS.
	•	Do not attempt to log in or scrape gated content.

12. Integration points
	•	Exported JSONL consumed downstream by embedding pipeline (Qdrant), FastAPI endpoints, PWA.
