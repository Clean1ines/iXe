# tests/test_utils_element_pairer.py

import unittest
from bs4 import BeautifulSoup
from bs4.element import Tag
from utils.element_pairer import ElementPairer
import re

class TestElementPairer(unittest.TestCase):

    def setUp(self):
        self.pairer = ElementPairer()

    def test_pair_simple_case(self):
        html = """
        <html>
        <body>
            <div id="i1">Header 1</div>
            <div class="qblock">Question 1</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        # Проверка типа результата
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        pair = result[0]
        self.assertIsInstance(pair, tuple)
        self.assertEqual(len(pair), 2)
        self.assertIsInstance(pair[0], Tag)
        self.assertIsInstance(pair[1], Tag)

        # Проверка содержимого тегов
        self.assertEqual(pair[0].get_text(strip=True), "Header 1")
        self.assertEqual(pair[1].get_text(strip=True), "Question 1")

    def test_pair_multiple_pairs(self):
        html = """
        <html>
        <body>
            <div id="i1">Header 1</div>
            <div class="qblock">Question 1</div>
            <div id="i2">Header 2</div>
            <div class="qblock">Question 2</div>
            <div id="i3">Header 3</div>
            <div class="qblock">Question 3</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

        expected_pairs = [
            ("Header 1", "Question 1"),
            ("Header 2", "Question 2"),
            ("Header 3", "Question 3"),
        ]

        for i, (header_text, qblock_text) in enumerate(expected_pairs):
            pair = result[i]
            self.assertIsInstance(pair, tuple)
            self.assertEqual(len(pair), 2)
            self.assertIsInstance(pair[0], Tag)
            self.assertIsInstance(pair[1], Tag)
            self.assertEqual(pair[0].get_text(strip=True), header_text)
            self.assertEqual(pair[1].get_text(strip=True), qblock_text)

    def test_pair_unpaired_elements(self):
        html = """
        <html>
        <body>
            <div id="i1">Header 1</div>
            <div class="qblock">Question 1</div>
            <div id="i2">Unpaired Header</div>
            <div class="other">Other Element</div>
            <div class="qblock">Unpaired Question</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        # Ожидаем только 1 сопряженную пару
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        pair = result[0]
        self.assertIsInstance(pair, tuple)
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0].get_text(strip=True), "Header 1")
        self.assertEqual(pair[1].get_text(strip=True), "Question 1")

    def test_pair_no_elements(self):
        html = """
        <html>
        <body>
            <p>Some other content</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_pair_empty_soup(self):
        html = ""
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_pair_complex_structure(self):
        html = """
        <html>
        <body>
            <script>console.log('test');</script>
            <div id="i1">
                <h2>Header 1</h2>
                <span>Extra content</span>
            </div>
            <div class="qblock">
                <p>Question 1 content</p>
                <div class="nested">Nested div</div>
            </div>
            <div class="other">Other content</div>
            <div class="qblock">
                <p>Unpaired Question</p>
            </div>
            <div id="i2">
                <h2>Header 2</h2>
            </div>
            <div class="qblock">
                <p>Question 2 content</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = self.pairer.pair(soup)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Проверка первой пары
        first_pair = result[0]
        self.assertIsInstance(first_pair, tuple)
        self.assertEqual(len(first_pair), 2)
        self.assertIn("Header 1", first_pair[0].get_text())
        self.assertIn("Question 1", first_pair[1].get_text())

        # Проверка второй пары
        second_pair = result[1]
        self.assertIsInstance(second_pair, tuple)
        self.assertEqual(len(second_pair), 2)
        self.assertIn("Header 2", second_pair[0].get_text())
        self.assertIn("Question 2", second_pair[1].get_text())


if __name__ == '__main__':
    unittest.main()
