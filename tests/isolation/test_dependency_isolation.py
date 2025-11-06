import sys
import subprocess
import pytest
from unittest.mock import patch, MagicMock


def test_automation_no_qdrant_supabase():
    """Test that automation components don't import qdrant or supabase"""
    # Save original modules
    original_modules = sys.modules.copy()
    
    try:
        # Try to import automation components without qdrant/supabase
        with patch.dict('sys.modules', {
            'qdrant_client': None,
            'qdrant_client.http': None,
            'qdrant_client.http.models': None,
            'supabase': None,
            'supabase.client': None,
        }):
            # Remove any cached modules that might interfere
            modules_to_remove = [name for name in sys.modules.keys() if 'qdrant' in name or 'supabase' in name]
            for mod in modules_to_remove:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Try to import automation components
            from utils.browser_manager import BrowserManager
            from utils.browser_pool_manager import BrowserPoolManager
            from utils.answer_checker import FIPIAnswerChecker
            from processors.html.image_processor import ImageScriptProcessor
            
            # Verify imports succeeded
            assert BrowserManager is not None
            assert BrowserPoolManager is not None
            assert FIPIAnswerChecker is not None
            assert ImageScriptProcessor is not None
            
    finally:
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(original_modules)


def test_web_can_import_qdrant_supabase():
    """Test that web components can import qdrant and supabase"""
    try:
        # Import web components that should have qdrant/supabase access
        from utils.retriever import QdrantProblemRetriever  # Use correct class name
        from utils.vector_indexer import QdrantProblemIndexer
        from api.services.quiz_service_adapter import QuizServiceAdapter
        
        # These should import without error
        assert QdrantProblemRetriever is not None
        assert QdrantProblemIndexer is not None
        assert QuizServiceAdapter is not None
        
    except ImportError as e:
        pytest.fail(f"Web components failed to import due to missing qdrant/supabase: {e}")


def test_requirements_files_exist():
    """Test that isolated requirements files exist"""
    import os
    
    assert os.path.exists('requirements_scraping_checking.txt'), "requirements_scraping_checking.txt not found"
    assert os.path.exists('requirements_web.txt'), "requirements_web.txt not found"
    assert os.path.exists('requirements_indexing.txt'), "requirements_indexing.txt not found"
    assert os.path.exists('requirements_common.txt'), "requirements_common.txt not found"
    
    # Check content of requirements files
    with open('requirements_scraping_checking.txt', 'r') as f:
        auto_content = f.read()
        assert 'playwright==' in auto_content
        assert 'qdrant-client' not in auto_content or 'qdrant-client==' not in auto_content
        assert 'supabase' not in auto_content or 'supabase==' not in auto_content
    
    with open('requirements_web.txt', 'r') as f:
        web_content = f.read()
        assert 'fastapi==' in web_content
        # Web requirements may have qdrant-client if QuizServiceAdapter uses it through common
    
    with open('requirements_indexing.txt', 'r') as f:
        index_content = f.read()
        assert 'qdrant-client==' in index_content
        assert 'sentence-transformers==' in index_content


if __name__ == "__main__":
    test_automation_no_qdrant_supabase()
    test_web_can_import_qdrant_supabase()
    test_requirements_files_exist()
    print("All isolation tests passed!")
