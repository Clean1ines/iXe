import unittest
from processors import html_renderer, ui_components


class TestHTMLRenderer(unittest.TestCase):
    """
    Tests for the HTMLRenderer class in processors/html_renderer.py.
    """

    def setUp(self):
        """Set up the HTMLRenderer instance for tests."""
        self.renderer = html_renderer.HTMLRenderer()

    def test_render_returns_string(self):
        """Test that the render method returns a string."""
        test_data = {
            "page_name": "test_page",
            "blocks_html": ["<p>Block 1 content</p>"],
            "assignments": ["Assignment 1 text"]
        }
        result = self.renderer.render(test_data)
        self.assertIsInstance(result, str)

    def test_render_includes_page_name_in_title(self):
        """Test that the rendered HTML includes the page name in the title."""
        test_data = {
            "page_name": "init",
            "blocks_html": ["<p>Block 1 content</p>"],
            "assignments": ["Assignment 1 text"]
        }
        result = self.renderer.render(test_data)
        self.assertIn("<title>FIPI Page init</title>", result)

    def test_render_includes_mathjax_script(self):
        """Test that the rendered HTML includes the MathJax script tag."""
        test_data = {
            "page_name": "test_page",
            "blocks_html": ["<p>Block 1 content</p>"],
            "assignments": ["Assignment 1 text"]
        }
        result = self.renderer.render(test_data)
        self.assertIn("MathJax.js?config=TeX-MML-AM_CHTML", result)

    def test_render_includes_blocks_content(self):
        """Test that the rendered HTML includes the content from blocks_html."""
        test_block_content = "<p>Specific block content to find</p>"
        test_data = {
            "page_name": "test_page",
            "blocks_html": [test_block_content],
            "assignments": ["Assignment 1 text"]
        }
        result = self.renderer.render(test_data)
        self.assertIn(test_block_content, result)

    def test_render_includes_answer_form(self):
        """Test that the rendered HTML includes the answer form structure."""
        test_data = {
            "page_name": "test_page",
            "blocks_html": ["<p>Block 1 content</p>"],
            "assignments": ["Assignment 1 text"]
        }
        result = self.renderer.render(test_data)
        # Check for key elements of the form
        self.assertIn('<form class="answer-form"', result)
        self.assertIn('onsubmit="submitAndCheckAnswer(event,', result) # Should reference block index
        self.assertIn('<label for="answer_', result) # Should reference block index
        self.assertIn('<input type="text" id="answer_', result) # Should reference block index
        self.assertIn('name="answer"', result)
        self.assertIn('maxlength="250"', result)
        self.assertIn('placeholder="Введите/соберите ответ"', result)
        self.assertIn('class="toggle-math-btn"', result)
        self.assertIn('class="math-buttons"', result)
        self.assertIn('<button type="submit">Отправить ответ</button>', result)

    def test_render_includes_data_attributes_from_metadata(self):
        """Test that the rendered HTML includes data-task-id and data-form-id from metadata."""
        test_block_content = "<p>Block 1 content</p>"
        task_id = "TASK789"
        form_id = "FORM101"
        test_data = {
            "page_name": "test_page",
            "blocks_html": [test_block_content],
            "assignments": ["Assignment 1 text"],
            "task_metadata": [{"task_id": task_id, "form_id": form_id}] # Предполагаемая структура
        }
        result = self.renderer.render(test_data)
        # Проверяем, что атрибуты встроены в первый (и единственный) блок (с одинарными кавычками)
        self.assertIn(f"data-task-id='{task_id}'", result)
        self.assertIn(f"data-form-id='{form_id}'", result)

    def test_render_block_returns_string(self):
        """Test that the render_block method returns a string."""
        block_html = "<p>Single block content</p>"
        block_index = 0
        result = self.renderer.render_block(block_html, block_index)
        self.assertIsInstance(result, str)

    def test_render_block_includes_block_index_in_title(self):
        """Test that the rendered block HTML includes the block index in the title."""
        block_html = "<p>Single block content</p>"
        block_index = 5
        result = self.renderer.render_block(block_html, block_index)
        self.assertIn(f"<title>FIPI Block {block_index}</title>", result)

    def test_render_block_includes_mathjax_script(self):
        """Test that the rendered block HTML includes the MathJax script tag."""
        block_html = "<p>Single block content</p>"
        block_index = 0
        result = self.renderer.render_block(block_html, block_index)
        self.assertIn("MathJax.js?config=TeX-MML-AM_CHTML", result)

    def test_render_block_includes_passed_content(self):
        """Test that the rendered block HTML includes the passed block_html."""
        test_block_content = "<div>Unique block content</div>"
        block_index = 0
        result = self.renderer.render_block(test_block_content, block_index)
        self.assertIn(test_block_content, result)

    def test_render_block_includes_answer_form(self):
        """Test that the rendered block HTML includes the answer form for that block."""
        block_html = "<p>Single block content</p>"
        block_index = 2
        result = self.renderer.render_block(block_html, block_index)
        # Check for key elements of the form, referencing the correct index
        self.assertIn('<form class="answer-form"', result)
        self.assertIn(f'onsubmit="submitAndCheckAnswer(event, {block_index})"', result)
        self.assertIn(f'<label for="answer_{block_index}">', result)
        self.assertIn(f'<input type="text" id="answer_{block_index}"', result)
        self.assertIn('name="answer"', result)
        self.assertIn('maxlength="250"', result)
        self.assertIn('placeholder="Введите/соберите ответ"', result)
        self.assertIn('class="toggle-math-btn"', result)
        self.assertIn('class="math-buttons"', result)
        self.assertIn('<button type="submit">Отправить ответ</button>', result)

    def test_render_block_includes_data_attributes(self):
        """Test that the rendered block HTML includes data-task-id and data-form-id."""
        block_html = "<p>Single block content</p>"
        block_index = 3
        task_id = "TASK123"
        form_id = "FORM456"
        result = self.renderer.render_block(block_html, block_index, task_id=task_id, form_id=form_id)
        # Check for data attributes in the processed_qblock div (с одинарными кавычками)
        self.assertIn(f"data-task-id='{task_id}'", result)
        self.assertIn(f"data-form-id='{form_id}'", result)


    def test_render_block_handles_asset_prefix(self):
        """Test that the render_block method correctly adjusts asset paths if prefix is provided."""
        block_html_with_img = '<p>Question</p><img src="assets/test_image.jpg" alt="Test Image"><p>Answer area</p>'
        block_index = 1
        asset_prefix = "../assets"
        result = self.renderer.render_block(block_html_with_img, block_index, asset_path_prefix=asset_prefix)
        
        # The image path should be adjusted
        expected_img_src = f'src="{asset_prefix}/test_image.jpg"'
        self.assertIn(expected_img_src, result)
        # The original path should not be present
        self.assertNotIn('src="assets/test_image.jpg"', result)

        # Other parts of the block HTML should remain
        self.assertIn('<p>Question</p>', result)
        self.assertIn('<p>Answer area</p>', result)
        self.assertIn('alt="Test Image"', result)

    def test_save_writes_to_file(self):
        """Test that the save method writes the HTML string to a file."""
        import tempfile
        import os

        test_html = "<html><body>Test content</body></html>"
        # Use a temporary file to avoid side effects
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as tmp_file:
            temp_filename = tmp_file.name

        try:
            self.renderer.save(test_html, temp_filename)
            # Check if the file was created and contains the correct content
            self.assertTrue(os.path.exists(temp_filename))
            with open(temp_filename, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            self.assertEqual(saved_content, test_html)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_clean_css_removes_empty_rules(self):
        """Test that the _clean_css method removes empty CSS rules."""
        # Access the private method for testing
        raw_css = ".class1 { color: red; } .class2 { } .class3 { font-size: 12px; }"
        # ИСПРАВЛЕНО: Ожидаемый результат теперь соответствует реальному поведению регулярного выражения
        # После удаления .class2 { } остаётся один пробел между .class1 и .class3
        expected_cleaned = ".class1 { color: red; } .class3 { font-size: 12px; }"
        result = self.renderer._clean_css(raw_css)
        self.assertEqual(result, expected_cleaned)

    # --- Удалены тесты для _get_answer_form_html и _get_js_functions ---
    # Эти методы больше не существуют в HTMLRenderer.
    # Их логика вынесена в ui_components.
    # Соответствующие тесты должны быть в тестах для ui_components.

# --- Новый класс для тестирования ui_components ---
class TestUIComponents(unittest.TestCase):
    """
    Tests for the UI components in processors/ui_components.py.
    """

    def test_math_symbol_buttons_renderer_returns_string(self):
        """Test that MathSymbolButtonsRenderer.render returns a string."""
        result = ui_components.MathSymbolButtonsRenderer.render(0)
        self.assertIsInstance(result, str)

    def test_math_symbol_buttons_renderer_includes_index(self):
        """Test that MathSymbolButtonsRenderer.render includes the correct block index."""
        idx = 7
        result = ui_components.MathSymbolButtonsRenderer.render(idx)
        # Check for symbol insertion calls with the index
        self.assertIn(f'onclick="insertSymbol({idx},', result)

    def test_math_symbol_buttons_renderer_active_class(self):
        """Test that MathSymbolButtonsRenderer.render includes active class when requested."""
        idx = 0
        result_inactive = ui_components.MathSymbolButtonsRenderer.render(idx, active=False)
        result_active = ui_components.MathSymbolButtonsRenderer.render(idx, active=True)
        self.assertIn('class="math-buttons"', result_inactive)
        self.assertIn('class="math-buttons active"', result_active)
        self.assertNotIn('class="math-buttons active"', result_inactive)
        self.assertIn('class="math-buttons active"', result_active)

    def test_answer_form_renderer_returns_string(self):
        """Test that AnswerFormRenderer.render returns a string."""
        result = ui_components.AnswerFormRenderer().render(0)
        self.assertIsInstance(result, str)

    def test_answer_form_renderer_includes_index(self):
        """Test that AnswerFormRenderer.render includes the correct block index."""
        idx = 7
        result = ui_components.AnswerFormRenderer().render(idx)
        self.assertIn(f'id="answer_{idx}"', result)
        self.assertIn(f'name="answer"', result) # Name should be generic
        self.assertIn(f'onsubmit="submitAndCheckAnswer(event, {idx})"', result) # ИСПРАВЛЕНО: Проверка на submitAndCheckAnswer
        # Should also contain the math buttons HTML which includes the index
        self.assertIn(f'onclick="insertSymbol({idx},', result)

    def test_common_css_is_string(self):
        """Test that the COMMON_CSS constant is a string."""
        self.assertIsInstance(ui_components.COMMON_CSS, str)

    def test_common_js_functions_is_string(self):
        """Test that the COMMON_JS_FUNCTIONS constant is a string."""
        self.assertIsInstance(ui_components.COMMON_JS_FUNCTIONS, str)


if __name__ == '__main__':
    unittest.main()
