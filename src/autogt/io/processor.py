"""Unified file processor that handles multiple input formats.

Coordinates Excel, CSV, JSON, and text parsers to provide a single
interface for processing automotive TARA data files.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from datetime import datetime

from .excel_parser import ExcelParser, ExcelParseResult
from .csv_parser import CsvParser, CsvParseResult
from .json_parser import JsonParser, JsonParseResult
from .text_parser import TextParser, TextParseResult
from ..core.exceptions import FileParsingError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class UnifiedParseResult:
    """Unified result from file processing with metadata."""
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[str]
    confidence_score: float
    parser_used: str
    processing_time_ms: int
    file_info: Dict[str, Any]


class FileProcessor:
    """Unified file processor for automotive TARA analysis data.
    
    Automatically detects file format and uses appropriate parser
    to extract asset and threat information.
    """
    
    def __init__(self):
        """Initialize file processor with all parsers."""
        self.parsers = {
            'excel': ExcelParser(),
            'csv': CsvParser(),
            'json': JsonParser(),
            'text': TextParser()
        }
        
        # File extension to parser mapping
        self.extension_mapping = {
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.csv': 'csv',
            '.tsv': 'csv',
            '.json': 'json',
            '.jsonl': 'json',
            '.txt': 'text',
            '.md': 'text',
            '.rst': 'text',
            '.log': 'text',
            '.text': 'text'
        }
        
        # MIME type to parser mapping (for future web upload support)
        self.mime_mapping = {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel',
            'application/vnd.ms-excel': 'excel',
            'text/csv': 'csv',
            'application/json': 'json',
            'text/plain': 'text',
            'text/markdown': 'text'
        }
        
    def process_file(self, file_path: Union[str, Path], 
                    parser_hint: Optional[str] = None,
                    validation_strict: bool = False) -> UnifiedParseResult:
        """Process file and extract TARA data using appropriate parser.
        
        Args:
            file_path: Path to file to process
            parser_hint: Optional hint for which parser to use ('excel', 'csv', 'json', 'text')
            validation_strict: Whether to use strict validation rules
            
        Returns:
            UnifiedParseResult with parsed data and metadata
            
        Raises:
            FileParsingError: If file cannot be processed
            ValidationError: If validation fails in strict mode
        """
        file_path = Path(file_path)
        start_time = datetime.now()
        
        try:
            # Get file information
            file_info = self._get_file_info(file_path)
            
            # Determine which parser to use
            parser_name = self._select_parser(file_path, parser_hint)
            parser = self.parsers[parser_name]
            
            logger.info(f"Processing {file_path} using {parser_name} parser")
            
            # Parse file using selected parser
            parse_result = parser.parse_file(file_path)
            
            # Convert parser-specific result to unified format
            unified_result = self._convert_to_unified_result(
                parse_result, parser_name, file_info, start_time
            )
            
            # Additional validation if requested
            if validation_strict:
                self._strict_validation(unified_result)
            
            # Log processing summary
            logger.info(
                f"Processed {file_path.name}: {len(unified_result.assets)} assets, "
                f"{len(unified_result.threats)} threats, confidence: {unified_result.confidence_score:.2f}"
            )
            
            return unified_result
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
            raise FileParsingError(f"File processing failed: {str(e)}")
    
    def process_multiple_files(self, file_paths: List[Union[str, Path]],
                              merge_results: bool = True) -> Union[UnifiedParseResult, List[UnifiedParseResult]]:
        """Process multiple files and optionally merge results.
        
        Args:
            file_paths: List of file paths to process
            merge_results: Whether to merge all results into one
            
        Returns:
            Single UnifiedParseResult if merge_results=True, otherwise list of results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {str(e)}")
                continue
        
        if not results:
            raise FileParsingError("No files could be processed successfully")
        
        if merge_results:
            return self._merge_results(results)
        else:
            return results
    
    def validate_file(self, file_path: Union[str, Path]) -> tuple[bool, List[str], str]:
        """Validate if file can be processed without full parsing.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_valid, error_messages, suggested_parser)
        """
        file_path = Path(file_path)
        errors = []
        
        try:
            # Check file exists and is accessible
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return False, errors, 'unknown'
            
            if not file_path.is_file():
                errors.append(f"Path is not a file: {file_path}")
                return False, errors, 'unknown'
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:  # Conservative limit
                errors.append(f"File too large: {file_size_mb:.1f}MB")
                return False, errors, 'unknown'
            
            # Determine parser and check format-specific validation
            parser_name = self._select_parser(file_path)
            parser = self.parsers[parser_name]
            
            # Basic parser validation
            if hasattr(parser, '_validate_file'):
                try:
                    parser._validate_file(file_path)
                except (FileParsingError, ValidationError) as e:
                    errors.append(str(e))
            
            is_valid = len(errors) == 0
            return is_valid, errors, parser_name
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors, 'unknown'
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get information about supported file formats.
        
        Returns:
            Dictionary mapping parser names to supported extensions
        """
        return {
            'excel': ['.xlsx', '.xls'],
            'csv': ['.csv', '.tsv'],
            'json': ['.json', '.jsonl'],
            'text': ['.txt', '.md', '.rst', '.log', '.text']
        }
    
    def get_parser_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get information about each parser's capabilities.
        
        Returns:
            Dictionary with parser capabilities and limitations
        """
        return {
            'excel': {
                'max_file_size_mb': 10,
                'supports_multiple_sheets': True,
                'structured_data': True,
                'confidence_typical': 0.8,
                'best_for': 'Structured automotive data with assets and threats in tables'
            },
            'csv': {
                'max_file_size_mb': 10,
                'supports_multiple_sheets': False,
                'structured_data': True,
                'confidence_typical': 0.7,
                'best_for': 'Tabular data exported from databases or other tools'
            },
            'json': {
                'max_file_size_mb': 10,
                'supports_multiple_sheets': False,
                'structured_data': True,
                'confidence_typical': 0.85,
                'best_for': 'API responses or structured data exports in JSON format'
            },
            'text': {
                'max_file_size_mb': 5,
                'supports_multiple_sheets': False,
                'structured_data': False,
                'confidence_typical': 0.4,
                'best_for': 'Documentation, requirements, or unstructured reports'
            }
        }
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract file information and metadata."""
        stat = file_path.stat()
        
        return {
            'filename': file_path.name,
            'extension': file_path.suffix.lower(),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 3),
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'absolute_path': str(file_path.absolute())
        }
    
    def _select_parser(self, file_path: Path, parser_hint: Optional[str] = None) -> str:
        """Select appropriate parser based on file extension or hint."""
        # Use hint if provided and valid
        if parser_hint and parser_hint in self.parsers:
            return parser_hint
        
        # Select based on file extension
        extension = file_path.suffix.lower()
        parser_name = self.extension_mapping.get(extension)
        
        if not parser_name:
            # Try to guess based on content for extensionless files
            parser_name = self._guess_parser_from_content(file_path)
        
        if not parser_name:
            raise FileParsingError(f"Unsupported file format: {extension}")
        
        return parser_name
    
    def _guess_parser_from_content(self, file_path: Path) -> Optional[str]:
        """Guess parser type by examining file content."""
        try:
            # Read first few bytes to detect format
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Check for Excel signatures
            if header.startswith(b'PK\x03\x04') or header.startswith(b'\xd0\xcf\x11\xe0'):
                return 'excel'
            
            # Try to decode as text and check content
            try:
                text_content = header.decode('utf-8')
                
                # Check for JSON
                if text_content.strip().startswith(('{', '[')):
                    return 'json'
                
                # Check for CSV (comma or semicolon separated)
                lines = text_content.split('\n')[:5]
                if len(lines) > 1:
                    for line in lines:
                        if ',' in line or ';' in line or '\t' in line:
                            return 'csv'
                
                # Default to text
                return 'text'
                
            except UnicodeDecodeError:
                # Binary file, try Excel
                return 'excel'
                
        except Exception:
            # Default to text if all else fails
            return 'text'
    
    def _convert_to_unified_result(self, parse_result: Union[ExcelParseResult, CsvParseResult, 
                                                            JsonParseResult, TextParseResult],
                                 parser_name: str, file_info: Dict[str, Any],
                                 start_time: datetime) -> UnifiedParseResult:
        """Convert parser-specific result to unified format."""
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create unified metadata
        unified_metadata = {
            'parser_used': parser_name,
            'processing_timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'file_info': file_info,
            'original_metadata': parse_result.metadata
        }
        
        # Add parser-specific metadata
        if hasattr(parse_result, 'detected_format'):
            unified_metadata['detected_format'] = parse_result.detected_format
        elif hasattr(parse_result, 'detected_schema'):
            unified_metadata['detected_schema'] = parse_result.detected_schema
        elif hasattr(parse_result, 'detected_patterns'):
            unified_metadata['detected_patterns'] = parse_result.detected_patterns
        
        return UnifiedParseResult(
            assets=parse_result.assets,
            threats=parse_result.threats,
            metadata=unified_metadata,
            validation_errors=parse_result.validation_errors,
            confidence_score=parse_result.confidence_score,
            parser_used=parser_name,
            processing_time_ms=processing_time,
            file_info=file_info
        )
    
    def _strict_validation(self, result: UnifiedParseResult) -> None:
        """Perform strict validation on parsing results."""
        errors = []
        
        # Check minimum data requirements
        if not result.assets and not result.threats:
            errors.append("No assets or threats found in file")
        
        # Check confidence threshold
        if result.confidence_score < 0.5:
            errors.append(f"Low confidence score: {result.confidence_score:.2f} < 0.5")
        
        # Check for critical validation errors
        critical_keywords = ['duplicate', 'missing', 'invalid', 'too short', 'too generic']
        critical_errors = [error for error in result.validation_errors 
                          if any(keyword in error.lower() for keyword in critical_keywords)]
        
        if critical_errors:
            errors.extend(critical_errors)
        
        if errors:
            raise ValidationError(f"Strict validation failed: {'; '.join(errors)}")
    
    def _merge_results(self, results: List[UnifiedParseResult]) -> UnifiedParseResult:
        """Merge multiple parsing results into one."""
        if not results:
            raise ValueError("Cannot merge empty results list")
        
        if len(results) == 1:
            return results[0]
        
        # Combine assets and threats
        all_assets = []
        all_threats = []
        all_errors = []
        
        asset_names = set()
        threat_names = set()
        
        for result in results:
            # Merge assets, avoiding duplicates
            for asset in result.assets:
                if asset['name'] not in asset_names:
                    all_assets.append(asset)
                    asset_names.add(asset['name'])
            
            # Merge threats, avoiding duplicates
            for threat in result.threats:
                if threat['name'] not in threat_names:
                    all_threats.append(threat)
                    threat_names.add(threat['name'])
            
            all_errors.extend(result.validation_errors)
        
        # Calculate combined metadata
        total_processing_time = sum(result.processing_time_ms for result in results)
        combined_confidence = sum(result.confidence_score for result in results) / len(results)
        
        combined_metadata = {
            'merged_from_files': [result.file_info['filename'] for result in results],
            'parsers_used': list(set(result.parser_used for result in results)),
            'total_processing_time_ms': total_processing_time,
            'merge_timestamp': datetime.now().isoformat(),
            'individual_results': [
                {
                    'filename': result.file_info['filename'],
                    'parser': result.parser_used,
                    'assets_count': len(result.assets),
                    'threats_count': len(result.threats),
                    'confidence': result.confidence_score
                }
                for result in results
            ]
        }
        
        # Use metadata from first result as base
        first_result = results[0]
        
        return UnifiedParseResult(
            assets=all_assets,
            threats=all_threats,
            metadata=combined_metadata,
            validation_errors=list(set(all_errors)),  # Remove duplicates
            confidence_score=combined_confidence,
            parser_used='merged',
            processing_time_ms=total_processing_time,
            file_info={'filename': 'merged_results', 'type': 'merged'}
        )


# Utility functions
def process_file(file_path: Union[str, Path], **kwargs) -> UnifiedParseResult:
    """Convenience function to process a single file."""
    processor = FileProcessor()
    return processor.process_file(file_path, **kwargs)


def process_files(file_paths: List[Union[str, Path]], **kwargs) -> Union[UnifiedParseResult, List[UnifiedParseResult]]:
    """Convenience function to process multiple files."""
    processor = FileProcessor()
    return processor.process_multiple_files(file_paths, **kwargs)


def validate_file(file_path: Union[str, Path]) -> tuple[bool, List[str], str]:
    """Convenience function to validate a file."""
    processor = FileProcessor()
    return processor.validate_file(file_path)


def get_supported_formats() -> Dict[str, List[str]]:
    """Get list of supported file formats."""
    processor = FileProcessor()
    return processor.get_supported_formats()