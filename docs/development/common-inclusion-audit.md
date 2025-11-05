| Файл | Использования | Heavy_deps | Stateful | Решение |
|------|---------------|------------|----------|---------|
| models/database_models.py | 5 | No | No | ✅ В common |
| models/problem_schema.py | 3 | No | No | ✅ В common |
| models/pydantic_models.py | 4 | No | No | ✅ В common |
| utils/model_adapter.py | 2 | No | No | ✅ В common |
| utils/task_id_utils.py | 3 | No | No | ✅ В common |
| utils/subject_mapping.py | 4 | No | No | ✅ В common |
| utils/task_number_inferer.py | 2 | No | No | ✅ В common |
| utils/fipi_urls.py | 5 | No | No | ✅ В common |
| processors/page_processor.py | 2 | Yes (BrowserManager/Playwright) | No | ❌ Исключить |
| processors/block_processor.py | 2 | Yes (BrowserManager/Playwright) | No | ❌ Исключить |
| services/specification.py | 2 | No | No | ✅ В common |
| utils/downloader.py | 2 | Yes (BrowserManager) | No | ❌ Исключить |
| utils/metadata_extractor.py | 1 | Yes (BrowserManager) | No | ❌ Исключить |
| utils/retriever.py | 2 | Yes (qdrant) | No | ❌ Исключить |
| utils/vector_indexer.py | 1 | Yes (qdrant) | No | ❌ Исключить |
| utils/browser_manager.py | 3 | Yes (playwright) | Yes (Singleton) | ❌ Исключить |
| utils/answer_checker.py | 2 | Yes (BrowserManager) | No | ❌ Исключить |
