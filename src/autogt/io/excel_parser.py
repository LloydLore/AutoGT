"""Excel file parser with pandas integration for .xlsx/.xls files.

Implements FR-001 file input validation and parsing for Excel formats
with automotive TARA data structure detection and validation.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

from ..models.enums import AssetType, CriticalityLevel
from ..core.exceptions import FileParsingError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class ParsedAssetData:
    """Structured representation of parsed asset data."""
    name: str
    asset_type: str
    criticality: str
    interfaces: List[str]
    description: Optional[str] = None
    security_properties: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None


@dataclass
class ExcelParseResult:
    """Result of Excel file parsing with validation metadata."""
    assets: List[ParsedAssetData]
    threats: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[str]
    confidence_score: float


class ExcelParser:
    """Excel file parser for automotive TARA analysis data.
    
    Supports multiple sheet formats and automotive-specific data structures
    with intelligent column mapping and data validation.
    """
    
    def __init__(self):
        """Initialize Excel parser with column mapping configurations."""
        self.supported_extensions = {'.xlsx', '.xls'}
        
        # Common column name mappings for flexible parsing
        self.asset_column_mappings = {
            'name': ['name', 'asset_name', 'asset name', 'component', 'component_name'],
            'type': ['type', 'asset_type', 'asset type', 'category', 'component_type'],
            'criticality': ['criticality', 'critical', 'importance', 'priority', 'risk_level'],
            'interfaces': ['interfaces', 'connections', 'protocols', 'communication'],
            'description': ['description', 'desc', 'details', 'notes', 'purpose'],
            'location': ['location', 'position', 'placement', 'zone'],
            'manufacturer': ['manufacturer', 'vendor', 'supplier', 'oem']
        }
        
        self.threat_column_mappings = {
            'name': ['threat', 'threat_name', 'attack', 'scenario'],
            'category': ['category', 'type', 'classification', 'stride'],
            'description': ['description', 'details', 'scenario_description'],
            'likelihood': ['likelihood', 'probability', 'frequency'],
            'impact': ['impact', 'severity', 'consequence'],
            'asset': ['asset', 'target', 'affected_asset', 'component']
        }
        
        # Validation rules
        self.max_file_size_mb = 10
        self.required_asset_columns = ['name', 'type']
        
    def parse_file(self, file_path: Path) -> ExcelParseResult:
        """Parse Excel file and extract TARA-relevant data.
        
        Args:
            file_path: Path to Excel file to parse
            
        Returns:
            ExcelParseResult with parsed data and validation results
            
        Raises:
            FileParsingError: If file cannot be parsed or is invalid
            ValidationError: If data validation fails
        """
        if not self._validate_file(file_path):
            raise FileParsingError(f"File validation failed for {file_path}")
            
        try:
            # Read Excel file with multiple sheets
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            # Analyze sheet structure and content
            sheet_analysis = self._analyze_sheets(excel_data)
            
            # Parse assets from identified sheets
            assets = self._parse_assets(excel_data, sheet_analysis)
            
            # Parse threats if available
            threats = self._parse_threats(excel_data, sheet_analysis)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, excel_data, sheet_analysis)
            
            # Validate parsed data
            validation_errors = self._validate_parsed_data(assets, threats)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                assets, threats, validation_errors, sheet_analysis
            )
            
            return ExcelParseResult(
                assets=assets,
                threats=threats,
                metadata=metadata,
                validation_errors=validation_errors,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Excel file {file_path}: {str(e)}")
            raise FileParsingError(f"Excel parsing failed: {str(e)}")
    
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
    
    def _analyze_sheets(self, excel_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze Excel sheets to identify data structure and content types."""
        sheet_analysis = {
            'asset_sheets': [],
            'threat_sheets': [],
            'metadata_sheets': [],
            'total_sheets': len(excel_data),
            'total_rows': 0
        }
        
        for sheet_name, df in excel_data.items():
            sheet_info = {
                'name': sheet_name,
                'rows': len(df),
                'columns': list(df.columns),
                'type': 'unknown'
            }
            
            sheet_analysis['total_rows'] += len(df)
            
            # Identify sheet type based on column names
            if self._is_asset_sheet(df):
                sheet_info['type'] = 'assets'
                sheet_analysis['asset_sheets'].append(sheet_info)
            elif self._is_threat_sheet(df):
                sheet_info['type'] = 'threats'
                sheet_analysis['threat_sheets'].append(sheet_info)
            else:
                sheet_info['type'] = 'metadata'
                sheet_analysis['metadata_sheets'].append(sheet_info)
        
        return sheet_analysis
    
    def _is_asset_sheet(self, df: pd.DataFrame) -> bool:
        """Determine if DataFrame contains asset data."""
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Look for asset-related column patterns
        asset_indicators = 0
        for field, patterns in self.asset_column_mappings.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    asset_indicators += 1
                    break
        
        # Require at least 2 asset-related columns to classify as asset sheet
        return asset_indicators >= 2
    
    def _is_threat_sheet(self, df: pd.DataFrame) -> bool:
        """Determine if DataFrame contains threat data."""
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Look for threat-related column patterns
        threat_indicators = 0
        for field, patterns in self.threat_column_mappings.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    threat_indicators += 1
                    break
        
        return threat_indicators >= 2
    
    def _parse_assets(self, excel_data: Dict[str, pd.DataFrame], 
                     sheet_analysis: Dict[str, Any]) -> List[ParsedAssetData]:
        """Parse asset data from identified asset sheets."""
        assets = []
        
        for sheet_info in sheet_analysis['asset_sheets']:
            df = excel_data[sheet_info['name']]
            
            # Map columns to standardized field names
            column_mapping = self._create_column_mapping(df, self.asset_column_mappings)
            
            # Parse each row as an asset
            for _, row in df.iterrows():
                try:
                    asset = self._parse_asset_row(row, column_mapping)
                    if asset:
                        assets.append(asset)
                except Exception as e:
                    logger.warning(f"Failed to parse asset row: {str(e)}")
                    continue
        
        return assets
    
    def _parse_threats(self, excel_data: Dict[str, pd.DataFrame],
                      sheet_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse threat data from identified threat sheets."""
        threats = []
        
        for sheet_info in sheet_analysis['threat_sheets']:
            df = excel_data[sheet_info['name']]
            
            # Map columns to standardized field names
            column_mapping = self._create_column_mapping(df, self.threat_column_mappings)
            
            # Parse each row as a threat
            for _, row in df.iterrows():
                try:
                    threat = self._parse_threat_row(row, column_mapping)
                    if threat:
                        threats.append(threat)
                except Exception as e:
                    logger.warning(f"Failed to parse threat row: {str(e)}")
                    continue
        
        return threats
    
    def _create_column_mapping(self, df: pd.DataFrame, 
                              field_mappings: Dict[str, List[str]]) -> Dict[str, str]:
        """Create mapping from standardized field names to actual column names."""
        columns_lower = {col.lower().strip(): col for col in df.columns}
        mapping = {}
        
        for field, patterns in field_mappings.items():
            for pattern in patterns:
                if pattern.lower() in columns_lower:
                    mapping[field] = columns_lower[pattern.lower()]
                    break
        
        return mapping
    
    def _parse_asset_row(self, row: pd.Series, 
                        column_mapping: Dict[str, str]) -> Optional[ParsedAssetData]:
        """Parse a single row as asset data."""
        # Skip empty rows
        if row.isna().all():
            return None
        
        # Extract required fields
        name = self._get_field_value(row, column_mapping, 'name')
        asset_type = self._get_field_value(row, column_mapping, 'type')
        
        if not name or not asset_type:
            return None
        
        # Extract optional fields
        criticality = self._get_field_value(row, column_mapping, 'criticality') or 'MEDIUM'
        interfaces_str = self._get_field_value(row, column_mapping, 'interfaces') or ''
        description = self._get_field_value(row, column_mapping, 'description')
        location = self._get_field_value(row, column_mapping, 'location')
        manufacturer = self._get_field_value(row, column_mapping, 'manufacturer')
        
        # Parse interfaces list
        interfaces = self._parse_interfaces(interfaces_str)
        
        # Normalize criticality
        criticality = self._normalize_criticality(criticality)
        
        return ParsedAssetData(
            name=str(name).strip(),
            asset_type=str(asset_type).strip(),
            criticality=criticality,
            interfaces=interfaces,
            description=str(description).strip() if description else None,
            location=str(location).strip() if location else None,
            manufacturer=str(manufacturer).strip() if manufacturer else None
        )
    
    def _parse_threat_row(self, row: pd.Series,
                         column_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single row as threat data."""
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
            'target_asset': self._get_field_value(row, column_mapping, 'asset')
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
        """Parse interfaces string into list of interface names."""
        if not interfaces_str:
            return []
        
        # Split by common separators
        separators = [',', ';', '|', '\n']
        interfaces = [interfaces_str]
        
        for sep in separators:
            new_interfaces = []
            for interface in interfaces:
                new_interfaces.extend([i.strip() for i in interface.split(sep)])
            interfaces = new_interfaces
        
        # Filter out empty strings and normalize
        return [i.upper() for i in interfaces if i and i.strip()]
    
    def _normalize_criticality(self, criticality: str) -> str:
        """Normalize criticality value to standard levels."""
        if not criticality:
            return 'MEDIUM'
        
        criticality_lower = criticality.lower().strip()
        
        # Map common variations to standard levels
        mapping = {
            'low': 'LOW',
            'l': 'LOW',
            'minor': 'LOW',
            'medium': 'MEDIUM',
            'med': 'MEDIUM',
            'm': 'MEDIUM',
            'moderate': 'MEDIUM',
            'high': 'HIGH',
            'h': 'HIGH',
            'major': 'HIGH',
            'critical': 'CRITICAL',
            'crit': 'CRITICAL',
            'severe': 'CRITICAL'
        }
        
        return mapping.get(criticality_lower, 'MEDIUM')
    
    def _extract_metadata(self, file_path: Path, excel_data: Dict[str, pd.DataFrame],
                         sheet_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract file and parsing metadata."""
        return {
            'filename': file_path.name,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'sheet_count': sheet_analysis['total_sheets'],
            'total_rows': sheet_analysis['total_rows'],
            'asset_sheets': len(sheet_analysis['asset_sheets']),
            'threat_sheets': len(sheet_analysis['threat_sheets']),
            'parser_version': '1.0.0',
            'parsing_timestamp': pd.Timestamp.now().isoformat()
        }
    
    def _validate_parsed_data(self, assets: List[ParsedAssetData],
                             threats: List[Dict[str, Any]]) -> List[str]:
        """Validate parsed data against business rules."""
        errors = []
        
        # Validate assets
        if not assets:
            errors.append("No assets found in file")
        
        asset_names = set()
        for asset in assets:
            # Check for duplicate names
            if asset.name in asset_names:
                errors.append(f"Duplicate asset name: {asset.name}")
            asset_names.add(asset.name)
            
            # Validate asset type
            if not self._is_valid_asset_type(asset.asset_type):
                errors.append(f"Invalid asset type for {asset.name}: {asset.asset_type}")
            
            # Validate criticality
            if asset.criticality not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                errors.append(f"Invalid criticality for {asset.name}: {asset.criticality}")
        
        return errors
    
    def _is_valid_asset_type(self, asset_type: str) -> bool:
        """Check if asset type is valid."""
        # Common automotive asset types
        valid_types = {
            'ecu', 'electronic control unit', 'gateway', 'sensor', 'actuator',
            'communication module', 'infotainment', 'telematics', 'camera',
            'radar', 'lidar', 'display', 'hmi', 'battery management system',
            'charging system', 'network', 'bus', 'can', 'ethernet', 'wireless'
        }
        
        return asset_type.lower().strip() in valid_types
    
    def _calculate_confidence_score(self, assets: List[ParsedAssetData],
                                   threats: List[Dict[str, Any]],
                                   validation_errors: List[str],
                                   sheet_analysis: Dict[str, Any]) -> float:
        """Calculate parsing confidence score."""
        score = 1.0
        
        # Penalize validation errors
        if validation_errors:
            score -= len(validation_errors) * 0.1
        
        # Reward asset completeness
        if assets:
            complete_assets = sum(1 for a in assets if a.description and a.interfaces)
            completeness_ratio = complete_assets / len(assets)
            score *= (0.7 + 0.3 * completeness_ratio)
        else:
            score *= 0.3  # Low score if no assets
        
        # Reward structured data (multiple sheets)
        if sheet_analysis['asset_sheets']:
            score *= 1.1
        if sheet_analysis['threat_sheets']:
            score *= 1.1
        
        return max(0.0, min(1.0, score))


# Utility functions for external use
def parse_excel_file(file_path: Path) -> ExcelParseResult:
    """Convenience function to parse Excel file."""
    parser = ExcelParser()
    return parser.parse_file(file_path)


def validate_excel_format(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate if file can be parsed as Excel without full parsing."""
    try:
        parser = ExcelParser()
        parser._validate_file(file_path)
        return True, []
    except (FileParsingError, ValidationError) as e:
        return False, [str(e)]