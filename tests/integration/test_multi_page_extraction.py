"""
Integration test for multi-page PDF extraction.
"""

from pathlib import Path

import fitz
import pytest
from PIL import Image

from scanner_watcher2.core.pdf_processor import PDFProcessor


def create_multi_page_pdf(output_path: Path, num_pages: int = 5) -> None:
    """Create a test PDF with multiple pages."""
    doc = fitz.open()
    
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)
        text = f"Test Page {i + 1}"
        page.insert_text((50, 50), text, fontsize=20)
    
    doc.save(str(output_path))
    doc.close()


@pytest.mark.integration
def test_extract_multiple_pages_from_pdf(temp_dir: Path) -> None:
    """
    Integration test: Extract multiple pages from a PDF.
    
    Validates: Requirements 2.1, 2.4, 9.6
    """
    processor = PDFProcessor()
    
    # Create a 5-page PDF
    pdf_path = temp_dir / "multi_page.pdf"
    create_multi_page_pdf(pdf_path, num_pages=5)
    
    # Extract 3 pages (default)
    images = processor.extract_first_pages(pdf_path, num_pages=3)
    
    # Verify we got 3 images
    assert len(images) == 3
    
    # Verify all are valid images
    for img in images:
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0


@pytest.mark.integration
def test_extract_pages_from_short_pdf(temp_dir: Path) -> None:
    """
    Integration test: Extract pages from PDF with fewer pages than requested.
    
    Validates: Requirements 2.4
    """
    processor = PDFProcessor()
    
    # Create a 2-page PDF
    pdf_path = temp_dir / "short.pdf"
    create_multi_page_pdf(pdf_path, num_pages=2)
    
    # Request 3 pages but should only get 2
    images = processor.extract_first_pages(pdf_path, num_pages=3)
    
    # Verify we got only 2 images (all available)
    assert len(images) == 2
    
    # Verify all are valid images
    for img in images:
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0


@pytest.mark.integration
def test_extract_single_page_compatibility(temp_dir: Path) -> None:
    """
    Integration test: Verify extract_first_page still works (backward compatibility).
    
    Validates: Requirements 2.1
    """
    processor = PDFProcessor()
    
    # Create a multi-page PDF
    pdf_path = temp_dir / "multi_page.pdf"
    create_multi_page_pdf(pdf_path, num_pages=3)
    
    # Use old method
    image = processor.extract_first_page(pdf_path)
    
    # Verify we got a single image
    assert isinstance(image, Image.Image)
    assert image.width > 0
    assert image.height > 0


@pytest.mark.integration
def test_optimize_multiple_images(temp_dir: Path) -> None:
    """
    Integration test: Optimize multiple extracted images.
    
    Validates: Requirements 9.3
    """
    processor = PDFProcessor()
    
    # Create a multi-page PDF
    pdf_path = temp_dir / "multi_page.pdf"
    create_multi_page_pdf(pdf_path, num_pages=3)
    
    # Extract pages
    images = processor.extract_first_pages(pdf_path, num_pages=3)
    
    # Optimize all images
    optimized_images = [processor.optimize_image(img) for img in images]
    
    # Verify all are optimized
    assert len(optimized_images) == 3
    for img in optimized_images:
        assert isinstance(img, Image.Image)
        assert img.width <= processor.MAX_IMAGE_WIDTH
        assert img.height <= processor.MAX_IMAGE_HEIGHT
