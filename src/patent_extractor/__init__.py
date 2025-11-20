"""
Patent XML doc-number extraction package.

This package provides functionality to extract doc-number values from patent
XML documents, prioritizing epo format over patent-office format.
"""

from patent_extractor.extractor import extract_doc_numbers
from patent_extractor.errors import (
    ExtractionError,
    FileError,
    XMLParseError,
)

__version__ = "1.0.0"
__all__ = [
    "extract_doc_numbers",
    "ExtractionError",
    "FileError",
    "XMLParseError",
]

