"""JSON file parser with schema validation per FR-003.

Implements automotive TARA data parsing from JSON files with flexible
structure detection and validation against automotive domain requirements.
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass

from ..models.enums import AssetType, CriticalityLevel
from ..core.exceptions import FileParsingError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class JsonParseResult:
    """Result of JSON file parsing with validation metadata."""
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[str]
    confidence_score: float
    detected_schema: Dict[str, Any]


class JsonParser:
    """JSON file parser for automotive TARA analysis data.
    
    Handles various JSON structures with flexible schema detection
    and validation for automotive cybersecurity data.
    """
    
    def __init__(self):
        """Initialize JSON parser with configuration."""
        self.supported_extensions = {'.json', '.jsonl'}
        self.max_file_size_mb = 10
        
        # Expected JSON schema patterns for TARA data
        self.tara_schema = {
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "asset_type": {"type": "string"},
                            "criticality": {"type": "string"},
                            "interfaces": {"type": "array", "items": {"type": "string"}},
                            "description": {"type": "string"},
                            "location": {"type": "string"},
                            "manufacturer": {"type": "string"}
                        },
                        "required": ["name", "asset_type"]
                    }
                },
                "threats": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "category": {"type": "string"},
                            "description": {"type": "string"},
                            "likelihood": {"type": ["string", "number"]},
                            "impact": {"type": ["string", "number"]},
                            "target_asset": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                },
                "metadata": {"type": "object"}
            }
        }
        
        # Alternative schema patterns to recognize
        self.schema_variants = [
            # Flat array of assets
            {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"}
                    },
                    "required": ["name"]
                }
            },
            # Simple object with mixed data
            {
                "type": "object",
                "additionalProperties": True
            }
        ]
        
        # Field name mappings for flexible parsing
        self.field_mappings = {
            # Asset fields
            'asset_name': ['name', 'asset_name', 'component', 'component_name', 'id'],
            'asset_type': ['type', 'asset_type', 'category', 'component_type', 'kind'],
            'criticality': ['criticality', 'critical', 'importance', 'priority', 'risk_level'],
            'interfaces': ['interfaces', 'connections', 'protocols', 'communication'],
            'description': ['description', 'desc', 'details', 'notes', 'purpose'],
            'location': ['location', 'position', 'placement', 'zone', 'area'],
            'manufacturer': ['manufacturer', 'vendor', 'supplier', 'oem', 'provider'],
            
            # Threat fields
            'threat_name': ['name', 'threat', 'threat_name', 'attack', 'scenario'],
            'category': ['category', 'type', 'classification', 'stride', 'threat_type'],
            'likelihood': ['likelihood', 'probability', 'frequency', 'chance'],
            'impact': ['impact', 'severity', 'consequence', 'damage'],
            'target_asset': ['asset', 'target', 'affected_asset', 'component']
        }
        
    def parse_file(self, file_path: Path) -> JsonParseResult:
        """Parse JSON file and extract TARA-relevant data.
        
        Args:
            file_path: Path to JSON file to parse
            
        Returns:
            JsonParseResult with parsed data and validation results
            
        Raises:
            FileParsingError: If file cannot be parsed or is invalid
            ValidationError: If data validation fails
        """
        if not self._validate_file(file_path):
            raise FileParsingError(f"File validation failed for {file_path}")
        
        try:
            # Load JSON data
            json_data = self._load_json_file(file_path)
            
            # Detect JSON structure and schema
            detected_schema = self._detect_schema(json_data)
            
            # Parse data based on detected structure
            assets, threats = self._parse_data_by_schema(json_data, detected_schema)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, json_data, detected_schema)
            
            # Validate parsed data
            validation_errors = self._validate_parsed_data(assets, threats, json_data)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                assets, threats, validation_errors, detected_schema, json_data
            )
            
            return JsonParseResult(
                assets=assets,
                threats=threats,
                metadata=metadata,
                validation_errors=validation_errors,
                confidence_score=confidence_score,
                detected_schema=detected_schema
            )
            
        except Exception as e:
            logger.error(f"Failed to parse JSON file {file_path}: {str(e)}")
            raise FileParsingError(f"JSON parsing failed: {str(e)}")
    
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
    
    def _load_json_file(self, file_path: Path) -> Union[Dict, List]:
        """Load JSON data from file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.jsonl':
                    # Handle JSON Lines format
                    return [json.loads(line) for line in f if line.strip()]
                else:
                    return json.load(f)
                    
        except json.JSONDecodeError as e:
            raise FileParsingError(f"Invalid JSON format: {str(e)}")
        except UnicodeDecodeError as e:
            # Try alternative encodings
            for encoding in ['latin-1', 'cp1252', 'utf-8-sig']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return json.load(f)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            raise FileParsingError(f"Cannot decode file with any supported encoding: {str(e)}")
    
    def _detect_schema(self, data: Union[Dict, List]) -> Dict[str, Any]:
        """Detect JSON schema and structure type."""
        schema_info = {
            'type': 'unknown',
            'structure': None,
            'has_assets': False,
            'has_threats': False,
            'confidence': 0.0
        }
        
        if isinstance(data, dict):
            schema_info['structure'] = 'object'
            
            # Check for TARA structure
            if 'assets' in data and isinstance(data['assets'], list):
                schema_info['has_assets'] = True
                schema_info['type'] = 'tara_format'
                
            if 'threats' in data and isinstance(data['threats'], list):
                schema_info['has_threats'] = True
                schema_info['type'] = 'tara_format'
            
            # Check if object contains asset-like or threat-like data
            if not schema_info['has_assets'] and not schema_info['has_threats']:
                if self._contains_asset_fields(data):
                    schema_info['type'] = 'single_asset'
                elif self._contains_threat_fields(data):
                    schema_info['type'] = 'single_threat'
                else:
                    schema_info['type'] = 'generic_object'
                    
        elif isinstance(data, list):
            schema_info['structure'] = 'array'
            
            if data:  # Non-empty array
                first_item = data[0]
                if isinstance(first_item, dict):
                    if self._contains_asset_fields(first_item):
                        schema_info['type'] = 'asset_array'
                        schema_info['has_assets'] = True
                    elif self._contains_threat_fields(first_item):
                        schema_info['type'] = 'threat_array'
                        schema_info['has_threats'] = True
                    else:
                        schema_info['type'] = 'generic_array'
        
        # Calculate detection confidence
        schema_info['confidence'] = self._calculate_schema_confidence(data, schema_info)
        
        return schema_info
    
    def _contains_asset_fields(self, obj: Dict) -> bool:
        """Check if object contains asset-related fields."""
        if not isinstance(obj, dict):
            return False
        
        keys_lower = [key.lower() for key in obj.keys()]
        
        # Look for asset indicators
        asset_indicators = ['name', 'type', 'asset', 'component', 'criticality', 'interfaces']
        matches = sum(1 for indicator in asset_indicators if any(indicator in key for key in keys_lower))
        
        return matches >= 2  # Need at least 2 matching fields
    
    def _contains_threat_fields(self, obj: Dict) -> bool:
        """Check if object contains threat-related fields."""
        if not isinstance(obj, dict):
            return False
        
        keys_lower = [key.lower() for key in obj.keys()]
        
        # Look for threat indicators
        threat_indicators = ['threat', 'attack', 'scenario', 'likelihood', 'impact', 'stride']
        matches = sum(1 for indicator in threat_indicators if any(indicator in key for key in keys_lower))
        
        return matches >= 2
    
    def _parse_data_by_schema(self, data: Union[Dict, List], 
                             schema_info: Dict[str, Any]) -> tuple[List[Dict], List[Dict]]:
        """Parse data based on detected schema structure."""
        assets = []
        threats = []
        
        schema_type = schema_info['type']
        
        if schema_type == 'tara_format':
            # Standard TARA format with assets and threats arrays
            if isinstance(data, dict):
                if 'assets' in data and isinstance(data['assets'], list):
                    assets = [self._parse_asset_object(asset) for asset in data['assets']]
                    assets = [a for a in assets if a]  # Remove None results
                
                if 'threats' in data and isinstance(data['threats'], list):
                    threats = [self._parse_threat_object(threat) for threat in data['threats']]
                    threats = [t for t in threats if t]  # Remove None results
        
        elif schema_type == 'asset_array':
            # Array of asset objects
            if isinstance(data, list):
                assets = [self._parse_asset_object(item) for item in data]
                assets = [a for a in assets if a]
        
        elif schema_type == 'threat_array':
            # Array of threat objects
            if isinstance(data, list):
                threats = [self._parse_threat_object(item) for item in data]
                threats = [t for t in threats if t]
        
        elif schema_type == 'single_asset':
            # Single asset object
            asset = self._parse_asset_object(data)
            if asset:
                assets = [asset]
        
        elif schema_type == 'single_threat':
            # Single threat object
            threat = self._parse_threat_object(data)
            if threat:
                threats = [threat]
        
        elif schema_type in ['generic_object', 'generic_array']:
            # Try to parse as both assets and threats
            if isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = data
            else:
                items = []
            
            for item in items:
                if isinstance(item, dict):
                    # Try as asset first
                    asset = self._parse_asset_object(item)
                    if asset:
                        assets.append(asset)
                    else:
                        # Try as threat
                        threat = self._parse_threat_object(item)
                        if threat:
                            threats.append(threat)
        
        return assets, threats
    
    def _parse_asset_object(self, obj: Dict) -> Optional[Dict[str, Any]]:
        """Parse a JSON object as an asset."""
        if not isinstance(obj, dict):
            return None
        
        # Get asset name (required)
        name = self._get_mapped_field(obj, self.field_mappings['asset_name'])
        if not name:
            return None
        
        # Get asset type (required)
        asset_type = self._get_mapped_field(obj, self.field_mappings['asset_type'])
        if not asset_type:
            return None
        
        # Get optional fields
        criticality = self._get_mapped_field(obj, self.field_mappings['criticality']) or 'MEDIUM'
        interfaces = self._get_mapped_field(obj, self.field_mappings['interfaces']) or []
        description = self._get_mapped_field(obj, self.field_mappings['description'])
        location = self._get_mapped_field(obj, self.field_mappings['location'])
        manufacturer = self._get_mapped_field(obj, self.field_mappings['manufacturer'])
        
        # Normalize interfaces
        if isinstance(interfaces, str):
            interfaces = [i.strip() for i in interfaces.split(',') if i.strip()]
        elif not isinstance(interfaces, list):
            interfaces = []
        
        return {
            'name': str(name).strip(),
            'asset_type': str(asset_type).strip(),
            'criticality': self._normalize_criticality(criticality),
            'interfaces': [str(i).upper() for i in interfaces],
            'description': str(description).strip() if description else None,
            'location': str(location).strip() if location else None,
            'manufacturer': str(manufacturer).strip() if manufacturer else None
        }
    
    def _parse_threat_object(self, obj: Dict) -> Optional[Dict[str, Any]]:
        """Parse a JSON object as a threat."""
        if not isinstance(obj, dict):
            return None
        
        # Get threat name (required)
        name = self._get_mapped_field(obj, self.field_mappings['threat_name'])
        if not name:
            return None
        
        return {
            'name': str(name).strip(),
            'category': self._get_mapped_field(obj, self.field_mappings['category']),
            'description': self._get_mapped_field(obj, self.field_mappings['description']),
            'likelihood': self._get_mapped_field(obj, self.field_mappings['likelihood']),
            'impact': self._get_mapped_field(obj, self.field_mappings['impact']),
            'target_asset': self._get_mapped_field(obj, self.field_mappings['target_asset'])
        }
    
    def _get_mapped_field(self, obj: Dict, field_names: List[str]) -> Any:
        """Get field value using flexible field name mapping."""
        # Direct key match first
        for field_name in field_names:
            if field_name in obj:
                return obj[field_name]
        
        # Case-insensitive match
        obj_keys_lower = {k.lower(): k for k in obj.keys()}
        for field_name in field_names:
            if field_name.lower() in obj_keys_lower:
                actual_key = obj_keys_lower[field_name.lower()]
                return obj[actual_key]
        
        return None
    
    def _normalize_criticality(self, criticality: Any) -> str:
        """Normalize criticality value to standard levels."""
        if not criticality:
            return 'MEDIUM'
        
        criticality_str = str(criticality).lower().strip()
        
        mapping = {
            'low': 'LOW', 'l': 'LOW', 'minor': 'LOW', '1': 'LOW',
            'medium': 'MEDIUM', 'med': 'MEDIUM', 'm': 'MEDIUM', 'moderate': 'MEDIUM', '2': 'MEDIUM',
            'high': 'HIGH', 'h': 'HIGH', 'major': 'HIGH', '3': 'HIGH',
            'critical': 'CRITICAL', 'crit': 'CRITICAL', 'severe': 'CRITICAL', '4': 'CRITICAL'
        }
        
        return mapping.get(criticality_str, 'MEDIUM')
    
    def _calculate_schema_confidence(self, data: Union[Dict, List], 
                                   schema_info: Dict[str, Any]) -> float:
        """Calculate confidence in schema detection."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for known patterns
        if schema_info['type'] == 'tara_format':
            confidence = 0.9
        elif schema_info['type'] in ['asset_array', 'threat_array']:
            confidence = 0.8
        elif schema_info['type'] in ['single_asset', 'single_threat']:
            confidence = 0.7
        
        # Boost if both assets and threats are present
        if schema_info['has_assets'] and schema_info['has_threats']:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_metadata(self, file_path: Path, data: Union[Dict, List],
                         schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract file and parsing metadata."""
        metadata = {
            'filename': file_path.name,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'detected_structure': schema_info['structure'],
            'detected_type': schema_info['type'],
            'schema_confidence': schema_info['confidence'],
            'has_assets': schema_info['has_assets'],
            'has_threats': schema_info['has_threats'],
            'parser_version': '1.0.0'
        }
        
        # Add data-specific metadata
        if isinstance(data, list):
            metadata['item_count'] = len(data)
        elif isinstance(data, dict):
            metadata['property_count'] = len(data)
            
            # Extract embedded metadata if present
            if 'metadata' in data and isinstance(data['metadata'], dict):
                metadata['embedded_metadata'] = data['metadata']
        
        return metadata
    
    def _validate_parsed_data(self, assets: List[Dict[str, Any]],
                             threats: List[Dict[str, Any]], 
                             original_data: Union[Dict, List]) -> List[str]:
        """Validate parsed data against business rules."""
        errors = []
        
        # Check for minimum data requirements
        if not assets and not threats:
            errors.append("No valid assets or threats found in JSON")
        
        # Validate asset data
        asset_names = set()
        for asset in assets:
            # Check for duplicates
            if asset['name'] in asset_names:
                errors.append(f"Duplicate asset name: {asset['name']}")
            asset_names.add(asset['name'])
            
            # Validate required fields
            if not asset['asset_type']:
                errors.append(f"Missing asset type for {asset['name']}")
        
        # Validate threat data
        threat_names = set()
        for threat in threats:
            if threat['name'] in threat_names:
                errors.append(f"Duplicate threat name: {threat['name']}")
            threat_names.add(threat['name'])
        
        # Validate JSON schema if possible
        try:
            if isinstance(original_data, dict) and ('assets' in original_data or 'threats' in original_data):
                jsonschema.validate(original_data, self.tara_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
        except jsonschema.SchemaError:
            # Schema itself is invalid, skip validation
            pass
        
        return errors
    
    def _calculate_confidence_score(self, assets: List[Dict[str, Any]],
                                   threats: List[Dict[str, Any]],
                                   validation_errors: List[str],
                                   schema_info: Dict[str, Any],
                                   original_data: Union[Dict, List]) -> float:
        """Calculate parsing confidence score."""
        # Start with schema confidence
        score = schema_info['confidence']
        
        # Penalize validation errors
        if validation_errors:
            score -= len(validation_errors) * 0.1
        
        # Reward data completeness
        total_data = len(assets) + len(threats)
        if total_data > 0:
            # Bonus for having both types of data
            if assets and threats:
                score += 0.1
            
            # Bonus for rich data (multiple fields populated)
            rich_assets = sum(1 for asset in assets if sum(1 for v in asset.values() if v) > 3)
            if rich_assets > 0:
                score += 0.05
                
        else:
            score *= 0.2  # Very low score if no data parsed
        
        return max(0.0, min(1.0, score))


# Utility functions
def parse_json_file(file_path: Path) -> JsonParseResult:
    """Convenience function to parse JSON file."""
    parser = JsonParser()
    return parser.parse_file(file_path)


def validate_json_schema(data: Union[Dict, List]) -> tuple[bool, List[str]]:
    """Validate JSON data against TARA schema."""
    parser = JsonParser()
    try:
        if isinstance(data, dict):
            jsonschema.validate(data, parser.tara_schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [e.message]
    except jsonschema.SchemaError as e:
        return False, [f"Schema error: {e.message}"]


def detect_json_structure(data: Union[Dict, List]) -> Dict[str, Any]:
    """Detect JSON structure without full parsing."""
    parser = JsonParser()
    return parser._detect_schema(data)