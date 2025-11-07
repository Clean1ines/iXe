"""Domain service for enhancing metadata using specification data."""

from typing import List, Dict, Any, Optional
from services.specification import SpecificationService


class MetadataExtractionService:
    """Service for enhancing extracted metadata with specification data."""

    def __init__(self, specification_service: SpecificationService):
        """
        Initialize the service.

        Args:
            specification_service: SpecificationService instance for accessing official specs
        """
        self.specification_service = specification_service

    def enhance_metadata(self, extracted_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance extracted metadata with additional information from specifications.

        Args:
            extracted_meta: Dictionary with initially extracted metadata

        Returns:
            Enhanced metadata dictionary
        """
        enhanced_meta = extracted_meta.copy()
        
        kes_codes = extracted_meta.get('kes_codes', [])
        kos_codes = extracted_meta.get('kos_codes', [])
        
        # Add explanations from specification if available
        if kes_codes:
            kes_explanations = []
            for code in kes_codes:
                try:
                    explanation = self.specification_service.explain_kes(code)
                    kes_explanations.append(explanation)
                except Exception:
                    kes_explanations.append(f"Unknown KES code: {code}")
            enhanced_meta['kes_explanations'] = kes_explanations
            
        if kos_codes:
            kos_explanations = []
            for code in kos_codes:
                try:
                    explanation = self.specification_service.explain_kos(code)
                    kos_explanations.append(explanation)
                except Exception:
                    kos_explanations.append(f"Unknown KOS code: {code}")
            enhanced_meta['kos_explanations'] = kos_explanations
        
        return enhanced_meta
