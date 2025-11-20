"""
Comprehensive test suite for patent XML doc-number extraction.

Tests cover standard cases, edge cases, error scenarios, and XML variations.
"""

import logging
from pathlib import Path

import pytest

from patent_extractor.errors import ExtractionError, FileError, XMLParseError
from patent_extractor.extractor import extract_doc_numbers

# Set up test logging
logging.basicConfig(level=logging.DEBUG)

# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "sample_data"


def test_standard_xml():
    """Test extraction from standard XML format matching challenge specification."""
    xml_file = TEST_DATA_DIR / "standard.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should return epo first, then patent-office
    assert doc_numbers == ["999000888", "66667777"]
    assert len(doc_numbers) == 2


def test_multiple_application_references():
    """Test extraction from XML with multiple application-reference blocks."""
    xml_file = TEST_DATA_DIR / "multiple_app_refs.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should return all epo format first, then all patent-office
    # epo: 111111111, 333333333
    # patent-office: 222222222, 444444444
    assert doc_numbers == ["111111111", "333333333", "222222222", "444444444"]
    assert len(doc_numbers) == 4


def test_case_variations():
    """Test extraction with case variations in attribute names."""
    xml_file = TEST_DATA_DIR / "case_variations.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should handle uppercase and underscore variations
    assert doc_numbers == ["999000888", "66667777"]
    assert len(doc_numbers) == 2


def test_missing_load_source():
    """Test extraction when load-source attribute is missing."""
    xml_file = TEST_DATA_DIR / "missing_load_source.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should skip document-id without load-source, but extract others
    # Only the patent-office one should be extracted (missing load-source should be skipped)
    assert doc_numbers == ["66667777"]
    assert len(doc_numbers) == 1


def test_empty_doc_number():
    """Test extraction when doc-number elements are empty or whitespace-only."""
    xml_file = TEST_DATA_DIR / "empty_doc_number.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should skip empty doc-numbers, only extract valid ones
    assert doc_numbers == ["66667777"]
    assert len(doc_numbers) == 1


def test_missing_doc_number():
    """Test extraction when doc-number element is missing."""
    xml_file = TEST_DATA_DIR / "missing_doc_number.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should skip document-id without doc-number element
    assert doc_numbers == ["66667777"]
    assert len(doc_numbers) == 1


def test_namespaced_xml():
    """Test extraction from XML with namespace prefixes."""
    xml_file = TEST_DATA_DIR / "namespaced.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should handle namespaced elements
    assert doc_numbers == ["999000888", "66667777"]
    assert len(doc_numbers) == 2


def test_malformed_xml():
    """Test extraction from malformed XML (should use error recovery)."""
    xml_file = TEST_DATA_DIR / "malformed.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should still extract what it can with error recovery
    assert "999000888" in doc_numbers
    # May or may not get the second one depending on recovery
    assert len(doc_numbers) >= 1


def test_priority_ordering():
    """Test that priority ordering works correctly (epo before patent-office)."""
    xml_file = TEST_DATA_DIR / "priority_order.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should return all epo format first, then patent-office
    # epo (priority 0): 222222222, 333333333
    # patent-office (priority 1): 111111111, 444444444
    assert doc_numbers == ["222222222", "333333333", "111111111", "444444444"]
    assert len(doc_numbers) == 4


def test_no_application_reference():
    """Test extraction when no application-reference elements exist."""
    xml_file = TEST_DATA_DIR / "no_application_reference.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Should return empty list
    assert doc_numbers == []
    assert len(doc_numbers) == 0


def test_file_not_found():
    """Test error handling when file doesn't exist."""
    xml_file = TEST_DATA_DIR / "nonexistent.xml"

    with pytest.raises(FileError):
        extract_doc_numbers(xml_file)


def test_docdb_treated_as_epo():
    """Test that docdb load-source is treated as epo format."""
    xml_file = TEST_DATA_DIR / "standard.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # docdb should have same priority as epo (priority 0)
    # In standard.xml, docdb comes first, then patent-office
    # So docdb (999000888) should come before patent-office (66667777)
    assert doc_numbers[0] == "999000888"  # docdb
    assert doc_numbers[1] == "66667777"  # patent-office


def test_multiple_doc_ids_same_source():
    """Test handling of multiple document-id elements with same load-source."""
    xml_file = TEST_DATA_DIR / "priority_order.xml"
    doc_numbers = extract_doc_numbers(xml_file)

    # Multiple epo sources should all come first
    epo_docs = [d for d in doc_numbers if d in ["222222222", "333333333"]]
    patent_office_docs = [d for d in doc_numbers if d in ["111111111", "444444444"]]

    # Verify ordering: all epo before any patent-office
    assert all(doc in doc_numbers[:2] for doc in epo_docs)
    assert all(doc in doc_numbers[2:] for doc in patent_office_docs)


def test_whitespace_in_doc_number():
    """Test that whitespace in doc-number is properly stripped."""
    # Create a temporary XML with whitespace
    import tempfile

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <application-reference ucid="US-XXXXXXXX-A">
    <document-id mxw-id="ABCD99999999" load-source="epo" format="epo">
      <country>US</country>
      <doc-number>  999000888  </doc-number>
    </document-id>
  </application-reference>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(xml_content)
        temp_file = Path(f.name)

    try:
        doc_numbers = extract_doc_numbers(temp_file)
        assert doc_numbers == ["999000888"]
    finally:
        temp_file.unlink()

