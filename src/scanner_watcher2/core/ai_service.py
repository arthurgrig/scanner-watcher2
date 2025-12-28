"""
AI Service for document classification using OpenAI API.
"""

import base64
import io
import json
import time
from typing import Any

import httpx
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from PIL import Image

from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification, DocumentType


# Legacy document types list - kept for reference
# Now using DocumentType enum with prioritized classification
# SUPPORTED_DOCUMENT_TYPES = [
#     "Panel List",
#     "QME Appointment Notification Form",
#     "Agreed Medical Evaluator Report",
#     "Qualified Medical Evaluator Report",
#     "PTP Initial Report",
#     "PTP P&S Report",
#     "RFA (Request for Authorization)",
#     "UR Approval",
#     "UR Denial",
#     "Modified UR",
#     "Finding and Award",
#     "Finding & Order",
#     "Advocacy/Cover Letter",
#     "Declaration of Readiness to Proceed",
#     "Objection to Declaration of Readiness to Proceed",
# ]


class AIService:
    """
    Service for classifying documents using OpenAI API.
    
    Provides:
    - Document classification using GPT-4 Vision with prioritized enum-based approach
    - Three-tier classification: standard categories, specific types, OTHER fallback
    - Response parsing and validation
    - API error handling and rate limit management
    - Timeout handling
    - TLS 1.2+ security
    - Corporate proxy support
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: int,
        error_handler: ErrorHandler,
        logger: Logger,
        max_tokens: int = 500,
        temperature: float = 0.1,
        proxy: str | None = None,
    ) -> None:
        """
        Initialize AI service with API credentials.

        Args:
            api_key: OpenAI API key
            model: Model name to use for classification
            timeout: Request timeout in seconds
            error_handler: Error handler for retry logic
            logger: Logger instance
            max_tokens: Maximum tokens in response
            temperature: Model temperature (0.0-1.0)
            proxy: Optional proxy URL for corporate environments
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.error_handler = error_handler
        self.logger = logger
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.proxy = proxy

        # Configure HTTP client with proxy and TLS settings
        http_client_kwargs: dict[str, Any] = {
            "timeout": httpx.Timeout(timeout),
            "verify": True,  # Use default SSL verification
        }

        if proxy:
            http_client_kwargs["proxies"] = proxy

        http_client = httpx.Client(**http_client_kwargs)

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout,
            http_client=http_client,
        )

    def get_supported_document_types(self) -> list[str]:
        """
        Return list of supported document type categories.

        Returns standard enum categories for classification.

        Returns:
            List of standardized document type category names
        """
        return [dt.value for dt in DocumentType if dt != DocumentType.OTHER]

    def _encode_image(self, image: Image.Image) -> str:
        """
        Encode PIL Image to base64 string for API transmission.

        Args:
            image: PIL Image to encode

        Returns:
            Base64 encoded image string
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def classify_document(self, images: Image.Image | list[Image.Image]) -> Classification:
        """
        Send image(s) to OpenAI and get classification.

        Implements Requirements 2.2.

        Args:
            images: Document image or list of images to classify

        Returns:
            Classification result

        Raises:
            APIError: If API returns an error
            APITimeoutError: If request times out
            RateLimitError: If rate limit is exceeded
        """
        start_time = time.time()

        try:
            # Normalize to list
            image_list = images if isinstance(images, list) else [images]

            # Encode all images for API transmission
            base64_images = [self._encode_image(img) for img in image_list]

            if self.logger:
                self.logger.debug(
                    "Encoding images for API transmission",
                    num_images=len(base64_images),
                )

            # Build content with text and all images
            num_pages = len(image_list)
            if num_pages == 1:
                text_prompt = "Classify this legal document based on the provided page."
            else:
                text_prompt = f"Classify this legal document. {num_pages} pages are provided for analysis."
            
            content: list[Any] = [
                {
                    "type": "text",
                    "text": text_prompt,
                }
            ]

            # Add all images to the content
            for idx, base64_image in enumerate(base64_images):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                    },
                })

            # Build comprehensive system prompt with prioritized classification logic
            # Three-tier classification approach:
            # Priority 1: Match to standard enum categories
            # Priority 2: Use specific document type if no enum match
            # Priority 3: Return "OTHER_[description]" if unclassifiable
            
            # Build list of standard categories with descriptions
            category_descriptions = [
                "- MEDICAL_REPORT: Any medical evaluation, QME, AME, PTP, IME reports",
                "- INJURY_REPORT: Initial injury reports, incident reports",
                "- CLAIM_FORM: DWC-1, claim applications",
                "- DEPOSITION: Deposition transcripts",
                "- EXPERT_WITNESS_REPORT: Expert opinions, vocational evaluations",
                "- SETTLEMENT_AGREEMENT: Compromise & Release, Stipulations",
                "- COURT_ORDER: WCAB orders, findings, awards",
                "- INSURANCE_CORRESPONDENCE: Carrier letters, UR decisions, RFAs",
                "- WAGE_STATEMENT: Earnings records, pay stubs",
                "- VOCATIONAL_REPORT: Vocational rehabilitation reports",
                "- IME_REPORT: Independent Medical Examinations",
                "- SURVEILLANCE_REPORT: Investigation reports",
                "- SUBPOENA: Subpoenas, subpoena duces tecum",
                "- MOTION: Motions, petitions, DORs",
                "- BRIEF: Legal briefs, memoranda",
            ]
            
            categories_text = "\n".join(category_descriptions)
            
            system_prompt = (
                "You are a legal document classifier for California Workers' Compensation cases. "
                "Classify documents using this prioritized approach:\n\n"
                "**PRIORITY 1 - Standard Categories (use if document clearly fits):**\n"
                f"{categories_text}\n\n"
                "**PRIORITY 2 - Specific Type (if no standard category fits):**\n"
                "Provide the specific document type name (e.g., 'Panel List', 'QME Appointment Notification Form')\n\n"
                "**PRIORITY 3 - Unknown (if cannot classify):**\n"
                "Return 'OTHER_[Brief Description]' (e.g., 'OTHER_Unidentified Medical Form')\n\n"
                "Return JSON with:\n"
                "- document_type: The classification (standard category value like 'Medical Report', specific type, or OTHER_description)\n"
                "- confidence: 0.0-1.0\n"
                "- identifiers: Extract relevant information using these EXACT keys when available:\n"
                "  * plaintiff_name: The plaintiff/injured worker name (HIGHEST PRIORITY - always extract)\n"
                "  * patient_name: Alternative for plaintiff/injured worker (use if plaintiff_name not clear)\n"
                "  * client_name: The employer/defendant company name\n"
                "  * case_number: Any case, claim, or file number\n"
                "  * date_of_injury: Date of injury if mentioned\n"
                "  * report_date: Date of the report/document\n"
                "  * evaluator_name: Name of doctor/evaluator if applicable\n"
                "  * other relevant fields as needed\n"
                "  Use these exact key names for consistency in file naming."
            )

            # Prepare the API request
            def make_api_call() -> dict[str, Any]:
                """Make the API call with retry support."""
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": content,
                        },
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return response.model_dump()

            # Execute with retry logic and circuit breaker
            raw_response = self.error_handler.execute_with_retry(
                func=make_api_call,
                operation_name="OpenAI API call",
                use_circuit_breaker=True,
            )

            # Calculate and log API latency
            latency_ms = int((time.time() - start_time) * 1000)
            self.logger.info(
                "OpenAI API call completed",
                latency_ms=latency_ms,
                model=self.model,
            )

            # Parse and validate the response
            classification = self.parse_classification(raw_response)

            return classification

        except RateLimitError as e:
            # Log rate limit error with retry-after if available
            retry_after = getattr(e, "retry_after", None)
            self.logger.warning(
                "OpenAI API rate limit exceeded",
                retry_after=retry_after,
                error=str(e),
            )
            raise

        except APITimeoutError as e:
            # Log timeout error
            self.logger.error(
                "OpenAI API request timed out",
                timeout_seconds=self.timeout,
                error=str(e),
            )
            raise

        except APIError as e:
            # Log general API error
            self.logger.error(
                "OpenAI API error",
                status_code=getattr(e, "status_code", None),
                error=str(e),
            )
            raise

        except Exception as e:
            # Log unexpected error
            self.logger.error(
                "Unexpected error during document classification",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    def parse_classification(self, response: dict[str, Any]) -> Classification:
        """
        Parse OpenAI response into structured data.

        Args:
            response: Raw API response

        Returns:
            Parsed classification

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract the content from the response
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices in API response")

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                raise ValueError("Empty content in API response")

            # Parse JSON from content
            try:
                classification_data = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract from markdown code block
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                    classification_data = json.loads(json_str)
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                    classification_data = json.loads(json_str)
                else:
                    raise ValueError(f"Could not parse JSON from response: {content}")

            # Validate required fields
            if "document_type" not in classification_data:
                raise ValueError("Missing 'document_type' in classification response")

            document_type = classification_data["document_type"]
            confidence = classification_data.get("confidence", 0.0)
            identifiers = classification_data.get("identifiers", {})

            # Validate types
            if not isinstance(document_type, str):
                raise ValueError("document_type must be a string")

            if not isinstance(confidence, (int, float)):
                raise ValueError("confidence must be a number")

            if not isinstance(identifiers, dict):
                raise ValueError("identifiers must be a dictionary")

            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, float(confidence)))

            return Classification(
                document_type=document_type,
                confidence=confidence,
                identifiers=identifiers,
                raw_response=response,
            )

        except Exception as e:
            self.logger.error(
                "Failed to parse classification response",
                error=str(e),
                response_preview=str(response)[:200],
            )
            raise
