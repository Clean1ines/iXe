import pytest
from unittest.mock import Mock
from domain.services.metadata_enhancer import MetadataExtractionService
from services.specification import SpecificationService


class TestMetadataExtractionService:
    """Unit tests for MetadataExtractionService."""

    @pytest.fixture
    def mock_spec_service(self):
        """Create a mock SpecificationService."""
        return Mock(spec=SpecificationService)

    @pytest.fixture
    def metadata_enhancer(self, mock_spec_service):
        """Create a MetadataExtractionService instance with mocked dependencies."""
        return MetadataExtractionService(specification_service=mock_spec_service)

    def test_enhance_metadata_with_kes_codes(self, metadata_enhancer, mock_spec_service):
        """Test enhancement of metadata with KES codes."""
        mock_spec_service.explain_kes.return_value = "Explanation for KES code"
        
        extracted_meta = {
            'kes_codes': ['1.1'],
            'kos_codes': []
        }
        
        result = metadata_enhancer.enhance_metadata(extracted_meta)
        
        mock_spec_service.explain_kes.assert_called_once_with('1.1')
        assert 'kes_explanations' in result
        assert result['kes_explanations'] == ['Explanation for KES code']

    def test_enhance_metadata_with_kos_codes(self, metadata_enhancer, mock_spec_service):
        """Test enhancement of metadata with KOS codes."""
        mock_spec_service.explain_kos.return_value = "Explanation for KOS code"
        
        extracted_meta = {
            'kes_codes': [],
            'kos_codes': ['2.1']
        }
        
        result = metadata_enhancer.enhance_metadata(extracted_meta)
        
        mock_spec_service.explain_kos.assert_called_once_with('2.1')
        assert 'kos_explanations' in result
        assert result['kos_explanations'] == ['Explanation for KOS code']

    def test_enhance_metadata_with_unknown_codes(self, metadata_enhancer, mock_spec_service):
        """Test enhancement when specification service raises an exception."""
        mock_spec_service.explain_kes.side_effect = Exception("Unknown code")
        
        extracted_meta = {
            'kes_codes': ['unknown_code'],
            'kos_codes': []
        }
        
        result = metadata_enhancer.enhance_metadata(extracted_meta)
        
        assert 'kes_explanations' in result
        assert result['kes_explanations'] == ['Unknown KES code: unknown_code']

    def test_enhance_metadata_preserves_original_data(self, metadata_enhancer, mock_spec_service):
        """Test that original metadata is preserved during enhancement."""
        extracted_meta = {
            'kes_codes': ['1.1'],
            'original_field': 'original_value'
        }
        
        result = metadata_enhancer.enhance_metadata(extracted_meta)
        
        assert result['original_field'] == 'original_value'
        assert result['kes_codes'] == ['1.1']
