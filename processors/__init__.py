# processors/__init__.py
from .html_renderer import HTMLRenderer
from .json_saver import JSONSaver
# Импортируем новый модуль, чтобы его компоненты были доступны
from . import ui_components

__all__ = ["HTMLRenderer", "JSONSaver", "ui_components"]