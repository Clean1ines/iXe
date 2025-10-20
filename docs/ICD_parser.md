Interface Control Document (ICD) — Data schemas & API

1. Problem schema (JSON) — problem_schema_v1.0

{
  "schema_version": "problem_schema_v1.0",
  "problem_id": "string",            // GUID: proj+guid or uuid4
  "proj": "string",                  // project id from source
  "block_id": "string",              // html block id (eg q40B442)
  "guid": "string",                  // original guid field if exists
  "source_page": "integer",
  "source_url": "string",
  "title": "string | null",
  "text_plain": "string",            // plain text (no markup) - utf-8
  "text_latex": "string | null",     // LaTeX representation extracted from MathML
  "html": "string",                  // sanitized rendered HTML for block (trimmed) - safe
  "text_display": "string",          // how it looks for preview (with marked math placeholders)
  "kes_codes": ["string"],           // topics codes
  "kes_descs": ["string"],
  "images": [
    {
      "image_id": "string",
      "orig_url": "string",
      "local_path": "string",
      "width": "int|null",
      "height": "int|null",
      "mime": "string"
    }
  ],
  "answer_type": "short|long|multiple_choice|none",
  "canonical_answer": "string|null",
  "solutions": [{"solution_id":"string","text":"string","author":"string"}],
  "meta": {"raw_fetch_time":"ISO8601","render_time_ms":123, "fetch_method":"requests|playwright"},
  "created_at": "ISO8601"
}

Примечание: html — sanitized (удалены лишние скрипты), MathJax вывел MathML/visible text.

2. CLI contract
	•	parse_fipi.py --proj <proj> --start-page 1 --end-page 100 --out data/json/ --resume
	•	exit codes:
	•	0 success, 1 partial failure (some pages), 2 fatal error.

3. Debug artifacts
	•	debug_pages/page_<n>.html — rendered HTML of page n.
	•	debug_pages/page_<n>_screenshot.png — optional (Playwright).
	•	debug_pages/page_<n>_log.json — structured log.

4. Export formats
	•	data/json/problems.jsonl — newline delimited problems (problem_schema_v1.0).
	•	data/raw_html/<proj>_page_<n>.html — raw.
	•	data/assets/<proj>/<guid>/* — images.

5. API endpoints (internal prototype)

(For integration with FastAPI service)
	•	POST /ingest/problem — accept single problem JSON; returns 201.
	•	POST /ingest/problems — batch upsert.
	•	GET /ingest/status/{proj} — ingestion status.
