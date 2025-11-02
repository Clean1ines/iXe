import pytest
from unittest.mock import MagicMock
from utils.skill_graph import get_skill_graph_cached, _skill_graph_cache
from utils.skill_graph import InMemorySkillGraph


def test_get_skill_graph_cached_builds_once():
    # Arrange
    global _skill_graph_cache
    _skill_graph_cache = None  # сброс кэша перед тестом

    db_mock = MagicMock()
    spec_mock = MagicMock()

    # Act
    graph1 = get_skill_graph_cached(db_mock, spec_mock)
    graph2 = get_skill_graph_cached(db_mock, spec_mock)

    # Assert
    assert graph1 is graph2, "Кэш должен возвращать один и тот же экземпляр"
    assert isinstance(graph1, InMemorySkillGraph)
    db_mock.get_all_problems.assert_called_once()  # убедитесь, что build вызван один раз
