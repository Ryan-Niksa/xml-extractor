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
    "patent_office": 1,  # underscore variant
    "patentoffice": 1,   # no separator
}

DEFAULT_PRIORITY = 99  # unknown formats get lowest priority


def normalize_load_source(load_source: str) -> str:
    normalized = load_source.lower().strip()

    # Map docdb to epo
    if normalized in ("epo", "docdb"):
        return "epo"

    # Map various patent-office variations
    if normalized in ("patent-office", "patent_office", "patentoffice"):
        return "patent-office"

    return normalized


def get_priority(load_source: str) -> int:
    normalized = normalize_load_source(load_source)
    return PRIORITY_MAP.get(normalized, DEFAULT_PRIORITY)


def extract_doc_number_from_document_id(document_id_elem: LXMLElement) -> Tuple[str, int, str]:
    try:
        # Need load-source to determine priority - skip if missing
        load_source = get_normalized_attribute(document_id_elem, "load-source")
        if not load_source:
            logger.warning("document-id element missing load-source attribute")
            return None, DEFAULT_PRIORITY, ""

        # Find doc-number, handle namespaces since some files use them
        doc_number_elem = document_id_elem.find("doc-number")
        if doc_number_elem is None:
            # Try finding by local name for namespaced XML
            for child in document_id_elem.iter():
                tag_str = str(child.tag) if hasattr(child, 'tag') else child.tag
                local_name = tag_str.split("}")[-1] if "}" in tag_str else tag_str
                if local_name == "doc-number":
                    doc_number_elem = child
                    break

        if doc_number_elem is None:
            logger.warning("document-id element missing doc-number child element")
            return None, DEFAULT_PRIORITY, load_source

        doc_number = extract_text_content(doc_number_elem)
        if not doc_number:
            logger.warning("doc-number element has empty text content")
            return None, DEFAULT_PRIORITY, load_source

        priority = get_priority(load_source)

        return doc_number, priority, load_source

    except Exception as e:
        logger.error(f"Error extracting doc-number from document-id element: {e}")
        raise ExtractionError(f"Failed to extract doc-number: {e}")


def extract_doc_numbers(file_path: Path) -> List[str]:
    logger.info(f"Extracting doc-numbers from: {file_path}")

    try:
        root = parse_xml_file(file_path)
    except Exception as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise

    # Find all application-reference blocks
    application_refs = find_elements_with_namespace_handling(root, "application-reference")
    logger.debug(f"Found {len(application_refs)} application-reference element(s)")

    if not application_refs:
        logger.warning("No application-reference elements found in XML")
        return []

    doc_number_entries: List[Tuple[str, int, str]] = []

    for app_ref in application_refs:
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
                continue  # Keep going with other elements
            except Exception as e:
                logger.error(f"Unexpected error extracting doc-number: {e}")
                continue

    if not doc_number_entries:
        logger.warning("No valid doc-number values found in XML")
        return []

    # Sort by priority, then doc-number for consistent ordering
    doc_number_entries.sort(key=lambda x: (x[1], x[0]))

    result = [doc_number for doc_number, _, _ in doc_number_entries]

    logger.info(f"Successfully extracted {len(result)} doc-number value(s)")
    logger.debug(f"Extracted doc-numbers in order: {result}")

    return result

