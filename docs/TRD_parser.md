Technical Requirements Document (TRD) — FIPI Parser

Версия: 1.0

1. Обозначения
	•	MUST — обязательное.
	•	SHOULD — желательное.
	•	MAY — опционально.

2. Функциональные требования (с ID)

ID	Текст требования	Priority	Verification
TRD-PAR-001	Парсер должен корректно извлекать qblocks (вся структура задания) со страниц проекта bank/questions.php (proj param).	MUST	AC-001
TRD-PAR-002	MathML / MathJax в блоках должны рендериться и сохраняться как: raw MathML (если есть) + LaTeX верно экстрагированный.	MUST	AC-002
TRD-PAR-003	Изображения (внутри блоков и схемы) должны скачиваться локально и путь должен быть прописан в JSON.	MUST	AC-003
TRD-PAR-004	При неудаче при обычном HTTP/requests парсер использует Playwright fallback и сохраняет rendered HTML.	MUST	AC-004
TRD-PAR-005	Структура выходного JSON должна соответствовать problem_schema_v1.0 (см. ICD).	MUST	AC-005
TRD-PAR-006	CLI должен уметь “resume from last_page” и логировать progress в state/last_run.json.	MUST	AC-006
TRD-PAR-007	Парсер должен иметь throttle-конфиг: max_requests_per_sec (default=1) и max_concurrent_renderers (default=2).	SHOULD	AC-007
TRD-PAR-008	Дубли MathJax/HTML (видимые в предварительном выводе) должны нормализовываться (удаляться дубли).	MUST	AC-008
TRD-PAR-009	Кодировка cp1251 должна корректно конвертироваться; fallback: detect via chardet.	MUST	AC-009
TRD-PAR-010	Output должен включать rendered.html preview и debug_pages/* для каждой страницы.	SHOULD	AC-010
TRD-PAR-011	Экспорт в JSONL должен поддерживать versioning: "schema_version": "problem_schema_v1.0".	MUST	AC-011

3. Нефункциональные требования

ID	Requirement	Priority
TRD-PAR-NF-001	Логирование: structured logs (JSON) + debug dumps; retain 7 days.	MUST
TRD-PAR-NF-002	Тесты: unit tests ≥ 80% покрытия core modules.	SHOULD
TRD-PAR-NF-003	CI: тесты и lint на PR.	MUST
TRD-PAR-NF-004	Производительность: P95 render ≤ 3s	SHOULD

4. Acceptance criteria (связанные)

(смотрите docs/QA_plan_parser.md для деталей). Каждый TRD-пункт имеет связанный AC-XXX.
