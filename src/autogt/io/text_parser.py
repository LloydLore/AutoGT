"""Text file parser with pattern recognition for automotive TARA data.

Implements parsing of unstructured text files using natural language
processing and pattern matching to extract asset and threat information.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from pathlib import Path
import logging
from dataclasses import dataclass
from collections import defaultdict, Counter

from ..models.enums import AssetType, CriticalityLevel
from ..core.exceptions import FileParsingError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class TextParseResult:
    """Result of text file parsing with pattern matching metadata."""
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[str]
    confidence_score: float
    detected_patterns: Dict[str, Any]


class TextParser:
    """Text file parser for automotive TARA analysis data.
    
    Uses pattern matching, keyword extraction, and context analysis
    to identify asset and threat information in unstructured text.
    """
    
    def __init__(self):
        """Initialize text parser with patterns and configuration."""
        self.supported_extensions = {'.txt', '.md', '.rst', '.log', '.text'}
        self.max_file_size_mb = 5  # Smaller limit for text files
        
        # Asset identification patterns
        self.asset_patterns = {
            'keywords': [
                'ecu', 'controller', 'sensor', 'actuator', 'gateway', 'display',
                'telematics', 'infotainment', 'brake', 'steering', 'engine',
                'transmission', 'airbag', 'abs', 'esp', 'camera', 'radar',
                'lidar', 'can bus', 'ethernet', 'bluetooth', 'wifi', 'cellular'
            ],
            'prefixes': [
                'component:', 'asset:', 'device:', 'system:', 'module:', 'unit:'
            ],
            'patterns': [
                r'\b(?:ECU|ecu)\s*[-:]\s*([A-Za-z0-9\s]+)',
                r'\b(?:Component|Asset|Device|System|Module)\s*[-:]\s*([A-Za-z0-9\s]+)',
                r'\b([A-Za-z0-9\s]+)\s+(?:ECU|Controller|Sensor|Gateway)',
                r'•\s*([A-Za-z0-9\s]+)(?:\s*[-–]\s*(?:ECU|Controller|System))?',
                r'-\s+([A-Za-z0-9\s]+?)(?:\s*[-:]\s*(?:critical|important|high))?'
            ]
        }
        
        # Threat identification patterns
        self.threat_patterns = {
            'keywords': [
                'attack', 'threat', 'vulnerability', 'exploit', 'breach',
                'injection', 'spoofing', 'tampering', 'repudiation', 'disclosure',
                'denial of service', 'elevation', 'malware', 'intrusion'
            ],
            'stride_categories': [
                'spoofing', 'tampering', 'repudiation', 'information disclosure',
                'denial of service', 'elevation of privilege'
            ],
            'patterns': [
                r'\b(?:Threat|Attack|Vulnerability)\s*[-:]\s*([A-Za-z0-9\s]+)',
                r'\b([A-Za-z0-9\s]+)\s+(?:attack|threat|vulnerability)',
                r'•\s*([A-Za-z0-9\s]+)(?:\s*[-–]\s*(?:attack|threat))?',
                r'T\d+[-.:]\s*([A-Za-z0-9\s]+)',  # Threat numbering
                r'Risk[-:\s]+([A-Za-z0-9\s]+)'
            ]
        }
        
        # Criticality and risk level patterns
        self.criticality_patterns = {
            'high': ['critical', 'high', 'severe', 'major', 'maximum'],
            'medium': ['medium', 'moderate', 'normal', 'standard'],
            'low': ['low', 'minor', 'minimal', 'negligible']
        }
        
        # Interface and protocol patterns
        self.interface_patterns = [
            r'\b(CAN|LIN|FlexRay|Ethernet|MOST|USB|SPI|I2C|UART)\b',
            r'\b(WiFi|Bluetooth|Cellular|4G|5G|LTE|GPS)\b',
            r'\b(TCP/IP|UDP|HTTP|HTTPS|TLS|SSL)\b'
        ]
        
        # Context markers for sections
        self.section_markers = {
            'assets': [
                'components', 'assets', 'systems', 'devices', 'modules',
                'architecture', 'inventory', 'bill of materials', 'bom'
            ],
            'threats': [
                'threats', 'attacks', 'vulnerabilities', 'risks', 'security',
                'threat model', 'attack scenarios', 'stride analysis'
            ]
        }
        
    def parse_file(self, file_path: Path) -> TextParseResult:
        """Parse text file and extract TARA-relevant data.
        
        Args:
            file_path: Path to text file to parse
            
        Returns:
            TextParseResult with parsed data and validation results
            
        Raises:
            FileParsingError: If file cannot be parsed or is invalid
            ValidationError: If data validation fails
        """
        if not self._validate_file(file_path):
            raise FileParsingError(f"File validation failed for {file_path}")
        
        try:
            # Read and preprocess text
            text_content = self._read_text_file(file_path)
            processed_text = self._preprocess_text(text_content)
            
            # Analyze text structure and identify sections
            text_analysis = self._analyze_text_structure(processed_text)
            
            # Extract assets and threats using pattern matching
            assets = self._extract_assets(processed_text, text_analysis)
            threats = self._extract_threats(processed_text, text_analysis)
            
            # Enhance extracted data with context
            assets = self._enhance_asset_data(assets, processed_text)
            threats = self._enhance_threat_data(threats, processed_text)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, text_content, text_analysis)
            
            # Validate parsed data
            validation_errors = self._validate_parsed_data(assets, threats, processed_text)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                assets, threats, validation_errors, text_analysis
            )
            
            return TextParseResult(
                assets=assets,
                threats=threats,
                metadata=metadata,
                validation_errors=validation_errors,
                confidence_score=confidence_score,
                detected_patterns=text_analysis
            )
            
        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {str(e)}")
            raise FileParsingError(f"Text parsing failed: {str(e)}")
    
    def _validate_file(self, file_path: Path) -> bool:
        """Validate file before parsing."""
        # Check file exists
        if not file_path.exists():
            raise FileParsingError(f"File not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() not in self.supported_extensions:
            raise FileParsingError(f"Unsupported file extension: {file_path.suffix}")
        
        # Check file size (5MB limit for text files)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise FileParsingError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        return True
    
    def _read_text_file(self, file_path: Path) -> str:
        """Read text file with encoding detection."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Last resort: read as binary and decode with errors
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            return raw_data.decode('utf-8', errors='ignore')
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better pattern matching."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Normalize dashes and bullets
        text = re.sub(r'[–—]', '-', text)
        text = re.sub(r'[•◦▪▫]', '•', text)
        
        return text
    
    def _analyze_text_structure(self, text: str) -> Dict[str, Any]:
        """Analyze text structure to identify sections and patterns."""
        analysis = {
            'line_count': len(text.split('\n')),
            'word_count': len(text.split()),
            'has_sections': False,
            'sections': {},
            'list_items': 0,
            'numbered_items': 0,
            'asset_density': 0,
            'threat_density': 0,
            'technical_terms': set()
        }
        
        lines = text.split('\n')
        
        # Identify sections
        current_section = 'general'
        analysis['sections'][current_section] = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check for section headers
            section_type = self._identify_section_type(line_lower)
            if section_type:
                current_section = section_type
                analysis['sections'][current_section] = []
                analysis['has_sections'] = True
                continue
            
            analysis['sections'][current_section].append((i, line))
            
            # Count list items
            if re.match(r'^\s*[•\-\*]\s+', line):
                analysis['list_items'] += 1
            elif re.match(r'^\s*\d+[\.\)]\s+', line):
                analysis['numbered_items'] += 1
        
        # Calculate keyword density
        text_lower = text.lower()
        asset_keyword_count = sum(1 for keyword in self.asset_patterns['keywords'] 
                                 if keyword in text_lower)
        threat_keyword_count = sum(1 for keyword in self.threat_patterns['keywords'] 
                                  if keyword in text_lower)
        
        analysis['asset_density'] = asset_keyword_count / max(1, analysis['word_count']) * 100
        analysis['threat_density'] = threat_keyword_count / max(1, analysis['word_count']) * 100
        
        # Extract technical terms
        analysis['technical_terms'] = self._extract_technical_terms(text)
        
        return analysis
    
    def _identify_section_type(self, line: str) -> Optional[str]:
        """Identify if line is a section header and its type."""
        # Check for markdown headers
        if line.startswith('#'):
            line = line.lstrip('#').strip()
        
        # Check for underlined headers
        if len(line) > 2 and line.replace('=', '').replace('-', '').strip() == '':
            return None  # This is an underline, not a header
        
        line_words = line.split()
        if not line_words:
            return None
        
        # Check for asset section markers
        for marker in self.section_markers['assets']:
            if marker in line:
                return 'assets'
        
        # Check for threat section markers
        for marker in self.section_markers['threats']:
            if marker in line:
                return 'threats'
        
        return None
    
    def _extract_technical_terms(self, text: str) -> Set[str]:
        """Extract technical automotive terms from text."""
        terms = set()
        
        # Extract protocol names
        for match in re.finditer('|'.join(self.interface_patterns), text, re.IGNORECASE):
            terms.add(match.group().upper())
        
        # Extract automotive-specific terms
        automotive_pattern = r'\b(?:ECU|CAN|LIN|FlexRay|OBD|AUTOSAR|ISO\s*26262|IVI|TCU|BCM|PCM|ABS|ESP|EPS)\b'
        for match in re.finditer(automotive_pattern, text, re.IGNORECASE):
            terms.add(match.group().upper())
        
        return terms
    
    def _extract_assets(self, text: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract asset information from text using pattern matching."""
        assets = []
        
        # Focus on asset sections if available
        sections_to_search = []
        if 'assets' in analysis['sections']:
            sections_to_search.extend(analysis['sections']['assets'])
        else:
            # Search general sections
            sections_to_search.extend(analysis['sections'].get('general', []))
        
        # Convert sections back to text
        section_text = '\n'.join([line for _, line in sections_to_search])
        if not section_text.strip():
            section_text = text  # Fallback to full text
        
        # Extract using patterns
        found_assets = set()  # Track to avoid duplicates
        
        # Pattern-based extraction
        for pattern in self.asset_patterns['patterns']:
            for match in re.finditer(pattern, section_text, re.IGNORECASE | re.MULTILINE):
                asset_name = match.group(1).strip()
                if asset_name and asset_name not in found_assets and len(asset_name) > 2:
                    asset_data = self._create_asset_from_match(asset_name, match.group(0))
                    if asset_data:
                        assets.append(asset_data)
                        found_assets.add(asset_name)
        
        # Keyword-based extraction from list items
        lines = section_text.split('\n')
        for line in lines:
            if re.match(r'^\s*[•\-\*]\s+', line):
                line_content = re.sub(r'^\s*[•\-\*]\s+', '', line).strip()
                if self._contains_asset_keywords(line_content):
                    asset_name = self._extract_asset_name_from_line(line_content)
                    if asset_name and asset_name not in found_assets:
                        asset_data = self._create_asset_from_line(line_content)
                        if asset_data:
                            assets.append(asset_data)
                            found_assets.add(asset_name)
        
        return assets
    
    def _extract_threats(self, text: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract threat information from text using pattern matching."""
        threats = []
        
        # Focus on threat sections if available
        sections_to_search = []
        if 'threats' in analysis['sections']:
            sections_to_search.extend(analysis['sections']['threats'])
        else:
            sections_to_search.extend(analysis['sections'].get('general', []))
        
        section_text = '\n'.join([line for _, line in sections_to_search])
        if not section_text.strip():
            section_text = text
        
        found_threats = set()
        
        # Pattern-based extraction
        for pattern in self.threat_patterns['patterns']:
            for match in re.finditer(pattern, section_text, re.IGNORECASE | re.MULTILINE):
                threat_name = match.group(1).strip()
                if threat_name and threat_name not in found_threats and len(threat_name) > 3:
                    threat_data = self._create_threat_from_match(threat_name, match.group(0))
                    if threat_data:
                        threats.append(threat_data)
                        found_threats.add(threat_name)
        
        # STRIDE category extraction
        for category in self.threat_patterns['stride_categories']:
            pattern = rf'\b{re.escape(category)}\b.*?(?:attack|threat|risk)'
            for match in re.finditer(pattern, section_text, re.IGNORECASE):
                threat_name = match.group(0).strip()
                if threat_name not in found_threats:
                    threat_data = {
                        'name': threat_name,
                        'category': category.upper(),
                        'description': threat_name,
                        'likelihood': None,
                        'impact': None,
                        'target_asset': None
                    }
                    threats.append(threat_data)
                    found_threats.add(threat_name)
        
        return threats
    
    def _contains_asset_keywords(self, text: str) -> bool:
        """Check if text contains asset-related keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.asset_patterns['keywords'])
    
    def _extract_asset_name_from_line(self, line: str) -> Optional[str]:
        """Extract clean asset name from line."""
        # Remove common suffixes and prefixes
        line = re.sub(r'\s*[-:]\s*(critical|important|high|medium|low).*$', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^(component|asset|device|system|module)\s*[-:]\s*', '', line, flags=re.IGNORECASE)
        
        # Take first meaningful part
        parts = line.split('-', 1)
        name = parts[0].strip()
        
        return name if len(name) > 2 else None
    
    def _create_asset_from_match(self, name: str, context: str) -> Optional[Dict[str, Any]]:
        """Create asset data structure from pattern match."""
        name = name.strip()
        if len(name) < 3:
            return None
        
        # Infer asset type from context and name
        asset_type = self._infer_asset_type(name, context)
        
        # Extract criticality from context
        criticality = self._extract_criticality_from_context(context)
        
        return {
            'name': name,
            'asset_type': asset_type,
            'criticality': criticality,
            'interfaces': [],
            'description': context.strip(),
            'location': None,
            'manufacturer': None
        }
    
    def _create_asset_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Create asset data structure from line content."""
        name = self._extract_asset_name_from_line(line)
        if not name:
            return None
        
        asset_type = self._infer_asset_type(name, line)
        criticality = self._extract_criticality_from_context(line)
        
        return {
            'name': name,
            'asset_type': asset_type,
            'criticality': criticality,
            'interfaces': [],
            'description': line.strip(),
            'location': None,
            'manufacturer': None
        }
    
    def _create_threat_from_match(self, name: str, context: str) -> Optional[Dict[str, Any]]:
        """Create threat data structure from pattern match."""
        name = name.strip()
        if len(name) < 3:
            return None
        
        # Infer category from context
        category = self._infer_threat_category(name, context)
        
        return {
            'name': name,
            'category': category,
            'description': context.strip(),
            'likelihood': None,
            'impact': None,
            'target_asset': None
        }
    
    def _infer_asset_type(self, name: str, context: str) -> str:
        """Infer asset type from name and context."""
        name_lower = name.lower()
        context_lower = context.lower()
        
        # ECU patterns
        if 'ecu' in name_lower or 'controller' in name_lower or 'control' in name_lower:
            return 'ECU'
        
        # Sensor patterns
        if any(sensor in name_lower for sensor in ['sensor', 'camera', 'radar', 'lidar']):
            return 'SENSOR'
        
        # Gateway patterns
        if 'gateway' in name_lower or 'bridge' in name_lower:
            return 'GATEWAY'
        
        # Network patterns
        if any(net in context_lower for net in ['can', 'ethernet', 'network', 'bus']):
            return 'NETWORK'
        
        # Display patterns
        if any(display in name_lower for display in ['display', 'screen', 'hmi', 'cluster']):
            return 'DISPLAY'
        
        # Default to hardware component
        return 'HARDWARE_COMPONENT'
    
    def _infer_threat_category(self, name: str, context: str) -> Optional[str]:
        """Infer STRIDE threat category from name and context."""
        name_lower = name.lower()
        context_lower = context.lower()
        
        # STRIDE category mapping
        if any(term in context_lower for term in ['spoof', 'imperson', 'fake']):
            return 'SPOOFING'
        elif any(term in context_lower for term in ['tamper', 'modify', 'alter']):
            return 'TAMPERING'
        elif any(term in context_lower for term in ['deny', 'repudiat', 'claim']):
            return 'REPUDIATION'
        elif any(term in context_lower for term in ['disclosure', 'leak', 'expose', 'reveal']):
            return 'INFORMATION_DISCLOSURE'
        elif any(term in context_lower for term in ['dos', 'denial', 'flood', 'exhaust']):
            return 'DENIAL_OF_SERVICE'
        elif any(term in context_lower for term in ['elevat', 'privileg', 'escalat', 'admin']):
            return 'ELEVATION_OF_PRIVILEGE'
        
        return None
    
    def _extract_criticality_from_context(self, context: str) -> str:
        """Extract criticality level from context."""
        context_lower = context.lower()
        
        for level, keywords in self.criticality_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return level.upper()
        
        return 'MEDIUM'
    
    def _enhance_asset_data(self, assets: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Enhance asset data with additional context from text."""
        for asset in assets:
            # Look for interface mentions near asset name
            asset_context = self._find_context_around_term(text, asset['name'])
            interfaces = self._extract_interfaces_from_context(asset_context)
            asset['interfaces'] = interfaces
            
            # Look for location information
            location = self._extract_location_from_context(asset_context)
            if location:
                asset['location'] = location
        
        return assets
    
    def _enhance_threat_data(self, threats: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Enhance threat data with additional context from text."""
        for threat in threats:
            # Look for likelihood and impact mentions
            threat_context = self._find_context_around_term(text, threat['name'])
            
            likelihood = self._extract_likelihood_from_context(threat_context)
            if likelihood:
                threat['likelihood'] = likelihood
            
            impact = self._extract_impact_from_context(threat_context)
            if impact:
                threat['impact'] = impact
        
        return threats
    
    def _find_context_around_term(self, text: str, term: str, window: int = 100) -> str:
        """Find text context around a specific term."""
        term_lower = term.lower()
        text_lower = text.lower()
        
        index = text_lower.find(term_lower)
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(text), index + len(term) + window)
        
        return text[start:end]
    
    def _extract_interfaces_from_context(self, context: str) -> List[str]:
        """Extract interface protocols from context."""
        interfaces = []
        
        for pattern in self.interface_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            interfaces.extend([match.upper() for match in matches])
        
        return list(set(interfaces))  # Remove duplicates
    
    def _extract_location_from_context(self, context: str) -> Optional[str]:
        """Extract location information from context."""
        location_patterns = [
            r'(?:located|positioned|placed)\s+(?:in|at|on)\s+([A-Za-z0-9\s]+)',
            r'(?:zone|area|compartment)\s*[-:]\s*([A-Za-z0-9\s]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_likelihood_from_context(self, context: str) -> Optional[str]:
        """Extract likelihood assessment from context."""
        likelihood_patterns = [
            r'(?:likelihood|probability|chance)\s*[-:]\s*(high|medium|low)',
            r'(unlikely|possible|likely|very\s+likely)',
            r'(\d+%|\d+/\d+)'
        ]
        
        for pattern in likelihood_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_impact_from_context(self, context: str) -> Optional[str]:
        """Extract impact assessment from context."""
        impact_patterns = [
            r'(?:impact|severity|consequence)\s*[-:]\s*(high|medium|low|critical)',
            r'(catastrophic|major|moderate|minor|negligible)',
            r'(severe|serious|significant|limited)'
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_metadata(self, file_path: Path, text: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract file and parsing metadata."""
        return {
            'filename': file_path.name,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 3),
            'line_count': analysis['line_count'],
            'word_count': analysis['word_count'],
            'has_sections': analysis['has_sections'],
            'section_count': len(analysis['sections']),
            'list_items': analysis['list_items'],
            'numbered_items': analysis['numbered_items'],
            'asset_keyword_density': round(analysis['asset_density'], 2),
            'threat_keyword_density': round(analysis['threat_density'], 2),
            'technical_terms_count': len(analysis['technical_terms']),
            'technical_terms': list(analysis['technical_terms']),
            'parser_version': '1.0.0'
        }
    
    def _validate_parsed_data(self, assets: List[Dict[str, Any]],
                             threats: List[Dict[str, Any]], text: str) -> List[str]:
        """Validate parsed data against business rules."""
        errors = []
        
        # Check for minimum data requirements
        if not assets and not threats:
            errors.append("No assets or threats extracted from text")
        
        # Validate asset uniqueness
        asset_names = [asset['name'] for asset in assets]
        duplicates = [name for name, count in Counter(asset_names).items() if count > 1]
        for duplicate in duplicates:
            errors.append(f"Duplicate asset name found: {duplicate}")
        
        # Check for very short or generic names
        for asset in assets:
            if len(asset['name']) < 3:
                errors.append(f"Asset name too short: '{asset['name']}'")
            elif asset['name'].lower() in ['system', 'device', 'component', 'module']:
                errors.append(f"Asset name too generic: '{asset['name']}'")
        
        for threat in threats:
            if len(threat['name']) < 3:
                errors.append(f"Threat name too short: '{threat['name']}'")
        
        # Check extraction quality
        text_length = len(text.split())
        if text_length > 100 and not assets and not threats:
            errors.append("No automotive TARA data detected in substantial text content")
        
        return errors
    
    def _calculate_confidence_score(self, assets: List[Dict[str, Any]],
                                   threats: List[Dict[str, Any]],
                                   validation_errors: List[str],
                                   analysis: Dict[str, Any]) -> float:
        """Calculate parsing confidence score based on multiple factors."""
        score = 0.3  # Base score for text parsing (inherently less reliable)
        
        # Boost for finding data
        data_count = len(assets) + len(threats)
        if data_count > 0:
            score += min(0.3, data_count * 0.05)
        
        # Boost for technical term density
        if analysis['technical_terms']:
            score += min(0.2, len(analysis['technical_terms']) * 0.02)
        
        # Boost for structured content
        if analysis['has_sections']:
            score += 0.1
        if analysis['list_items'] > 0:
            score += min(0.1, analysis['list_items'] * 0.01)
        
        # Boost for automotive keyword density
        if analysis['asset_density'] > 0.5:
            score += 0.1
        if analysis['threat_density'] > 0.3:
            score += 0.1
        
        # Penalize validation errors
        score -= len(validation_errors) * 0.1
        
        # Penalize if no clear automotive content
        if analysis['asset_density'] < 0.1 and analysis['threat_density'] < 0.1:
            score *= 0.5
        
        return max(0.0, min(1.0, score))


# Utility functions
def parse_text_file(file_path: Path) -> TextParseResult:
    """Convenience function to parse text file."""
    parser = TextParser()
    return parser.parse_file(file_path)


def analyze_text_content(text: str) -> Dict[str, Any]:
    """Analyze text content without full parsing."""
    parser = TextParser()
    return parser._analyze_text_structure(text)


def extract_automotive_terms(text: str) -> Set[str]:
    """Extract automotive technical terms from text."""
    parser = TextParser()
    return parser._extract_technical_terms(text)