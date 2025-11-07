"""HTML processing pipeline with distinct stages."""

from typing import List, Tuple, Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class ProcessingStage(ABC):
    """Abstract base class for processing stages."""

    @abstractmethod
    async def execute(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Execute the processing stage.

        Args:
            content: Input content to process
            context: Processing context

        Returns:
            Tuple of processed content and updated metadata
        """
        pass


class AssetProcessingStage(ProcessingStage):
    """Stage for processing assets (images, files)."""

    async def execute(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process assets in the HTML content.

        Args:
            content: HTML content
            context: Processing context

        Returns:
            Tuple of processed content and metadata
        """
        # This stage would handle asset downloading and URL rewriting
        # For now, we'll just return the content as-is with empty metadata
        # The actual asset processing would be delegated to processors that implement IHTMLProcessor
        metadata = context.get('metadata', {})
        metadata['assets_processed'] = True
        return content, metadata


class ContentExtractionStage(ProcessingStage):
    """Stage for content extraction and cleaning."""

    async def execute(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Extract and clean content from HTML.

        Args:
            content: HTML content
            context: Processing context

        Returns:
            Tuple of processed content and metadata
        """
        # This stage would handle content cleaning (removing unwanted elements, etc.)
        # For now, we'll just return the content as-is with empty metadata
        metadata = context.get('metadata', {})
        metadata['content_extracted'] = True
        return content, metadata


class MetadataExtractionStage(ProcessingStage):
    """Stage for metadata extraction."""

    async def execute(self, content: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Extract metadata from HTML content.

        Args:
            content: HTML content
            context: Processing context

        Returns:
            Tuple of processed content and metadata
        """
        # This stage would handle metadata extraction using utils/metadata_extractor
        # For now, we'll just return the content as-is with empty metadata
        metadata = context.get('metadata', {})
        metadata['metadata_extracted'] = True
        return content, metadata


class HTMLProcessingPipeline:
    """Pipeline for processing HTML content through distinct stages."""

    def __init__(self, stages: List[ProcessingStage]):
        """
        Initialize the pipeline.

        Args:
            stages: List of processing stages to execute in order
        """
        self.stages = stages

    async def process(self, content: str, initial_context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Process content through all stages of the pipeline.

        Args:
            content: Input content to process
            initial_context: Initial processing context

        Returns:
            Tuple of final processed content and aggregated metadata
        """
        if initial_context is None:
            initial_context = {}

        current_content = content
        current_context = initial_context.copy()

        for i, stage in enumerate(self.stages):
            logger.debug(f"Executing pipeline stage {i+1}/{len(self.stages)}: {type(stage).__name__}")
            current_content, stage_metadata = await stage.execute(current_content, current_context)
            current_context.update(stage_metadata)

        return current_content, current_context
