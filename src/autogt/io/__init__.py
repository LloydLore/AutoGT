"""File I/O processing module for AutoGT platform.

Provides comprehensive file parsing and export capabilities for automotive
TARA analysis data across multiple formats (Excel, CSV, JSON, text).
"""

from .processor import (
    FileProcessor,
    UnifiedParseResult,
    process_file,
    process_files,
    validate_file,
    get_supported_formats
)

from .excel_parser import (
    ExcelParser,
    ExcelParseResult,
    parse_excel_file
)

from .csv_parser import (
    CsvParser,
    CsvParseResult,
    parse_csv_file,
    detect_csv_format
)

from .json_parser import (
    JsonParser,
    JsonParseResult,
    parse_json_file,
    validate_json_schema,
    detect_json_structure
)

from .text_parser import (
    TextParser,
    TextParseResult,
    parse_text_file,
    analyze_text_content,
    extract_automotive_terms
)

from .exporters import (
    ExportManager,
    ExportResult,
    JsonExporter,
    CsvExporter,
    ExcelExporter,
    export_tara_data,
    get_export_formats
)


__all__ = [
    # Main processor
    'FileProcessor',
    'UnifiedParseResult',
    'process_file',
    'process_files',
    'validate_file',
    'get_supported_formats',
    
    # Individual parsers
    'ExcelParser',
    'ExcelParseResult',
    'parse_excel_file',
    'CsvParser',
    'CsvParseResult',
    'parse_csv_file',
    'detect_csv_format',
    'JsonParser',
    'JsonParseResult',
    'parse_json_file',
    'validate_json_schema',
    'detect_json_structure',
    'TextParser',
    'TextParseResult',
    'parse_text_file',
    'analyze_text_content',
    'extract_automotive_terms',
    
    # Exporters
    'ExportManager',
    'ExportResult',
    'JsonExporter',
    'CsvExporter',
    'ExcelExporter',
    'export_tara_data',
    'get_export_formats'
]