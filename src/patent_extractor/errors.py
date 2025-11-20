"""
Custom exception classes for patent XML extraction.
"""


class PatentExtractorError(Exception):
    """Base exception for all patent extractor errors."""

    pass


class FileError(PatentExtractorError):
    """Raised when file operations fail."""

    pass


class XMLParseError(PatentExtractorError):
    """Raised when XML parsing fails."""

    pass


class ExtractionError(PatentExtractorError):
    """Raised when doc-number extraction fails."""

    pass

