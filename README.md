# Patent XML Doc-Number Extraction

A production-ready Python program that extracts `doc-number` values from patent XML documents stored in Google Cloud Storage (GCS) format, with priority ordering: **epo format first, then patent-office**.

## Features

- **Priority Ordering**: Extracts doc-numbers in priority order (epo format first, then patent-office)
- **Robust XML Parsing**: Handles malformed XML with error recovery
- **Real-World XML Variations**: Supports namespace variations, case differences, hyphen/underscore variations
- **Comprehensive Error Handling**: Uniform error handling with graceful degradation
- **Production Ready**: Includes guardrails, logging, and edge case handling

## Installation

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency management and virtual environment handling.

### Prerequisites

- Python 3.8 or higher
- `uv` package manager ([installation instructions](https://github.com/astral-sh/uv#installation))

### Setup

1. **Clone the repository** (or download the code):
   ```bash
   git clone <repository-url>
   cd XML_Extraction_Challenge
   ```

2. **Install dependencies using uv**:
   ```bash
   uv venv
   uv pip install -e .
   ```

   Or if you want to install with development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Usage

### Command-Line Interface

The program accepts an XML file path and extracts doc-number values:

```bash
patent-extractor <xml_file>
```

**Example:**
```bash
patent-extractor sample_input.xml
```

**Output (lines format, default):**
```
999000888
66667777
```

**Output (JSON format):**
```bash
patent-extractor sample_input.xml --output-format json
```

**Output:**
```json
[
  "999000888",
  "66667777"
]
```

**Verbose logging:**
```bash
patent-extractor sample_input.xml --verbose
```

### Command-Line Options

- `xml_file`: Path to the XML file to process (required)
- `--output-format {lines,json}`: Output format (default: `lines`)
  - `lines`: One doc-number per line
  - `json`: JSON array of doc-numbers
- `-v, --verbose`: Enable verbose logging for debugging

### Programmatic Usage

You can also use the extraction functionality programmatically:

```python
from pathlib import Path
from patent_extractor import extract_doc_numbers

doc_numbers = extract_doc_numbers(Path("sample_input.xml"))
print(doc_numbers)  # ['999000888', '66667777']
```

## How It Works

1. **XML Parsing**: The program uses `lxml` with error recovery to parse XML files, handling malformed XML gracefully
2. **Normalization**: Attribute names are normalized to handle case variations (e.g., `LOAD-SOURCE` vs `load-source`) and hyphen/underscore differences (e.g., `load-source` vs `load_source`)
3. **Extraction**: Finds all `document-id` elements within `application-reference` elements
4. **Priority Sorting**: Sorts doc-numbers by format priority:
   - Priority 0: `epo` format (including `docdb` load-source)
   - Priority 1: `patent-office` format
   - Priority 99: Unknown formats (lowest priority)
5. **Validation**: Skips invalid or empty doc-numbers with warnings

## Assumptions

The following assumptions are made about the XML document structure:

1. **Structure**: `document-id` elements are nested under `application-reference` elements
2. **Load Source**: The `load-source` attribute identifies the format:
   - `docdb` is treated as `epo` format (same priority)
   - `patent-office` (or variations) identifies patent-office format
3. **Doc-Number Element**: `doc-number` is a child element of `document-id` with text content
4. **Multiple Elements**: Multiple `document-id` elements per `application-reference` are allowed and expected
5. **Attributes**: Attributes may have case variations or hyphen/underscore differences (handled via normalization)
6. **XML Quality**: XML may be malformed or have missing attributes (handled with error recovery and warnings)
7. **Namespaces**: XML may or may not use namespaces; both are supported
8. **Encoding**: XML files may use various encodings (utf-8, utf-16, latin-1, etc.); the program tries multiple encodings

## Real-World XML Variations Handled

The program handles various real-world XML variations:

- **Namespace Variations**: Supports XML with or without namespaces, with different namespace prefixes
- **Case Variations**: Handles uppercase, lowercase, or mixed-case attribute/element names
- **Hyphen vs Underscore**: Normalizes `load-source`, `load_source`, `LOAD-SOURCE`, etc. to the same value
- **Missing Attributes**: Gracefully handles missing `load-source` attributes (logs warning, continues)
- **Empty Values**: Skips empty or whitespace-only doc-number values
- **Malformed XML**: Uses error recovery to extract data from partially malformed XML
- **Multiple Blocks**: Handles multiple `application-reference` blocks in a single file
- **Encoding Issues**: Tries multiple encodings if the default fails

## Error Handling

The program uses a uniform error handling approach:

### Error Categories

1. **FileError**: Raised when the file cannot be read or found
2. **XMLParseError**: Raised when XML parsing fails critically
3. **ExtractionError**: Raised when doc-number extraction fails critically

### Error Recovery

- **Malformed XML**: Uses lxml's error recovery mode to extract partial data
- **Missing Elements**: Logs warnings and continues processing other elements
- **Invalid Values**: Skips invalid doc-numbers with warnings, returns partial results
- **Encoding Issues**: Tries multiple encodings automatically

### Exit Codes

- `0`: Success
- `1`: Error (file error, parsing error, or extraction error)

## Testing

The project includes a comprehensive test suite covering:

- Standard XML format
- Multiple application-reference blocks
- Case variations in attributes
- Missing load-source attributes
- Empty doc-number values
- Missing doc-number elements
- Namespaced XML
- Malformed XML (error recovery)
- Priority ordering verification
- Edge cases (no application-reference, file not found, etc.)

### Running Tests

```bash
# Using uv
uv run pytest

# Or with coverage
uv run pytest --cov=patent_extractor --cov-report=html
```

## Example XML Input

The program expects XML in the following format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root>
  <application-reference ucid="US-XXXXXXXX-A" is-representative="NO" us-art-unit="9999" us-series-code="XX">
    <document-id mxw-id="ABCD99999999" load-source="docdb" format="epo">
      <country>US</country>
      <doc-number>999000888</doc-number>
      <kind>A</kind>
      <date>20051213</date>
      <lang>EN</lang>
    </document-id>
    <document-id mxw-id="ABCD88888888" load-source="patent-office" format="original">
      <country>US</country>
      <doc-number>66667777</doc-number>
      <lang>EN</lang>
    </document-id>
  </application-reference>
</root>
```

### Expected Output

```
999000888
66667777
```

The first doc-number (`999000888`) has priority because its `load-source` is `docdb` (treated as `epo`), which has higher priority than `patent-office`.

## Project Structure

```
.
├── src/
│   └── patent_extractor/
│       ├── __init__.py          # Package initialization
│       ├── extractor.py          # Core extraction logic
│       ├── parser.py             # XML parsing utilities
│       ├── errors.py             # Custom exception classes
│       └── cli.py                # Command-line interface
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py         # Test suite
│   └── sample_data/              # Test XML files
├── sample_input.xml              # Example input file
├── pyproject.toml                # Project configuration (uv)
└── README.md                     # This file
```

## Dependencies

- **lxml**: Robust XML parsing with error recovery
- **typing**: Type hints for better code quality

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Test coverage reporting

## License

This project is provided as-is for the Cypress Data Engineer Challenge.

## Author

Created for the Cyprus Data Engineer Challenge - XML Attribute Extraction task.

