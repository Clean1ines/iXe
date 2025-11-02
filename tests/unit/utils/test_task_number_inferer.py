import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest
from utils.task_number_inferer import TaskNumberInferer
from services.specification import SpecificationService


@pytest.fixture
def mock_spec_service():
    """Mock SpecificationService instance with minimal spec data."""
    mock_spec_data = {
        "tasks": [
            {"task_number": 2, "kes_codes": ["7"], "answer_type": "short"},
            {"task_number": 4, "kes_codes": ["6"], "answer_type": "short"},
            {"task_number": 13, "kes_codes": ["4"], "answer_type": "extended"},
        ]
    }
    mock_service = MagicMock(spec=SpecificationService)
    mock_service.spec = mock_spec_data
    return mock_service


@pytest.fixture
def rules_config():
    return {
        "direct_mappings": [
            {"kes_code": "7.5", "task_number": 2},
            {"kes_code": "6.2", "task_number": 4, "answer_type": "short"},
            {"kes_code": "4.2", "task_number": 12},
            {"kes_codes": ["1.5", "1.8"], "task_number": 7}
        ]
    }


def test_infer_returns_none_on_empty_kes_codes(mock_spec_service, rules_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(rules_config))):
        inferer = TaskNumberInferer(mock_spec_service)
        result = inferer.infer([], "short")
        assert result is None


def test_infer_applies_direct_mapping_from_config(mock_spec_service, rules_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(rules_config))):
        inferer = TaskNumberInferer(mock_spec_service)
        assert inferer.infer(["7.5"], "short") == 2
        assert inferer.infer(["6.2"], "short") == 4
        assert inferer.infer(["1.5", "1.8"], "short") == 7


def test_infer_returns_none_on_no_match(mock_spec_service, rules_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(rules_config))):
        inferer = TaskNumberInferer(mock_spec_service)
        result = inferer.infer(["999.999"], "short")
        assert result is None


def test_infer_falls_back_to_spec_candidates_when_no_direct_rule(mock_spec_service, rules_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(rules_config))):
        inferer = TaskNumberInferer(mock_spec_service)
        # KES "7.999" → top-level "7" → candidate task 2
        result = inferer.infer(["7.999"], "short")
        assert result == 2


def test_from_paths_creates_instance():
    """Smoke test for from_paths factory method."""
    try:
        inferer = TaskNumberInferer.from_paths(
            spec_path="data/specs/ege_2026_math_spec.json",
            kes_kos_path="data/specs/ege_2026_math_kes_kos.json"
        )
        assert isinstance(inferer, TaskNumberInferer)
        # Basic inference smoke test
        assert inferer.infer(["7.5"], "short") == 2
    except FileNotFoundError:
        pytest.skip("Specification files not found for integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
