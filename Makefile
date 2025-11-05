install-dev:
	pip install -r dev-requirements.txt

install-common:
	pip install -e ./common

install-web:
	pip install -r requirements_web.txt && make install-common

install-scraping-checking:
	pip install -r requirements_scraping_checking.txt && make install-common

install-indexing:
	pip install -r requirements_indexing.txt && make install-common

analyze-deps-api:
	python audit_requirements.py --path api --path run.py --path services --path models --path config --path templates

analyze-deps-scraper:
	python audit_requirements.py --path scraper --file utils/browser_manager.py --file utils/downloader.py

analyze-deps-checker:
	python audit_requirements.py --file utils/answer_checker.py --file utils/browser_manager.py

analyze-deps-indexer:
	python audit_requirements.py --path utils/vector_indexer.py --path utils/retriever.py --path scripts/index_problems.py

analyze-deps-common:
	python audit_requirements.py --path common

test-reqs:
	pytest tests/requirements/

.PHONY: install-dev install-common install-web install-scraping-checking install-indexing analyze-deps-api analyze-deps-scraper analyze-deps-checker analyze-deps-indexer analyze-deps-common test-reqs
