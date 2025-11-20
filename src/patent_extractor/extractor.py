"""
Core extraction logic for doc-number values from patent XML documents.

Extracts doc-number values with priority ordering: epo format first, then patent-office.
"""

import logging
from pathlib import Path
from typing import List, Tuple

from lxml.etree import Element as LXMLElement

from patent_extractor.errors import ExtractionError, XMLParseError
from patent_extractor.parser import (
    extract_text_content,
    find_elements_with_namespace_handling,
    get_normalized_attribute,
    parse_xml_file,
)

logger = logging.getLogger(__name__)

# Priority mapping: lower number = higher priority
PRIORITY_MAP = {
    "epo": 0,
    "docdb": 0,  # docdb is treated as epo
    "patent-office": 1,
    "patent_office": 1,  # Handle underscore variation
    "patentoffice": 1,  # Handle no separator variation
}

# Default priority for unknown formats
DEFAULT_PRIORITY = 99


def normalize_load_source(load_source: str) -> str:
    """
    Normalize load-source value to standard format names.

    Args:
        load_source: The load-source attribute value

    Returns:
        Normalized format name (epo or patent-office)
    """
    normalized = load_source.lower().strip()

    # Map docdb to epo
    if normalized in ("epo", "docdb"):
        return "epo"

    # Map various patent-office variations
    if normalized in ("patent-office", "patent_office", "patentoffice"):
        return "patent-office"

    return normalized


def get_priority(load_source: str) -> int:
    """
    Get priority value for a given load-source.

    Args:
        load_source: The normalized load-source value

    Returns:
        Priority value (lower = higher priority)
    """
    normalized = normalize_load_source(load_source)
    return PRIORITY_MAP.get(normalized, DEFAULT_PRIORITY)


def extract_doc_number_from_document_id(document_id_elem: LXMLElement) -> Tuple[str, int, str]:
    """
    Extract doc-number and priority from a document-id element.

    Args:
        document_id_elem: The document-id XML element

    Returns:
        Tuple of (doc-number, priority, load-source) or (None, DEFAULT_PRIORITY, "") if extraction fails

    Raises:
        ExtractionError: If extraction fails critically
    """
    try:
        # Get load-source attribute
        load_source = get_normalized_attribute(document_id_elem, "load-source")
        if not load_source:
            logger.warning("document-id element missing load-source attribute")
            load_source = "unknown"

        # Find doc-number element
        doc_number_elem = document_id_elem.find("doc-number")
        if doc_number_elem is None:
            logger.warning("document-id element missing doc-number child element")
            return None, DEFAULT_PRIORITY, load_source

        # Extract doc-number text content
        doc_number = extract_text_content(doc_number_elem)
        if not doc_number:
            logger.warning("doc-number element has empty text content")
            return None, DEFAULT_PRIORITY, load_source

        # Calculate priority
        priority = get_priority(load_source)

        return doc_number, priority, load_source

    except Exception as e:
        logger.error(f"Error extracting doc-number from document-id element: {e}")
        raise ExtractionError(f"Failed to extract doc-number: {e}")


def extract_doc_numbers(file_path: Path) -> List[str]:
    """
    Extract all doc-number values from a patent XML file in priority order.

    Priority order:
    1. epo format (including docdb load-source)
    2. patent-office format

    Args:
        file_path: Path to the XML file

    Returns:
        List of doc-number values in priority order

    Raises:
        FileError: If the file cannot be read
        XMLParseError: If the XML cannot be parsed
        ExtractionError: If extraction fails critically

    Assumptions:
        - document-id elements are nested under application-reference elements
        - load-source attribute identifies format (docdb treated as epo)
        - doc-number is a child element with text content
        - Multiple document-id elements per application-reference are allowed
        - Attributes may have case variations or hyphen/underscore differences
        - XML may be malformed or have missing attributes (will log warnings and continue)
    """
    logger.info(f"Extracting doc-numbers from: {file_path}")

    # Parse XML file
    try:
        root = parse_xml_file(file_path)
    except Exception as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise

    # Find all application-reference elements
    application_refs = find_elements_with_namespace_handling(root, "application-reference")
    logger.debug(f"Found {len(application_refs)} application-reference element(s)")

    if not application_refs:
        logger.warning("No application-reference elements found in XML")
        return []

    # Collect all doc-number entries with their priorities
    doc_number_entries: List[Tuple[str, int, str]] = []

    for app_ref in application_refs:
        # Find all document-id elements within this application-reference
        document_ids = find_elements_with_namespace_handling(app_ref, "document-id")
        logger.debug(f"Found {len(document_ids)} document-id element(s) in application-reference")

        for doc_id in document_ids:
            try:
                doc_number, priority, load_source = extract_doc_number_from_document_id(doc_id)

                if doc_number:
                    doc_number_entries.append((doc_number, priority, load_source))
                    logger.debug(
                        f"Extracted doc-number: {doc_number}, priority: {priority}, "
                        f"load-source: {load_source}"
                    )
                else:
                    logger.warning("Skipping document-id with invalid or missing doc-number")

            except ExtractionError as e:
                logger.error(f"Critical error extracting doc-number: {e}")
                # Continue processing other document-id elements
                continue
            except Exception as e:
                logger.error(f"Unexpected error extracting doc-number: {e}")
                # Continue processing other document-id elements
                continue

    if not doc_number_entries:
        logger.warning("No valid doc-number values found in XML")
        return []

    # Sort by priority (lower number = higher priority), then by doc-number for stability
    doc_number_entries.sort(key=lambda x: (x[1], x[0]))

    # Extract just the doc-numbers in order
    result = [doc_number for doc_number, _, _ in doc_number_entries]

    logger.info(f"Successfully extracted {len(result)} doc-number value(s)")
    logger.debug(f"Extracted doc-numbers in order: {result}")

    return result

