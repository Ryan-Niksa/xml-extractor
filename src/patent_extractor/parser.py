"""XML parsing stuff - handles namespaces, normalizes attributes, deals with broken XML."""

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
    """Normalize attribute names - lowercase, handle hyphens/underscores."""
    # Both hyphens and underscores become underscores for comparison
    return name.lower().replace("-", "_").replace("_", "_")


def normalize_attribute_value(value: str) -> str:
    """Strip whitespace and lowercase attribute values."""
    return value.strip().lower() if value else ""


def get_normalized_attribute(element: LXMLElement, attr_name: str) -> Optional[str]:
    """Get attribute value with normalization - handles LOAD-SOURCE vs load_source etc."""
    if not element.attrib:
        return None

    normalized_attr = normalize_attribute_name(attr_name)

    for key, value in element.attrib.items():
        if normalize_attribute_name(key) == normalized_attr:
            return normalize_attribute_value(value)

    return None


def parse_xml_file(file_path: Path) -> LXMLElement:
    """
    Parse XML file with error recovery. Tries multiple encodings if needed.
    
    Uses lxml's recover mode so it can handle slightly broken XML files.
    """
    if not file_path.exists():
        raise FileError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileError(f"Path is not a file: {file_path}")

    # Try different encodings - some files are weird
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

    try:
        # Use recover mode - handles broken XML gracefully
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
    """Find elements by tag name - works with or without namespaces."""
    if namespace_map:
        try:
            return root.findall(f".//{{{namespace_map.get('ns', '')}}}{tag_name}", namespaces=namespace_map)
        except Exception:
            pass

    results = []
    # Try direct match first
    results.extend(root.findall(f".//{tag_name}"))

    # Also match by local name for namespaced elements (ns:tag -> tag)
    for elem in root.iter():
        tag_str = str(elem.tag) if hasattr(elem, 'tag') else elem.tag
        local_name = tag_str.split("}")[-1] if "}" in tag_str else tag_str
        if local_name == tag_name and elem not in results:
            results.append(elem)

    return results


def extract_text_content(element: LXMLElement) -> str:
    """Extract text content from element, stripped of whitespace."""
    if element is None:
        return ""
    return (element.text or "").strip()

