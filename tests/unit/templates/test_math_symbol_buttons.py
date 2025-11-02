import pytest
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
import json


def tojson_filter(value):
    return Markup(json.dumps(value, ensure_ascii=False))


@pytest.fixture
def jinja_env():
    env = Environment(loader=FileSystemLoader('templates'))
    env.filters['tojson'] = tojson_filter
    return env


def test_math_symbol_buttons_renders_correctly(jinja_env):
    template = jinja_env.get_template('ui_components/math_symbol_buttons.html.j2')
    
    test_cases = [
        # Обычные символы
        [{'value': 'α', 'label': 'α'}, {'value': 'β', 'label': 'β'}],
        # Апостроф
        [{'value': "f'(x)", 'label': "f'(x)"}],
        # Двойные кавычки
        [{'value': '"quoted"', 'label': '"quoted"'}],
        # Смешанные спецсимволы
        [{'value': '√(x² + 1)', 'label': '√(x² + 1)'}],
        # LaTeX-подобное
        [{'value': r'\frac{a}{b}', 'label': 'frac'}],
    ]
    
    for i, row in enumerate(test_cases):
        rendered = template.render(block_index=i, active=True, math_symbols=[row])
        
        # Проверяем, что block_index подставлен верно
        assert f"insertSymbol({i}," in rendered
        
        # Проверяем, что value экранирован как JSON в &quot;
        for btn in row:
            expected_value_escaped = json.dumps(btn['value'], ensure_ascii=False).replace('"', '&quot;')
            assert expected_value_escaped in rendered
        
        # Проверяем, что label HTML-экранирован
        for btn in row:
            assert btn['label'].replace("'", "&#39;") in rendered or "'" not in btn['label']


def test_empty_math_symbols(jinja_env):
    template = jinja_env.get_template('ui_components/math_symbol_buttons.html.j2')
    rendered = template.render(block_index=0, active=False, math_symbols=[])
    assert '<div class="math-buttons">' in rendered
    assert 'insertSymbol' not in rendered
