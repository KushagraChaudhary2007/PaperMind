from dataclasses import dataclass
from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """
    Raised when text cannot be extracted from a PDF.
    """


@dataclass(slots=True)
class ExtractedPDF:
    text: str
    page_count: int
    character_count: int
    extraction_status: str


def extract_pdf_text(
    file_path: Path,
) -> ExtractedPDF:
    """
    Extracts text from every page of a PDF.

    Returns:
        ExtractedPDF containing:
        - extracted text
        - number of pages
        - character count
        - extraction status
    """

    try:
        page_sections: list[str] = []

        with pymupdf.open(file_path) as document:
            if document.needs_pass:
                raise PDFExtractionError(
                    "Password-protected PDFs are not supported."
                )

            page_count = document.page_count

            for page_number, page in enumerate(
                document,
                start=1,
            ):
                page_text = page.get_text(
                    "text",
                    sort=True,
                ).strip()

                if page_text:
                    page_sections.append(
                        (
                            f"--- Page {page_number} ---\n"
                            f"{page_text}"
                        )
                    )

        extracted_text = "\n\n".join(
            page_sections
        ).strip()

        character_count = len(extracted_text)

        if extracted_text:
            extraction_status = "ready"
        else:
            extraction_status = "needs_ocr"

        return ExtractedPDF(
            text=extracted_text,
            page_count=page_count,
            character_count=character_count,
            extraction_status=extraction_status,
        )

    except PDFExtractionError:
        raise

    except Exception as error:
        raise PDFExtractionError(
            "PaperMind could not read this PDF."
        ) from error