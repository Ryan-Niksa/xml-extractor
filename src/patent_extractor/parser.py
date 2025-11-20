"""
XML parsing utilities with normalization and error recovery.

Handles namespace variations, attribute name normalization (case/hyphen variations),
and provides robust error recovery for malformed XML.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from lxml import etree
from lxml.etree import Element as LXMLElement

from patent_extractor.errors import FileError, XMLParseError

logger = logging.getLogger(__name__)

# Common encodings to try if the default fails
ENCODINGS_TO_TRY = ["utf-8", "utf-16", "latin-1", "iso-8859-1", "cp1252"]


def normalize_attribute_name(name: str) -> str:
    """
    Normalize attribute names to handle case and hyphen/underscore variations.

    Args:
        name: The attribute name to normalize

    Returns:
        Normalized attribute name in lowercase with hyphens converted to underscores
    """
    return name.lower().replace("-", "_").replace("_", "_")


def normalize_attribute_value(value: str) -> str:
    """
    Normalize attribute values by stripping whitespace and converting to lowercase.

    Args:
        value: The attribute value to normalize

    Returns:
        Normalized attribute value
    """
    return value.strip().lower() if value else ""


def get_normalized_attribute(element: LXMLElement, attr_name: str) -> Optional[str]:
    """
    Get an attribute value from an element with normalization.

    Handles case variations and hyphen/underscore differences in attribute names.

    Args:
        element: The XML element
        attr_name: The attribute name (will be normalized for lookup)

    Returns:
        The normalized attribute value, or None if not found
    """
    if not element.attrib:
        return None

    normalized_attr = normalize_attribute_name(attr_name)

    # Try exact match first (case-insensitive)
    for key, value in element.attrib.items():
        if normalize_attribute_name(key) == normalized_attr:
            return normalize_attribute_value(value)

    return None


def parse_xml_file(file_path: Path) -> LXMLElement:
    """
    Parse an XML file with error recovery and encoding detection.

    Args:
        file_path: Path to the XML file

    Returns:
        Parsed ElementTree

    Raises:
        FileError: If the file cannot be read
        XMLParseError: If the XML cannot be parsed even with error recovery
    """
    if not file_path.exists():
        raise FileError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileError(f"Path is not a file: {file_path}")

    # Try to read the file with different encodings
    content = None
    encoding_used = None

    for encoding in ENCODINGS_TO_TRY:
        try:
            with open(file_path, "rb") as f:
                raw_content = f.read()
                content = raw_content.decode(encoding)
                encoding_used = encoding
                logger.debug(f"Successfully read file with encoding: {encoding}")
                break
        except (UnicodeDecodeError, IOError) as e:
            logger.debug(f"Failed to read with encoding {encoding}: {e}")
            continue

    if content is None:
        raise FileError(f"Could not read file with any supported encoding: {file_path}")

    # Parse XML with error recovery
    try:
        # Use recover parser to handle malformed XML
        parser = etree.XMLParser(recover=True, huge_tree=True)
        tree = etree.fromstring(content.encode(encoding_used), parser=parser)
        logger.debug(f"Successfully parsed XML file: {file_path}")
        return tree
    except etree.XMLSyntaxError as e:
        raise XMLParseError(f"Failed to parse XML file {file_path}: {e}")
    except Exception as e:
        raise XMLParseError(f"Unexpected error parsing XML file {file_path}: {e}")


def find_elements_with_namespace_handling(
    root: LXMLElement, tag_name: str, namespace_map: Optional[Dict[str, str]] = None
) -> List[LXMLElement]:
    """
    Find elements by tag name, handling namespace variations.

    Args:
        root: Root element to search from
        tag_name: Tag name to find (local name, namespace-agnostic)
        namespace_map: Optional namespace map for explicit namespace handling

    Returns:
        List of matching elements
    """
    if namespace_map:
        # Use explicit namespace
        try:
            return root.findall(f".//{{{namespace_map.get('ns', '')}}}{tag_name}", namespaces=namespace_map)
        except Exception:
            pass

    # Try to find by local name (handles namespaced and non-namespaced)
    results = []

    # First, try without namespace (direct tag match)
    results.extend(root.findall(f".//{tag_name}"))

    # Also try to match local name regardless of namespace
    for elem in root.iter():
        # Extract local name (after last '}' or full tag if no namespace)
        # Convert tag to string to handle QName objects and cython types
        tag_str = str(elem.tag) if hasattr(elem, 'tag') else elem.tag
        local_name = tag_str.split("}")[-1] if "}" in tag_str else tag_str
        if local_name == tag_name and elem not in results:
            results.append(elem)

    return results


def extract_text_content(element: LXMLElement) -> str:
    """
    Extract and normalize text content from an element.

    Args:
        element: The XML element

    Returns:
        Normalized text content (stripped of whitespace)
    """
    if element is None:
        return ""

    # Get direct text and tail text
    text = (element.text or "").strip()
    tail = (element.tail or "").strip()

    # Also collect text from direct text nodes only (not nested)
    return text

