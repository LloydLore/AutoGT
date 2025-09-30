"""CSV file parser with validation per FR-002.

Implements automotive TARA data parsing from CSV files with flexible
column mapping and validation against automotive domain requirements.
"""

import pandas as pd
import csv
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from dataclasses import dataclass
from io import StringIO

from ..models.enums import AssetType, CriticalityLevel
from ..core.exceptions import FileParsingError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class CsvParseResult:
    """Result of CSV file parsing with validation metadata."""
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[str]
    confidence_score: float
    detected_format: Dict[str, Any]


class CsvParser:
    """CSV file parser for automotive TARA analysis data.
    
    Handles various CSV dialects, encoding detection, and flexible column
    mapping for automotive cybersecurity data structures.
    """
    
    def __init__(self):
        """Initialize CSV parser with configuration."""
        self.supported_extensions = {'.csv', '.tsv'}
        self.max_file_size_mb = 10
        
        # Common CSV dialects to try
        self.csv_dialects = [
            {'delimiter': ',', 'quotechar': '"'},
            {'delimiter': ';', 'quotechar': '"'},
            {'delimiter': '\t', 'quotechar': '"'},
            {'delimiter': '|', 'quotechar': '"'},
            {'delimiter': ',', 'quotechar': "'"}
        ]
        
        # Common encoding options
        self.encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        # Column mapping patterns (similar to Excel parser)
        self.asset_column_patterns = {
            'name': ['name', 'asset_name', 'asset name', 'component', 'component_name', 'id'],
            'type': ['type', 'asset_type', 'asset type', 'category', 'component_type', 'kind'],
            'criticality': ['criticality', 'critical', 'importance', 'priority', 'risk_level', 'severity'],
            'interfaces': ['interfaces', 'connections', 'protocols', 'communication', 'links'],
            'description': ['description', 'desc', 'details', 'notes', 'purpose', 'function'],
            'location': ['location', 'position', 'placement', 'zone', 'area'],
            'manufacturer': ['manufacturer', 'vendor', 'supplier', 'oem', 'provider']
        }
        
        self.threat_column_patterns = {
            'name': ['threat', 'threat_name', 'attack', 'scenario', 'threat_scenario'],
            'category': ['category', 'type', 'classification', 'stride', 'threat_type'],
            'description': ['description', 'details', 'scenario_description', 'attack_description'],
            'likelihood': ['likelihood', 'probability', 'frequency', 'chance'],
            'impact': ['impact', 'severity', 'consequence', 'damage'],
            'asset': ['asset', 'target', 'affected_asset', 'component', 'target_asset']
        }
        
    def parse_file(self, file_path: Path) -> CsvParseResult:
        """Parse CSV file and extract TARA-relevant data.
        
        Args:
            file_path: Path to CSV file to parse
            
        Returns:
            CsvParseResult with parsed data and validation results
            
        Raises:
            FileParsingError: If file cannot be parsed or is invalid
            ValidationError: If data validation fails
        """
        if not self._validate_file(file_path):
            raise FileParsingError(f"File validation failed for {file_path}")
        
        try:
            # Detect CSV format and encoding
            detected_format = self._detect_csv_format(file_path)
            
            # Read CSV with detected format
            df = self._read_csv_with_format(file_path, detected_format)
            
            # Analyze column structure
            column_analysis = self._analyze_columns(df)
            
            # Parse data based on detected structure
            if column_analysis['data_type'] == 'assets':
                assets = self._parse_assets_from_csv(df)
                threats = []
            elif column_analysis['data_type'] == 'threats':
                assets = []
                threats = self._parse_threats_from_csv(df)
            else:
                # Mixed or unknown format - try to parse both
                assets = self._parse_assets_from_csv(df)
                threats = self._parse_threats_from_csv(df)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, df, detected_format, column_analysis)
            
            # Validate parsed data
            validation_errors = self._validate_parsed_data(assets, threats, df)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                assets, threats, validation_errors, column_analysis
            )
            
            return CsvParseResult(
                assets=assets,
                threats=threats,
                metadata=metadata,
                validation_errors=validation_errors,
                confidence_score=confidence_score,
                detected_format=detected_format
            )
            
        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {str(e)}")
            raise FileParsingError(f"CSV parsing failed: {str(e)}")
    
    def _validate_file(self, file_path: Path) -> bool:
        """Validate file before parsing."""
        # Check file exists
        if not file_path.exists():
            raise FileParsingError(f"File not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() not in self.supported_extensions:
            raise FileParsingError(f"Unsupported file extension: {file_path.suffix}")
        
        # Check file size (10MB limit per FR-019)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise FileParsingError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        return True
    
    def _detect_csv_format(self, file_path: Path) -> Dict[str, Any]:
        """Detect CSV format including delimiter, encoding, and structure."""
        detected = {
            'delimiter': ',',
            'quotechar': '"',
            'encoding': 'utf-8',
            'has_header': True,
            'line_terminator': '\n'
        }
        
        # Try different encodings to find one that works
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    sample = f.read(8192)  # Read first 8KB for analysis
                
                detected['encoding'] = encoding
                
                # Use csv.Sniffer to detect delimiter and quote character
                try:
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample, delimiters=',;\t|')
                    detected['delimiter'] = dialect.delimiter
                    detected['quotechar'] = dialect.quotechar
                    detected['line_terminator'] = dialect.lineterminator
                except csv.Error:
                    # Fallback to manual detection
                    detected.update(self._manual_format_detection(sample))
                
                # Detect if first line is header
                detected['has_header'] = self._detect_header(sample, detected['delimiter'])
                
                return detected
                
            except UnicodeDecodeError:
                continue
        
        # If no encoding worked, use utf-8 with error handling
        detected['encoding'] = 'utf-8'
        return detected
    
    def _manual_format_detection(self, sample: str) -> Dict[str, str]:
        """Manually detect CSV format when csv.Sniffer fails."""
        lines = sample.split('\n')[:5]  # Check first 5 lines
        
        delimiter_counts = {}
        for delimiter in [',', ';', '\t', '|']:
            counts = [line.count(delimiter) for line in lines if line.strip()]
            if counts and all(c == counts[0] and c > 0 for c in counts):
                delimiter_counts[delimiter] = counts[0]
        
        # Choose delimiter with most consistent count
        if delimiter_counts:
            delimiter = max(delimiter_counts.items(), key=lambda x: x[1])[0]
        else:
            delimiter = ','
        
        # Detect quote character
        quotechar = '"'
        if "'" in sample and sample.count("'") > sample.count('"'):
            quotechar = "'"
        
        return {
            'delimiter': delimiter,
            'quotechar': quotechar
        }
    
    def _detect_header(self, sample: str, delimiter: str) -> bool:
        """Detect if first line contains column headers."""
        lines = [line for line in sample.split('\n') if line.strip()]
        if len(lines) < 2:
            return True  # Assume header if too few lines
        
        first_line = lines[0].split(delimiter)
        second_line = lines[1].split(delimiter)
        
        # Check if first line contains text while second contains more numeric data
        first_numeric = sum(1 for cell in first_line if self._is_numeric(cell.strip('"\'').strip()))
        second_numeric = sum(1 for cell in second_line if self._is_numeric(cell.strip('"\'').strip()))
        
        # If second line has more numeric values, first line is likely header
        return first_numeric < second_numeric
    
    def _is_numeric(self, value: str) -> bool:
        """Check if string represents a numeric value."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _read_csv_with_format(self, file_path: Path, format_info: Dict[str, Any]) -> pd.DataFrame:
        """Read CSV file using detected format parameters."""
        try:
            df = pd.read_csv(
                file_path,
                delimiter=format_info['delimiter'],
                quotechar=format_info['quotechar'],
                encoding=format_info['encoding'],
                header=0 if format_info['has_header'] else None,
                skipinitialspace=True,
                na_values=['', 'NULL', 'null', 'N/A', 'n/a', '#N/A'],
                keep_default_na=True
            )
            
            # If no header was detected, create generic column names
            if not format_info['has_header']:
                df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
            
            return df
            
        except Exception as e:
            # Fallback to basic CSV reading
            logger.warning(f"Advanced CSV parsing failed, using basic method: {str(e)}")
            return pd.read_csv(file_path, encoding=format_info['encoding'])
    
    def _analyze_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze CSV columns to determine data type and structure."""
        columns_lower = [str(col).lower().strip() for col in df.columns]
        
        analysis = {
            'data_type': 'unknown',
            'asset_score': 0,
            'threat_score': 0,
            'column_count': len(df.columns),
            'row_count': len(df),
            'matched_columns': {}
        }
        
        # Score columns for asset patterns
        for field, patterns in self.asset_column_patterns.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    analysis['asset_score'] += 1
                    analysis['matched_columns'][field] = pattern
                    break
        
        # Score columns for threat patterns
        for field, patterns in self.threat_column_patterns.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    analysis['threat_score'] += 1
                    break
        
        # Determine primary data type
        if analysis['asset_score'] >= 2 and analysis['asset_score'] > analysis['threat_score']:
            analysis['data_type'] = 'assets'
        elif analysis['threat_score'] >= 2 and analysis['threat_score'] > analysis['asset_score']:
            analysis['data_type'] = 'threats'
        elif analysis['asset_score'] >= 1 and analysis['threat_score'] >= 1:
            analysis['data_type'] = 'mixed'
        
        return analysis
    
    def _parse_assets_from_csv(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse asset data from CSV DataFrame."""
        assets = []
        
        # Create column mapping
        column_mapping = self._create_column_mapping(df, self.asset_column_patterns)
        
        # Parse each row
        for idx, row in df.iterrows():
            try:
                asset = self._parse_asset_row(row, column_mapping, idx)
                if asset:
                    assets.append(asset)
            except Exception as e:
                logger.warning(f"Failed to parse asset row {idx}: {str(e)}")
                continue
        
        return assets
    
    def _parse_threats_from_csv(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse threat data from CSV DataFrame."""
        threats = []
        
        # Create column mapping
        column_mapping = self._create_column_mapping(df, self.threat_column_patterns)
        
        # Only proceed if we have threat-related columns
        if not column_mapping:
            return threats
        
        # Parse each row
        for idx, row in df.iterrows():
            try:
                threat = self._parse_threat_row(row, column_mapping, idx)
                if threat:
                    threats.append(threat)
            except Exception as e:
                logger.warning(f"Failed to parse threat row {idx}: {str(e)}")
                continue
        
        return threats
    
    def _create_column_mapping(self, df: pd.DataFrame,
                              pattern_dict: Dict[str, List[str]]) -> Dict[str, str]:
        """Create mapping from field names to actual column names."""
        columns_lower = {str(col).lower().strip(): str(col) for col in df.columns}
        mapping = {}
        
        for field, patterns in pattern_dict.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    mapping[field] = columns_lower[pattern.lower()]
                    break
        
        return mapping
    
    def _parse_asset_row(self, row: pd.Series, column_mapping: Dict[str, str],
                        row_idx: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row as asset data."""
        # Skip empty rows
        if row.isna().all():
            return None
        
        # Get required fields
        name = self._get_field_value(row, column_mapping, 'name')
        asset_type = self._get_field_value(row, column_mapping, 'type')
        
        if not name or not asset_type:
            return None
        
        # Get optional fields
        criticality = self._get_field_value(row, column_mapping, 'criticality') or 'MEDIUM'
        interfaces = self._get_field_value(row, column_mapping, 'interfaces') or ''
        description = self._get_field_value(row, column_mapping, 'description')
        location = self._get_field_value(row, column_mapping, 'location')
        manufacturer = self._get_field_value(row, column_mapping, 'manufacturer')
        
        return {
            'name': str(name).strip(),
            'asset_type': str(asset_type).strip(),
            'criticality': self._normalize_criticality(criticality),
            'interfaces': self._parse_interfaces(interfaces),
            'description': str(description).strip() if description else None,
            'location': str(location).strip() if location else None,
            'manufacturer': str(manufacturer).strip() if manufacturer else None,
            'source_row': row_idx + 1  # 1-based for user reference
        }
    
    def _parse_threat_row(self, row: pd.Series, column_mapping: Dict[str, str],
                         row_idx: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row as threat data."""
        if row.isna().all():
            return None
        
        name = self._get_field_value(row, column_mapping, 'name')
        if not name:
            return None
        
        return {
            'name': str(name).strip(),
            'category': self._get_field_value(row, column_mapping, 'category'),
            'description': self._get_field_value(row, column_mapping, 'description'),
            'likelihood': self._get_field_value(row, column_mapping, 'likelihood'),
            'impact': self._get_field_value(row, column_mapping, 'impact'),
            'target_asset': self._get_field_value(row, column_mapping, 'asset'),
            'source_row': row_idx + 1
        }
    
    def _get_field_value(self, row: pd.Series, column_mapping: Dict[str, str],
                        field: str) -> Optional[str]:
        """Get field value from row using column mapping."""
        column_name = column_mapping.get(field)
        if column_name and column_name in row.index:
            value = row[column_name]
            if pd.isna(value):
                return None
            return str(value).strip() if value else None
        return None
    
    def _parse_interfaces(self, interfaces_str: str) -> List[str]:
        """Parse interfaces string into list."""
        if not interfaces_str:
            return []
        
        # Split by common separators
        separators = [',', ';', '|', '\n', '/', '\\']
        interfaces = [interfaces_str]
        
        for sep in separators:
            new_interfaces = []
            for interface in interfaces:
                new_interfaces.extend([i.strip() for i in str(interface).split(sep)])
            interfaces = new_interfaces
        
        # Filter and normalize
        return [i.upper() for i in interfaces if i and i.strip()]
    
    def _normalize_criticality(self, criticality: str) -> str:
        """Normalize criticality value to standard levels."""
        if not criticality:
            return 'MEDIUM'
        
        criticality_lower = str(criticality).lower().strip()
        
        mapping = {
            'low': 'LOW', 'l': 'LOW', 'minor': 'LOW', '1': 'LOW',
            'medium': 'MEDIUM', 'med': 'MEDIUM', 'm': 'MEDIUM', 'moderate': 'MEDIUM', '2': 'MEDIUM',
            'high': 'HIGH', 'h': 'HIGH', 'major': 'HIGH', '3': 'HIGH',
            'critical': 'CRITICAL', 'crit': 'CRITICAL', 'severe': 'CRITICAL', '4': 'CRITICAL'
        }
        
        return mapping.get(criticality_lower, 'MEDIUM')
    
    def _extract_metadata(self, file_path: Path, df: pd.DataFrame,
                         format_info: Dict[str, Any], column_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract file and parsing metadata."""
        return {
            'filename': file_path.name,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'row_count': len(df),
            'column_count': len(df.columns),
            'detected_delimiter': format_info['delimiter'],
            'detected_encoding': format_info['encoding'],
            'has_header': format_info['has_header'],
            'data_type': column_analysis['data_type'],
            'asset_score': column_analysis['asset_score'],
            'threat_score': column_analysis['threat_score'],
            'parser_version': '1.0.0',
            'parsing_timestamp': pd.Timestamp.now().isoformat()
        }
    
    def _validate_parsed_data(self, assets: List[Dict[str, Any]],
                             threats: List[Dict[str, Any]], df: pd.DataFrame) -> List[str]:
        """Validate parsed data against business rules."""
        errors = []
        
        # Check for minimum data requirements
        if not assets and not threats:
            errors.append("No valid assets or threats found in CSV")
        
        # Validate asset data
        asset_names = set()
        for asset in assets:
            # Check for duplicates
            if asset['name'] in asset_names:
                errors.append(f"Duplicate asset name: {asset['name']} (row {asset.get('source_row', '?')})")
            asset_names.add(asset['name'])
            
            # Validate required fields
            if not asset['asset_type']:
                errors.append(f"Missing asset type for {asset['name']} (row {asset.get('source_row', '?')})")
        
        # Check CSV structure quality
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > len(df) * 0.3:  # More than 30% empty rows
            errors.append(f"Too many empty rows: {empty_rows}/{len(df)} ({empty_rows/len(df)*100:.1f}%)")
        
        return errors
    
    def _calculate_confidence_score(self, assets: List[Dict[str, Any]],
                                   threats: List[Dict[str, Any]],
                                   validation_errors: List[str],
                                   column_analysis: Dict[str, Any]) -> float:
        """Calculate parsing confidence score."""
        score = 1.0
        
        # Penalize validation errors
        if validation_errors:
            score -= len(validation_errors) * 0.1
        
        # Reward data completeness
        total_data = len(assets) + len(threats)
        if total_data > 0:
            # Reward having both name and type columns identified
            if column_analysis['asset_score'] >= 2 or column_analysis['threat_score'] >= 2:
                score *= 1.1
            
            # Penalize if no clear data type identified
            if column_analysis['data_type'] == 'unknown':
                score *= 0.7
        else:
            score *= 0.2  # Very low score if no data parsed
        
        return max(0.0, min(1.0, score))


# Utility functions
def parse_csv_file(file_path: Path) -> CsvParseResult:
    """Convenience function to parse CSV file."""
    parser = CsvParser()
    return parser.parse_file(file_path)


def detect_csv_format(file_path: Path) -> Dict[str, Any]:
    """Detect CSV format without full parsing."""
    parser = CsvParser()
    return parser._detect_csv_format(file_path)


def validate_csv_format(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate if file can be parsed as CSV without full parsing."""
    try:
        parser = CsvParser()
        parser._validate_file(file_path)
        return True, []
    except (FileParsingError, ValidationError) as e:
        return False, [str(e)]