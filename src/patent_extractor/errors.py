class PatentExtractorError(Exception):
    pass


class FileError(PatentExtractorError):
    pass


class XMLParseError(PatentExtractorError):
    pass


class ExtractionError(PatentExtractorError):
    pass

