import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any
from bs4.element import Tag
from domain.interfaces.html_processor import IHTMLProcessor

class TaskInfoProcessor(IHTMLProcessor):
    """
    Processes task info buttons, updating onclick attributes.
    """
    
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single HTML block pair and return structured data.
        This method processes task info buttons, updating onclick attributes.
        """
        # Convert the qblock content to string for processing
        qblock_content = str(qblock)
        
        # Update onclick attributes for task info buttons
        # Look for onclick attributes that contain ShowTaskInfo calls
        pattern = r"onclick=[\"']javascript:ShowTaskInfo\([^)]+\)[\"']"
        updated_content = re.sub(pattern, 
                                f'onclick="javascript:ShowTaskInfo(\'{block_index}\')"', 
                                qblock_content)
        
        # Parse back to BeautifulSoup object
        updated_qblock = BeautifulSoup(updated_content, 'html.parser').find('div', class_='qblock')
        if not updated_qblock:
            # If no qblock found, return the first div
            updated_qblock = BeautifulSoup(updated_content, 'html.parser').find('div')
        
        # Return the processed block data
        return {
            'header_container': header_container,
            'qblock': updated_qblock,
            'block_index': block_index,
            'subject': subject,
            'base_url': base_url
        }

    async def process(self, content: str, context: dict):
        """
        Process HTML content string and return updated content with metadata.
        This method is needed to maintain compatibility with the existing codebase
        that calls .process() on TaskInfoProcessor instances.
        """
        # Parse the content string to BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all elements that might have ShowTaskInfo onclick attributes
        elements_with_onclick = soup.find_all(attrs={"onclick": re.compile(r"javascript:ShowTaskInfo")})
        
        # Update the onclick attributes to use the block_index from context if available
        block_index = context.get('block_index', 0)
        for element in elements_with_onclick:
            original_onclick = element.get('onclick', '')
            updated_onclick = re.sub(
                r"onclick=[\"']javascript:ShowTaskInfo\([^)]+\)[\"']",
                f'onclick="javascript:ShowTaskInfo(\'{block_index}\')"',
                original_onclick
            )
            element['onclick'] = updated_onclick
        
        # Return the updated content and metadata
        return str(soup), {'processed_by': 'TaskInfoProcessor', 'elements_updated': len(elements_with_onclick)}
