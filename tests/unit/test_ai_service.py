"""
Unit tests for AI service with enum-based classification.
"""

import json
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification, DocumentType


@pytest.fixture
def mock_logger(tmp_path):
    """Create a test logger."""
    return Logger(
        log_dir=tmp_path / "logs",
        component="test_ai_service",
        log_level="INFO",
        log_to_event_log=False,
    )


@pytest.fixture
def mock_error_handler():
    """Create a test error handler."""
    return ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)


@pytest.fixture
def ai_service(mock_error_handler, mock_logger):
    """Create an AI service instance for testing."""
    return AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=mock_error_handler,
        logger=mock_logger,
    )


def test_get_supported_document_types_returns_enum_values(ai_service):
    """Test that get_supported_document_types returns enum category values."""
    supported_types = ai_service.get_supported_document_types()
    
    # Should return all enum values except OTHER
    expected_count = len(DocumentType) - 1  # Exclude OTHER
    assert len(supported_types) == expected_count
    
    # Verify all returned types are enum values
    enum_values = [dt.value for dt in DocumentType if dt != DocumentType.OTHER]
    for doc_type in supported_types:
        assert doc_type in enum_values


def test_classification_is_standard_category_for_enum_match():
    """Test that is_standard_category returns True for enum values."""
    classification = Classification(
        document_type="Medical Report",
        confidence=0.95,
        identifiers={},
        raw_response={},
    )
    
    assert classification.is_standard_category is True


def test_classification_is_standard_category_for_specific_type():
    """Test that is_standard_category returns False for specific types."""
    classification = Classification(
        document_type="Panel List",
        confidence=0.95,
        identifiers={},
        raw_response={},
    )
    
    assert classification.is_standard_category is False


def test_classification_is_other_for_other_prefix():
    """Test that is_other returns True for OTHER_ prefix."""
    classification = Classification(
        document_type="OTHER_Unidentified Medical Form",
        confidence=0.5,
        identifiers={},
        raw_response={},
    )
    
    assert classification.is_other is True


def test_classification_is_other_for_standard_category():
    """Test that is_other returns False for standard categories."""
    classification = Classification(
        document_type="Medical Report",
        confidence=0.95,
        identifiers={},
        raw_response={},
    )
    
    assert classification.is_other is False


def test_classify_document_with_enum_category(ai_service):
    """Test classification with standard enum category."""
    # Create test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock OpenAI response with enum category
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Medical Report",
                        "confidence": 0.95,
                        "identifiers": {"plaintiff_name": "John Doe"},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        result = ai_service.classify_document(image)
        
        assert isinstance(result, Classification)
        assert result.document_type == "Medical Report"
        assert result.is_standard_category is True
        assert result.is_other is False


def test_classify_document_with_specific_type(ai_service):
    """Test classification with specific document type."""
    # Create test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock OpenAI response with specific type
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Panel List",
                        "confidence": 0.90,
                        "identifiers": {"case_number": "12345"},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        result = ai_service.classify_document(image)
        
        assert isinstance(result, Classification)
        assert result.document_type == "Panel List"
        assert result.is_standard_category is False
        assert result.is_other is False


def test_classify_document_with_other_fallback(ai_service):
    """Test classification with OTHER fallback."""
    # Create test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock OpenAI response with OTHER fallback
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "OTHER_Unidentified Medical Form",
                        "confidence": 0.50,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        result = ai_service.classify_document(image)
        
        assert isinstance(result, Classification)
        assert result.document_type == "OTHER_Unidentified Medical Form"
        assert result.is_standard_category is False
        assert result.is_other is True


def test_system_prompt_includes_prioritized_classification(ai_service):
    """Test that system prompt includes prioritized classification logic."""
    # Create test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock OpenAI response
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Medical Report",
                        "confidence": 0.95,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        ai_service.classify_document(image)
        
        # Get the system prompt from the call
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]
        system_prompt = system_message["content"]
        
        # Verify prioritized classification approach is in prompt
        assert "PRIORITY 1" in system_prompt
        assert "PRIORITY 2" in system_prompt
        assert "PRIORITY 3" in system_prompt
        assert "Standard Categories" in system_prompt
        assert "Specific Type" in system_prompt
        assert "OTHER_" in system_prompt
        
        # Verify enum categories are described
        assert "MEDICAL_REPORT" in system_prompt
        assert "COURT_ORDER" in system_prompt
        assert "INSURANCE_CORRESPONDENCE" in system_prompt


def test_system_prompt_includes_all_enum_categories(ai_service):
    """Test that system prompt includes all enum categories."""
    # Create test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock OpenAI response
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Medical Report",
                        "confidence": 0.95,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        ai_service.classify_document(image)
        
        # Get the system prompt from the call
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]
        system_prompt = system_message["content"]
        
        # Verify all enum categories (except OTHER) are in the prompt
        expected_categories = [
            "MEDICAL_REPORT",
            "INJURY_REPORT",
            "CLAIM_FORM",
            "DEPOSITION",
            "EXPERT_WITNESS_REPORT",
            "SETTLEMENT_AGREEMENT",
            "COURT_ORDER",
            "INSURANCE_CORRESPONDENCE",
            "WAGE_STATEMENT",
            "VOCATIONAL_REPORT",
            "IME_REPORT",
            "SURVEILLANCE_REPORT",
            "SUBPOENA",
            "MOTION",
            "BRIEF",
        ]
        
        for category in expected_categories:
            assert category in system_prompt, f"Category {category} not found in system prompt"


def test_enum_category_mapping_examples(ai_service):
    """Test that common document types map to correct enum categories."""
    # Test cases: (input document type, expected to be standard category)
    test_cases = [
        ("Medical Report", True),
        ("QME Report", False),  # Specific type, not enum value
        ("Court Order", True),
        ("Finding and Award", False),  # Specific type, not enum value
        ("Insurance Correspondence", True),
        ("Panel List", False),  # Specific type, not enum value
        ("OTHER_Unknown Document", False),  # OTHER fallback
    ]
    
    for doc_type, should_be_standard in test_cases:
        classification = Classification(
            document_type=doc_type,
            confidence=0.95,
            identifiers={},
            raw_response={},
        )
        
        assert classification.is_standard_category == should_be_standard, \
            f"Document type '{doc_type}' standard category check failed"
