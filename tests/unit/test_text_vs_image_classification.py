"""
Unit tests for text-first classification with image fallback.

Verifies:
- PDFProcessor.extract_text returns text for digital PDFs and None for image-only
- FileProcessor uses text path when text is available
- FileProcessor falls back to image path when text is unavailable
- Logging correctly records classification_mode
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import Mock

import fitz
import pytest
from PIL import Image

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.core.file_processor import FileProcessor
from scanner_watcher2.core.pdf_processor import PDFProcessor
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification


# ---------------------------------------------------------------------------
# PDFProcessor.extract_text tests
# ---------------------------------------------------------------------------

class TestPDFExtractText:
    """Tests for PDFProcessor.extract_text."""

    def _make_text_pdf(self, tmp_path: Path, lines: list[str], pages: int = 1) -> Path:
        """Create a PDF with embedded text."""
        doc = fitz.open()
        for i in range(pages):
            page = doc.new_page()
            y = 80
            for line in lines:
                page.insert_text((72, y), line, fontsize=11)
                y += 18
            page.insert_text((72, y), f"Page {i + 1} of {pages}", fontsize=10)
        pdf_path = tmp_path / "text_doc.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def _make_image_pdf(self, tmp_path: Path) -> Path:
        """Create a PDF that contains only an image (no text layer)."""
        doc = fitz.open()
        page = doc.new_page()
        img = Image.new("RGB", (200, 200), "white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page.insert_image(fitz.Rect(72, 72, 272, 272), stream=buf.getvalue())
        pdf_path = tmp_path / "image_doc.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    @pytest.mark.unit
    def test_extract_text_from_digital_pdf(self, tmp_path: Path) -> None:
        proc = PDFProcessor()
        pdf_path = self._make_text_pdf(tmp_path, [
            "WORKERS COMPENSATION APPEALS BOARD",
            "STATE OF CALIFORNIA",
            "Case No: ADJ-12345",
            "FINDINGS AND AWARD",
            "The Board issues the following Findings and Award",
            "for the applicant in the above-entitled matter.",
        ])
        text = proc.extract_text(pdf_path)
        assert text is not None
        assert "WORKERS COMPENSATION" in text
        assert "ADJ-12345" in text

    @pytest.mark.unit
    def test_extract_text_returns_none_for_image_pdf(self, tmp_path: Path) -> None:
        proc = PDFProcessor()
        pdf_path = self._make_image_pdf(tmp_path)
        text = proc.extract_text(pdf_path)
        assert text is None

    @pytest.mark.unit
    def test_extract_text_returns_none_for_short_text(self, tmp_path: Path) -> None:
        proc = PDFProcessor()
        pdf_path = self._make_text_pdf(tmp_path, ["Hi"])
        text = proc.extract_text(pdf_path)
        assert text is None, "Text shorter than MIN_TEXT_LENGTH should return None"

    @pytest.mark.unit
    def test_extract_text_multi_page(self, tmp_path: Path) -> None:
        proc = PDFProcessor()
        pdf_path = self._make_text_pdf(tmp_path, [
            "WORKERS COMPENSATION APPEALS BOARD",
            "DECLARATION OF READINESS TO PROCEED",
            "Case No: ADJ-99999",
            "The undersigned declares this case ready for hearing.",
        ], pages=3)
        text = proc.extract_text(pdf_path, num_pages=3)
        assert text is not None
        assert text.count("Page Break") == 2
        assert "Page 1" in text
        assert "Page 3" in text

    @pytest.mark.unit
    def test_extract_text_invalid_path(self, tmp_path: Path) -> None:
        proc = PDFProcessor()
        text = proc.extract_text(tmp_path / "nonexistent.pdf")
        assert text is None


# ---------------------------------------------------------------------------
# FileProcessor text-vs-image path tests
# ---------------------------------------------------------------------------

@pytest.fixture
def components_text_path(tmp_path: Path):
    """Build mocked components where extract_text returns text."""
    pdf_processor = Mock(spec=PDFProcessor)
    ai_service = Mock(spec=AIService)
    error_handler = Mock(spec=ErrorHandler)
    logger = Mock(spec=Logger)

    pdf_processor.extract_text.return_value = (
        "WORKERS COMPENSATION APPEALS BOARD\n"
        "Case No: ADJ-55555\nFINDINGS AND AWARD\n"
        "The Board issues the following Findings and Award for plaintiff JANE ROE."
    )

    classification = Classification(
        document_type="Finding and Award",
        confidence=0.97,
        identifiers={"plaintiff_name": "JANE ROE", "case_number": "ADJ-55555"},
        raw_response={},
    )
    ai_service.classify_document_text.return_value = classification

    file_manager = FileManager(
        error_handler=error_handler, logger=logger, temp_directory=tmp_path,
    )
    error_handler.execute_with_retry.side_effect = lambda func, **kw: func()

    return pdf_processor, ai_service, file_manager, error_handler, logger


@pytest.fixture
def components_image_path(tmp_path: Path):
    """Build mocked components where extract_text returns None (scanned PDF)."""
    pdf_processor = Mock(spec=PDFProcessor)
    ai_service = Mock(spec=AIService)
    error_handler = Mock(spec=ErrorHandler)
    logger = Mock(spec=Logger)

    pdf_processor.extract_text.return_value = None
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image

    classification = Classification(
        document_type="Medical Report",
        confidence=0.92,
        identifiers={"plaintiff_name": "BOB SMITH"},
        raw_response={},
    )
    ai_service.classify_document.return_value = classification

    file_manager = FileManager(
        error_handler=error_handler, logger=logger, temp_directory=tmp_path,
    )
    error_handler.execute_with_retry.side_effect = lambda func, **kw: func()

    return pdf_processor, ai_service, file_manager, error_handler, logger


@pytest.mark.unit
def test_file_processor_uses_text_path(tmp_path: Path, components_text_path) -> None:
    """When text is extractable, classify_document_text is called, not classify_document."""
    pdf_proc, ai_svc, file_mgr, err, log = components_text_path

    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")

    processor = FileProcessor(pdf_proc, ai_svc, file_mgr, err, log)
    result = processor.process_file(test_file)

    assert result.success is True
    assert result.document_type == "Finding and Award"
    ai_svc.classify_document_text.assert_called_once()
    ai_svc.classify_document.assert_not_called()
    pdf_proc.extract_first_pages.assert_not_called()


@pytest.mark.unit
def test_file_processor_uses_image_fallback(tmp_path: Path, components_image_path) -> None:
    """When text extraction returns None, classify_document (image) is used."""
    pdf_proc, ai_svc, file_mgr, err, log = components_image_path

    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")

    processor = FileProcessor(pdf_proc, ai_svc, file_mgr, err, log)
    result = processor.process_file(test_file)

    assert result.success is True
    assert result.document_type == "Medical Report"
    ai_svc.classify_document.assert_called_once()
    ai_svc.classify_document_text.assert_not_called()
    pdf_proc.extract_first_pages.assert_called_once()


@pytest.mark.unit
def test_text_path_logs_classification_mode(tmp_path: Path, components_text_path) -> None:
    """Verify classification_mode=text is logged on the text path."""
    pdf_proc, ai_svc, file_mgr, err, log = components_text_path

    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")

    processor = FileProcessor(pdf_proc, ai_svc, file_mgr, err, log)
    processor.process_file(test_file)

    info_calls = [c for c in log.info.call_args_list if "classification_mode" in c.kwargs]
    modes = [c.kwargs["classification_mode"] for c in info_calls]
    assert "text" in modes


@pytest.mark.unit
def test_image_path_logs_classification_mode(tmp_path: Path, components_image_path) -> None:
    """Verify classification_mode=image is logged on the image path."""
    pdf_proc, ai_svc, file_mgr, err, log = components_image_path

    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")

    processor = FileProcessor(pdf_proc, ai_svc, file_mgr, err, log)
    processor.process_file(test_file)

    info_calls = [c for c in log.info.call_args_list if "classification_mode" in c.kwargs]
    modes = [c.kwargs["classification_mode"] for c in info_calls]
    assert "image" in modes


@pytest.mark.unit
def test_text_path_skips_image_optimization(tmp_path: Path, components_text_path) -> None:
    """When using text, image extraction and optimization are never called."""
    pdf_proc, ai_svc, file_mgr, err, log = components_text_path

    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")

    processor = FileProcessor(pdf_proc, ai_svc, file_mgr, err, log)
    processor.process_file(test_file)

    pdf_proc.extract_first_pages.assert_not_called()
    pdf_proc.optimize_image.assert_not_called()
