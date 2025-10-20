QA & Verification Plan — Parser

1. Traceability matrix (snippet)

TRD ID	AC ID (QA)	Test Type	Test Name
TRD-PAR-001	AC-001	Integration	test_extract_qblocks_end_to_end
TRD-PAR-002	AC-002	Unit/Integration	test_mathml_to_latex_conversion
TRD-PAR-003	AC-003	Integration	test_images_downloaded_and_linked
TRD-PAR-004	AC-004	Integration	test_ssl_fallback_playwright
TRD-PAR-005	AC-005	Schema validation	test_output_schema_conformance

2. Acceptance criteria (детальные, тестируемые)

AC-001 (Extract qblocks)
	•	Given: rendered page debug_pages/page_init.html
	•	When: run extractor.extract_blocks(rendered_html)
	•	Then: returns len(blocks) >= expected_count and each block contains block_id, guid, raw_html.

Automated test: fixture with sample rendered HTML -> assert extraction yields >=10 blocks.

AC-002 (MathML → LaTeX)
	•	Given: block with MathML
	•	When: normalizer.mathml_to_latex(mathml_str)
	•	Then: returns LaTeX string, test equality with expected (unit test file uses canonical pairs).
	•	Metric: conversion accuracy on 100-sample set ≥ 95%.

AC-003 (Images)
	•	Given: block with <img src="...">
	•	When: image_fetcher.fetch_and_save(img_url)
	•	Then: file saved under data/assets/<proj>/<guid>/<filename> and problem.images entry filled.

AC-004 (SSL fallback)
	•	Given: mocked requests raising SSLError
	•	When: call fetcher.fetch_url(url)
	•	Then: fallback uses playwright and returns 200 + rendered HTML; test asserts meta.fetch_method == "playwright".

AC-005 (Schema)
	•	Given: output JSON
	•	When: run jsonschema.validate(output, problem_schema_v1.0)
	•	Then: no validation errors.

3. Test harness & CI
	•	Use pytest, jsonschema, fixtures under tests/fixtures/.
	•	CI jobs:
	•	lint (flake8/isort)
	•	unit (pytest -k unit)
	•	integration (pytest -k integration) — may be gated in PR.
	•	Test data: tests/data/sample_rendered_page_1.html etc.

4. Manual QA checklist
	•	Просмотреть rendered.html для первых 10 страниц.
	•	Убедиться, что MathJax корректно отрендерился.
	•	Проверить, что для каждого блока есть guid.
	•	Проверить отсутствие видимых дублирований (например, a → (25;0) a → (25;0)).
	•	Проверить корректность кодировки русского текста.

5. Regression & Acceptance
	•	Regression tests будут запускаться при каждом PR.
	•	Acceptance: main branch имеет все интеграционные тесты green, и sample dataset 100 задач сохранён в S3/артифакте.
