import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from patent_extractor.errors import ExtractionError, FileError, XMLParseError
from patent_extractor.extractor import extract_doc_numbers

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def output_results(doc_numbers: List[str], output_format: str = "lines") -> None:
    if output_format == "json":
        print(json.dumps(doc_numbers, indent=2))
    else:
        for doc_number in doc_numbers:
            print(doc_number)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract doc-numbers from patent XML files (epo priority > patent-office)"
    )
    parser.add_argument(
        "xml_file",
        type=Path,
        help="Path to the XML file to process",
    )
    parser.add_argument(
        "--output-format",
        choices=["lines", "json"],
        default="lines",
        help="Output format: 'lines' (one per line) or 'json' (JSON array). Default: lines",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    xml_file = args.xml_file
    if not xml_file.exists():
        logger.error(f"File not found: {xml_file}")
        print(f"Error: File not found: {xml_file}", file=sys.stderr)
        return 1

    if not xml_file.is_file():
        logger.error(f"Path is not a file: {xml_file}")
        print(f"Error: Path is not a file: {xml_file}", file=sys.stderr)
        return 1

    try:
        doc_numbers = extract_doc_numbers(xml_file)
    except FileError as e:
        logger.error(f"File error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except XMLParseError as e:
        logger.error(f"XML parsing error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ExtractionError as e:
        logger.error(f"Extraction error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    try:
        output_results(doc_numbers, output_format=args.output_format)
        return 0
    except Exception as e:
        logger.error(f"Error outputting results: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

