"""
PDF processor for extracting pages from PDF documents.
"""

from __future__ import annotations

import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from PyPDF2 import PdfReader

from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger


class PDFProcessor:
    """Extract pages from PDF documents for AI analysis."""

    # Image optimization settings
    MAX_IMAGE_WIDTH = 2048
    MAX_IMAGE_HEIGHT = 2048
    JPEG_QUALITY = 85
    DPI = 150  # DPI for PDF rendering

    def __init__(
        self,
        logger: Logger | None = None,
        error_handler: ErrorHandler | None = None,
    ) -> None:
        """
        Initialize PDF processor.

        Args:
            logger: Logger instance for structured logging
            error_handler: Error handler for retry logic
        """
        self.logger = logger
        self.error_handler = error_handler

    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        Check if PDF is valid and readable.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF is valid

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")

        # Try to open with PyMuPDF first
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()

            if page_count == 0:
                raise ValueError(f"PDF has no pages: {pdf_path}")

            return True

        except Exception as e:
            # Try PyPDF2 as fallback
            try:
                with open(pdf_path, "rb") as f:
                    reader = PdfReader(f)
                    page_count = len(reader.pages)

                if page_count == 0:
                    raise ValueError(f"PDF has no pages: {pdf_path}")

                return True

            except Exception:
                # Both methods failed
                raise ValueError(f"Invalid or corrupted PDF: {pdf_path}") from e

    def extract_first_page(self, pdf_path: Path) -> Image.Image:
        """
        Extract first page as image using PyMuPDF with PyPDF2 fallback.

        Args:
            pdf_path: Path to PDF file

        Returns:
            First page as PIL Image

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or has no pages
            RuntimeError: If extraction fails with both methods
        """
        # Use extract_first_pages and return the first image
        images = self.extract_first_pages(pdf_path, num_pages=1)
        return images[0]

    def extract_first_pages(self, pdf_path: Path, num_pages: int = 3) -> list[Image.Image]:
        """
        Extract first N pages as images using PyMuPDF with PyPDF2 fallback.

        Implements Requirements 2.1, 2.4, 9.6.

        Each page is extracted independently to prevent single page failures
        from blocking the entire process.

        Args:
            pdf_path: Path to PDF file
            num_pages: Number of pages to extract (default: 3)

        Returns:
            List of PIL Images (may be fewer than num_pages if PDF has fewer pages)

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or has no pages
            RuntimeError: If extraction fails for all pages
        """
        # Validate PDF first
        self.validate_pdf(pdf_path)

        # Try PyMuPDF first (primary method)
        try:
            if self.logger:
                self.logger.debug(
                    "Extracting pages with PyMuPDF",
                    pdf_path=str(pdf_path),
                    num_pages=num_pages,
                )

            doc = fitz.open(pdf_path)
            try:
                # Get actual page count
                total_pages = len(doc)
                pages_to_extract = min(num_pages, total_pages)

                if self.logger:
                    self.logger.debug(
                        "PDF page count determined",
                        total_pages=total_pages,
                        pages_to_extract=pages_to_extract,
                    )

                images: list[Image.Image] = []
                extraction_errors: list[str] = []

                # Extract each page independently
                for page_num in range(pages_to_extract):
                    try:
                        page = doc[page_num]

                        # Render page to pixmap with specified DPI
                        mat = fitz.Matrix(self.DPI / 72, self.DPI / 72)
                        pix = page.get_pixmap(matrix=mat)

                        # Convert pixmap to PIL Image
                        img_data = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_data))

                        images.append(image)

                        if self.logger:
                            self.logger.debug(
                                "Successfully extracted page",
                                page_num=page_num,
                                image_size=f"{image.width}x{image.height}",
                            )

                    except Exception as page_error:
                        # Log error but continue with other pages
                        error_msg = f"Page {page_num}: {str(page_error)}"
                        extraction_errors.append(error_msg)

                        if self.logger:
                            self.logger.warning(
                                "Failed to extract page, continuing with others",
                                page_num=page_num,
                                error=str(page_error),
                            )

                # Check if we got at least one image
                if not images:
                    raise RuntimeError(
                        f"Failed to extract any pages. Errors: {'; '.join(extraction_errors)}"
                    )

                if self.logger:
                    self.logger.info(
                        "Successfully extracted pages with PyMuPDF",
                        pdf_path=str(pdf_path),
                        pages_extracted=len(images),
                        pages_requested=num_pages,
                        total_pages=total_pages,
                    )

                return images

            finally:
                doc.close()

        except Exception as pymupdf_error:
            if self.logger:
                self.logger.warning(
                    "PyMuPDF extraction failed, trying PyPDF2 fallback",
                    pdf_path=str(pdf_path),
                    error=str(pymupdf_error),
                )

            # Fallback to PyPDF2
            try:
                with open(pdf_path, "rb") as f:
                    reader = PdfReader(f)

                    # PyPDF2 doesn't directly render to image, so we need a workaround
                    # We'll use PyMuPDF's ability to open from bytes as a last resort
                    # For now, we'll re-raise if PyMuPDF failed, as PyPDF2 doesn't
                    # have built-in image rendering
                    raise RuntimeError(
                        f"PyPDF2 fallback not fully implemented for image extraction. "
                        f"PyMuPDF error: {pymupdf_error}"
                    )

            except Exception as pypdf2_error:
                error_msg = (
                    f"Failed to extract pages with both PyMuPDF and PyPDF2. "
                    f"PyMuPDF error: {pymupdf_error}. PyPDF2 error: {pypdf2_error}"
                )

                if self.logger:
                    self.logger.error(
                        "PDF extraction failed with all methods",
                        pdf_path=str(pdf_path),
                        pymupdf_error=str(pymupdf_error),
                        pypdf2_error=str(pypdf2_error),
                    )

                raise RuntimeError(error_msg) from pypdf2_error

    def optimize_image(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for API transmission by resizing and compressing.

        Args:
            image: PIL Image to optimize

        Returns:
            Optimized PIL Image
        """
        if self.logger:
            self.logger.debug(
                "Optimizing image",
                original_size=f"{image.width}x{image.height}",
                original_mode=image.mode,
            )

        # Convert to RGB if necessary (remove alpha channel)
        if image.mode in ("RGBA", "LA", "P"):
            # Create white background
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = rgb_image

        # Resize if image is too large
        if image.width > self.MAX_IMAGE_WIDTH or image.height > self.MAX_IMAGE_HEIGHT:
            # Calculate scaling factor to fit within max dimensions
            width_scale = self.MAX_IMAGE_WIDTH / image.width
            height_scale = self.MAX_IMAGE_HEIGHT / image.height
            scale = min(width_scale, height_scale)

            new_width = int(image.width * scale)
            new_height = int(image.height * scale)

            if self.logger:
                self.logger.debug(
                    "Resizing image",
                    original_size=f"{image.width}x{image.height}",
                    new_size=f"{new_width}x{new_height}",
                    scale=scale,
                )

            # Use LANCZOS for high-quality downsampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Compress to JPEG with quality setting
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
        output.seek(0)

        optimized_image = Image.open(output)

        if self.logger:
            self.logger.info(
                "Image optimized successfully",
                final_size=f"{optimized_image.width}x{optimized_image.height}",
                format="JPEG",
                quality=self.JPEG_QUALITY,
            )

        return optimized_image
