# Patent XML Doc-Number Extractor

Simple tool to extract `doc-number` values from patent XML files. Prioritizes epo format over patent-office.

## Quick Start

Install with uv:

```bash
uv venv
uv pip install -e .
```

Or with regular pip in the venv:

```bash
pip install -e .
```

Run it:

```bash
patent-extractor sample_input.xml
```

Output:
```
999000888
66667777
```

The epo/docdb ones come first, then patent-office.

## Usage

Basic usage - just pass an XML file:

```bash
patent-extractor sample_input.xml
```

JSON output:

```bash
patent-extractor sample_input.xml --output-format json
```

Verbose mode (shows what's happening):

```bash
patent-extractor sample_input.xml --verbose
```

You can also use it in Python:

```python
from pathlib import Path
from patent_extractor import extract_doc_numbers

doc_numbers = extract_doc_numbers(Path("sample_input.xml"))
```

## What It Does

1. Parses the XML (handles broken XML with error recovery)
2. Finds all `document-id` elements inside `application-reference` blocks
3. Extracts the `doc-number` from each one
4. Sorts by priority: epo/docdb first, then patent-office
5. Returns the list in priority order

## Handling Real-World XML

The code handles a bunch of variations you see in actual patent data:

- **Namespaces** - Works with `ns:document-id` or just `document-id`
- **Case variations** - `LOAD-SOURCE`, `load-source`, `Load_Source` all work
- **Hyphen vs underscore** - Normalizes `load-source` and `load_source` the same way
- **Missing attributes** - Skips elements without `load-source` (logs a warning)
- **Broken XML** - Uses lxml's recover mode to extract what it can
- **Multiple encodings** - Tries utf-8, utf-16, latin-1, etc.

## Assumptions

- `document-id` elements are inside `application-reference` elements
- `load-source` attribute tells us the format (docdb = epo for priority purposes)
- `doc-number` is a child element with text content
- Multiple `document-id` elements per `application-reference` are fine
- XML might be messy - that's ok, we try to handle it

## Priority Ordering

Priority works like this:
- **Priority 0**: epo format (including docdb)
- **Priority 1**: patent-office format
- **Priority 99**: Unknown formats (skipped by default since they need load-source)

Lower number = higher priority. All epo ones come first, then patent-office.

## Testing

Run the tests:

```bash
pytest tests/ -v
```

There are 14 tests covering the edge cases - namespaces, missing attributes, broken XML, etc.

## Project Structure

```
src/patent_extractor/
  ├── extractor.py   # Main extraction logic
  ├── parser.py      # XML parsing utilities
  ├── cli.py         # Command-line interface
  └── errors.py      # Custom exceptions

tests/
  ├── test_extractor.py
  └── sample_data/   # Test XML files
```

## Dependencies

- `lxml` - XML parsing with error recovery

Dev dependencies:
- `pytest` - Testing
- `pytest-cov` - Coverage reports

## Notes

This was built for a data engineering challenge. The XML from GCS can be messy, so the code tries to be resilient. It logs warnings when it skips elements but keeps going - better to get partial results than fail completely.

If you find edge cases that break it, feel free to open an issue or submit a PR.
