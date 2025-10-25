class AnswerFormRenderer:
    """
    Renders the HTML for the interactive answer form for a specific block.
    """

    def __init__(self):
        """
        Initializes the AnswerFormRenderer.
        """
        self.math_buttons_renderer = MathSymbolButtonsRenderer()
        logger.debug("AnswerFormRenderer initialized with MathSymbolButtonsRenderer instance")

    def render(self, block_index: int) -> str:
        """
        Generates the HTML for the interactive answer form for a specific block using a Jinja2 template.

        Args:
            block_index (int): The index of the assignment block.

        Returns:
            str: The HTML string for the form.
        """
        logger.debug(f"Rendering AnswerForm for block_index: {block_index}")
        # Pass the MathSymbolButtonsRenderer instance to the template context
        template = jinja_env.get_template("answer_form.html.j2")
        html_content = template.render(
            block_index=block_index,
            math_buttons_renderer=self.math_buttons_renderer
        )
        logger.debug(f"Generated HTML for AnswerForm block_index: {block_index}, length: {len(html_content)} characters")
        return html_content
