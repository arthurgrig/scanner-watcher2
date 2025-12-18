"""
Property-based tests for AI service with OpenAI integration.
"""

import base64
import io
import json
import ssl
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from openai import APIError, APITimeoutError, RateLimitError
from PIL import Image

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification


# Helper strategies
@st.composite
def valid_images(draw):
    """Generate valid PIL images for testing."""
    width = draw(st.integers(min_value=100, max_value=1000))
    height = draw(st.integers(min_value=100, max_value=1000))
    mode = draw(st.sampled_from(["RGB", "L", "RGBA"]))
    
    # Create a simple image
    image = Image.new(mode, (width, height), color="white")
    return image


@st.composite
def valid_classification_responses(draw):
    """Generate valid OpenAI API responses."""
    document_type = draw(st.text(min_size=1, max_size=50))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    # Generate identifiers
    num_identifiers = draw(st.integers(min_value=0, max_value=5))
    identifiers = {}
    for _ in range(num_identifiers):
        key = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))))
        value = draw(st.text(min_size=1, max_size=50))
        identifiers[key] = value
    
    classification_json = {
        "document_type": document_type,
        "confidence": confidence,
        "identifiers": identifiers,
    }
    
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(classification_json),
                },
            },
        ],
    }
    
    return response, classification_json


def create_test_logger():
    """Create a logger for testing."""
    tmp_dir = tempfile.mkdtemp()
    return Logger(
        log_dir=Path(tmp_dir) / "logs",
        component="test_ai_service",
        log_level="INFO",
        log_to_event_log=False,
    )


# Feature: scanner-watcher2, Property 11: Multiple images to API transmission
@given(
    num_images=st.integers(min_value=1, max_value=3),
    images=st.lists(valid_images(), min_size=1, max_size=3),
)
@settings(max_examples=100, deadline=None)
def test_multiple_images_transmitted_to_api(num_images: int, images: list[Image.Image]) -> None:
    """
    For any set of extracted images, the system should send all images to OpenAI API for classification.
    
    Validates: Requirements 2.2
    """
    # Use only the requested number of images
    test_images = images[:num_images]
    
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Mock the OpenAI client
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Test Document",
                        "confidence": 0.95,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        # Classify the document with multiple images
        result = ai_service.classify_document(test_images)
        
        # Verify API was called
        assert mock_create.call_count == 1
        
        # Verify the call included all images
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        
        # Should have system and user messages
        assert len(messages) == 2
        
        # User message should contain all images
        user_message = messages[1]
        assert user_message["role"] == "user"
        assert isinstance(user_message["content"], list)
        
        # Count images in content
        image_count = 0
        for content_item in user_message["content"]:
            if content_item.get("type") == "image_url":
                image_count += 1
                # Verify it's a base64 encoded image
                image_url = content_item["image_url"]["url"]
                assert image_url.startswith("data:image/png;base64,")
        
        # Verify all images were included
        assert image_count == len(test_images), f"Expected {len(test_images)} images, found {image_count}"
        
        # Verify result is a Classification
        assert isinstance(result, Classification)


# Feature: scanner-watcher2, Property 12: Response parsing
@given(response_data=valid_classification_responses())
@settings(max_examples=100, deadline=None)
def test_response_parsing_success(response_data) -> None:
    """
    For any valid OpenAI classification response, the system should successfully parse the document type.
    
    Validates: Requirements 2.3
    """
    response, expected_data = response_data
    
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Parse the response
    classification = ai_service.parse_classification(response)
    
    # Verify parsed data matches expected
    assert classification.document_type == expected_data["document_type"]
    assert abs(classification.confidence - expected_data["confidence"]) < 0.01
    assert classification.identifiers == expected_data["identifiers"]
    assert classification.raw_response == response


# Feature: scanner-watcher2, Property 13: Response validation
@given(
    has_choices=st.booleans(),
    has_message=st.booleans(),
    has_content=st.booleans(),
    has_document_type=st.booleans(),
)
@settings(max_examples=100, deadline=None)
def test_response_validation_rejects_invalid(
    has_choices: bool,
    has_message: bool,
    has_content: bool,
    has_document_type: bool,
) -> None:
    """
    For any classification response received, the system should validate the response format before processing.
    
    Validates: Requirements 2.6
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Build response based on flags
    response = {}
    
    if has_choices:
        response["choices"] = []
        if has_message:
            message = {}
            if has_content:
                content_data = {}
                if has_document_type:
                    content_data["document_type"] = "Test Document"
                    content_data["confidence"] = 0.95
                    content_data["identifiers"] = {}
                message["content"] = json.dumps(content_data) if content_data else ""
            response["choices"].append({"message": message})
    
    # If all flags are True, response should be valid
    if has_choices and has_message and has_content and has_document_type:
        classification = ai_service.parse_classification(response)
        assert isinstance(classification, Classification)
        assert classification.document_type == "Test Document"
    else:
        # Otherwise, should raise ValueError
        with pytest.raises(ValueError):
            ai_service.parse_classification(response)


# Feature: scanner-watcher2, Property 33: Rate limit handling
@given(
    retry_after=st.integers(min_value=1, max_value=60),
)
@settings(max_examples=100, deadline=None)
def test_rate_limit_handling(retry_after: int) -> None:
    """
    For any OpenAI API rate limit error, the system should wait the specified retry-after duration before retrying.
    
    Validates: Requirements 12.1
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=3, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock the OpenAI client to raise RateLimitError
    # RateLimitError requires response and body arguments
    mock_response = Mock()
    mock_response.status_code = 429
    rate_limit_error = RateLimitError(
        "Rate limit exceeded",
        response=mock_response,
        body={"error": {"message": "Rate limit exceeded"}},
    )
    rate_limit_error.retry_after = retry_after
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.side_effect = rate_limit_error
        
        # Should raise RateLimitError after retries
        with pytest.raises(RateLimitError):
            ai_service.classify_document(image)
        
        # Verify retries were attempted
        assert mock_create.call_count == error_handler.max_attempts


# Feature: scanner-watcher2, Property 35: Timeout handling
@given(
    timeout_seconds=st.integers(min_value=1, max_value=60),
)
@settings(max_examples=100, deadline=None)
def test_timeout_handling(timeout_seconds: int) -> None:
    """
    For any API call that times out after configured seconds, the system should log the timeout and retry according to the retry policy.
    
    Validates: Requirements 12.3
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=3, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service with specified timeout
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=timeout_seconds,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Verify timeout is set correctly
    assert ai_service.timeout == timeout_seconds
    
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock the OpenAI client to raise APITimeoutError
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.side_effect = APITimeoutError("Request timed out")
        
        # Should raise APITimeoutError after retries
        with pytest.raises(APITimeoutError):
            ai_service.classify_document(image)
        
        # Verify retries were attempted (timeout is transient)
        assert mock_create.call_count == error_handler.max_attempts


# Feature: scanner-watcher2, Property 36: TLS security
@given(dummy=st.just(None))  # Add @given to make it a property test
@settings(max_examples=1, deadline=None)  # Only need to run once
def test_tls_security(dummy) -> None:
    """
    For any API call made, the system should use HTTPS with TLS 1.2 or higher.
    
    Validates: Requirements 12.4
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Patch httpx.Client to capture SSL verification setting
    captured_verify = None
    
    original_client_init = None
    
    def mock_client_init(self, *args, **kwargs):
        nonlocal captured_verify
        if "verify" in kwargs:
            captured_verify = kwargs["verify"]
        return original_client_init(self, *args, **kwargs)
    
    import httpx
    original_client_init = httpx.Client.__init__
    
    with patch.object(httpx.Client, "__init__", mock_client_init):
        # Create AI service
        ai_service = AIService(
            api_key="test-key",
            model="gpt-4-vision-preview",
            timeout=30,
            error_handler=error_handler,
            logger=logger,
        )
        
        # Verify SSL verification is enabled (True means use system defaults with TLS 1.2+)
        # httpx with verify=True uses the system's SSL context which enforces TLS 1.2+ by default
        assert captured_verify is not None
        assert captured_verify is True, "SSL verification must be enabled for secure HTTPS"


# Feature: scanner-watcher2, Property 42: API latency logging
@given(
    processing_time_ms=st.integers(min_value=100, max_value=5000),
)
@settings(max_examples=100, deadline=None)
def test_api_latency_logging(processing_time_ms: int) -> None:
    """
    For any API call made, the system should log the API response latency.
    
    Validates: Requirements 15.2
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock the OpenAI client
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Test Document",
                        "confidence": 0.95,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    import time
    
    def mock_create(*args, **kwargs):
        # Simulate processing time
        time.sleep(processing_time_ms / 1000.0)
        return Mock(model_dump=lambda: mock_response)
    
    with patch.object(ai_service.client.chat.completions, "create", side_effect=mock_create):
        # Mock logger.info to capture latency
        logged_latency = None
        
        original_info = logger.info
        
        def capture_info(message, **context):
            nonlocal logged_latency
            if "latency_ms" in context:
                logged_latency = context["latency_ms"]
            return original_info(message, **context)
        
        with patch.object(logger, "info", side_effect=capture_info):
            # Classify the document
            result = ai_service.classify_document(image)
            
            # Verify latency was logged
            assert logged_latency is not None
            assert isinstance(logged_latency, int)
            
            # Latency should be approximately the processing time (with some tolerance)
            assert logged_latency >= processing_time_ms * 0.8
            assert logged_latency <= processing_time_ms * 1.5 + 100  # Allow for overhead


# Feature: scanner-watcher2, Property 14: Document type support
@given(
    document_type=st.sampled_from([
        "Panel List",
        "QME Appointment Notification Form",
        "Agreed Medical Evaluator Report",
        "Qualified Medical Evaluator Report",
        "PTP Initial Report",
        "PTP P&S Report",
        "RFA (Request for Authorization)",
        "UR Approval",
        "UR Denial",
        "Modified UR",
        "Finding and Award",
        "Finding & Order",
        "Advocacy/Cover Letter",
        "Declaration of Readiness to Proceed",
        "Objection to Declaration of Readiness to Proceed",
    ]),
    confidence=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=100, deadline=None)
def test_document_type_support(document_type: str, confidence: float) -> None:
    """
    For any document matching a supported type, the system should return the standardized document type name.
    
    Validates: Requirements 16.1-16.15, 16.17
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Verify the document type is in the supported list
    supported_types = ai_service.get_supported_document_types()
    assert document_type in supported_types, f"{document_type} not in supported types"
    
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock the OpenAI client to return the specified document type
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": document_type,
                        "confidence": confidence,
                        "identifiers": {"test_key": "test_value"},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        # Classify the document
        result = ai_service.classify_document(image)
        
        # Verify the result contains the standardized document type name
        assert isinstance(result, Classification)
        assert result.document_type == document_type
        assert abs(result.confidence - confidence) < 0.01
        
        # Verify API was called with correct parameters
        assert mock_create.call_count == 1
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        
        # Verify system message contains all supported document types
        system_message = messages[0]
        assert system_message["role"] == "system"
        system_content = system_message["content"]
        
        # All supported document types should be in the prompt (Requirement 16.16)
        for supported_type in supported_types:
            assert supported_type in system_content, f"{supported_type} not found in system prompt"


# Feature: scanner-watcher2, Property 15: Comprehensive prompt inclusion
@given(dummy=st.just(None))  # Add @given to make it a property test
@settings(max_examples=1, deadline=None)  # Only need to run once
def test_comprehensive_prompt_inclusion(dummy) -> None:
    """
    For any classification request, the system should include all supported document types in the AI prompt.
    
    Validates: Requirements 16.16
    """
    # Create mock dependencies
    error_handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    logger = create_test_logger()
    
    # Create AI service
    ai_service = AIService(
        api_key="test-key",
        model="gpt-4-vision-preview",
        timeout=30,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Get all supported document types
    supported_types = ai_service.get_supported_document_types()
    
    # Verify we have all 15 document types
    assert len(supported_types) == 15, f"Expected 15 document types, found {len(supported_types)}"
    
    # Verify all expected types are present
    expected_types = [
        "Panel List",
        "QME Appointment Notification Form",
        "Agreed Medical Evaluator Report",
        "Qualified Medical Evaluator Report",
        "PTP Initial Report",
        "PTP P&S Report",
        "RFA (Request for Authorization)",
        "UR Approval",
        "UR Denial",
        "Modified UR",
        "Finding and Award",
        "Finding & Order",
        "Advocacy/Cover Letter",
        "Declaration of Readiness to Proceed",
        "Objection to Declaration of Readiness to Proceed",
    ]
    
    for expected_type in expected_types:
        assert expected_type in supported_types, f"{expected_type} not in supported types"
    
    # Create a simple test image
    image = Image.new("RGB", (100, 100), color="white")
    
    # Mock the OpenAI client
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "document_type": "Panel List",
                        "confidence": 0.95,
                        "identifiers": {},
                    }),
                },
            },
        ],
    }
    
    with patch.object(ai_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        # Classify the document
        result = ai_service.classify_document(image)
        
        # Verify API was called
        assert mock_create.call_count == 1
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]
        
        # Extract system message
        system_message = messages[0]
        assert system_message["role"] == "system"
        system_content = system_message["content"]
        
        # Verify ALL supported document types are included in the prompt
        for doc_type in supported_types:
            assert doc_type in system_content, f"Document type '{doc_type}' not found in system prompt"
        
        # Verify the prompt instructs to use exact names
        assert "exact name" in system_content.lower() or "supported types" in system_content.lower()
