"""Threat identification service with pattern matching.

Provides comprehensive threat analysis capabilities including identification,
categorization, impact assessment, and AI-powered threat modeling.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.threat import ThreatScenario
from ..models.asset import Asset
from ..models.enums import StrideCategory, ThreatCategory
from ..ai.orchestrator import TaraOrchestrator
from ..core.exceptions import ValidationError, AnalysisError


logger = logging.getLogger(__name__)


@dataclass
class ThreatIdentificationResult:
    """Result of threat identification operation."""
    threats_identified: int
    confidence_scores: Dict[str, float]
    stride_coverage: Dict[str, int]
    asset_coverage: Dict[str, int]
    recommendations: List[str]


@dataclass
class ThreatAnalysisResult:
    """Result of comprehensive threat analysis."""
    total_threats: int
    by_category: Dict[str, int]
    by_stride: Dict[str, int]
    by_impact: Dict[str, int]
    attack_paths_identified: int
    coverage_analysis: Dict[str, Any]


class ThreatIdentificationService:
    """Service for identifying and analyzing cybersecurity threats."""
    
    def __init__(self, db_session: Session):
        """Initialize threat identification service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.ai_orchestrator = TaraOrchestrator()
        
        # STRIDE threat patterns per automotive context
        self.stride_patterns = {
            'SPOOFING': {
                'keywords': ['impersonation', 'fake', 'masquerade', 'spoof', 'identity'],
                'asset_types': ['ECU', 'GATEWAY', 'SENSOR', 'TELEMATICS'],
                'interfaces': ['CAN', 'ETHERNET', 'WIFI', 'BLUETOOTH', 'CELLULAR']
            },
            'TAMPERING': {
                'keywords': ['modify', 'alter', 'corrupt', 'manipulate', 'inject'],
                'asset_types': ['ECU', 'SENSOR', 'ACTUATOR', 'MEMORY'],
                'interfaces': ['CAN', 'LIN', 'SPI', 'I2C', 'ETHERNET']
            },
            'REPUDIATION': {
                'keywords': ['deny', 'log', 'audit', 'trace', 'evidence'],
                'asset_types': ['GATEWAY', 'TELEMATICS', 'LOGGING_SYSTEM'],
                'interfaces': ['ETHERNET', 'CELLULAR', 'WIFI']
            },
            'INFORMATION_DISCLOSURE': {
                'keywords': ['leak', 'expose', 'reveal', 'eavesdrop', 'intercept'],
                'asset_types': ['ECU', 'GATEWAY', 'TELEMATICS', 'MEMORY'],
                'interfaces': ['CAN', 'ETHERNET', 'WIFI', 'BLUETOOTH', 'CELLULAR']
            },
            'DENIAL_OF_SERVICE': {
                'keywords': ['flood', 'exhaust', 'block', 'disable', 'overwhelm'],
                'asset_types': ['ECU', 'GATEWAY', 'NETWORK', 'BUS'],
                'interfaces': ['CAN', 'ETHERNET', 'WIFI', 'CELLULAR']
            },
            'ELEVATION_OF_PRIVILEGE': {
                'keywords': ['escalate', 'privilege', 'admin', 'root', 'permission'],
                'asset_types': ['ECU', 'GATEWAY', 'TELEMATICS', 'HYPERVISOR'],
                'interfaces': ['ETHERNET', 'DEBUG', 'JTAG']
            }
        }
        
        # Automotive-specific threat categories
        self.automotive_threats = {
            'CAN_BUS_ATTACKS': {
                'description': 'Attacks targeting CAN bus communication',
                'techniques': ['CAN injection', 'CAN flooding', 'CAN sniffing'],
                'affected_assets': ['ECU', 'GATEWAY', 'CAN_BUS']
            },
            'ECU_COMPROMISE': {
                'description': 'Electronic Control Unit compromise scenarios',
                'techniques': ['Firmware modification', 'Memory corruption', 'Debug access'],
                'affected_assets': ['ECU', 'MEMORY', 'FLASH']
            },
            'WIRELESS_ATTACKS': {
                'description': 'Attacks via wireless interfaces',
                'techniques': ['WiFi exploitation', 'Bluetooth attacks', 'Cellular hijacking'],
                'affected_assets': ['TELEMATICS', 'INFOTAINMENT', 'GATEWAY']
            },
            'SUPPLY_CHAIN_ATTACKS': {
                'description': 'Attacks through compromised components',
                'techniques': ['Malicious components', 'Firmware backdoors', 'Hardware trojans'],
                'affected_assets': ['ECU', 'SENSOR', 'ACTUATOR']
            }
        }
    
    async def identify_threats_for_analysis(self, analysis_id: str) -> ThreatIdentificationResult:
        """Identify threats for all assets in an analysis.
        
        Args:
            analysis_id: ID of analysis to identify threats for
            
        Returns:
            Comprehensive threat identification results
        """
        try:
            logger.info(f"Starting threat identification for analysis {analysis_id}")
            
            # Get assets for analysis
            assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
            
            if not assets:
                raise AnalysisError("No assets found for threat identification")
            
            # Identify threats using multiple approaches
            ai_threats = await self._identify_threats_ai(assets)
            pattern_threats = self._identify_threats_patterns(assets)
            automotive_threats = self._identify_automotive_threats(assets)
            
            # Combine and deduplicate threats
            all_threats = self._combine_threat_sources(ai_threats, pattern_threats, automotive_threats)
            
            # Create threat records
            threats_created = 0
            confidence_scores = {}
            stride_coverage = {}
            asset_coverage = {}
            
            for threat_data in all_threats:
                # Check for existing threat to avoid duplicates
                existing = self.db_session.query(ThreatScenario).filter(
                    and_(
                        ThreatScenario.analysis_id == analysis_id,
                        ThreatScenario.name == threat_data['name']
                    )
                ).first()
                
                if not existing:
                    threat = ThreatScenario(
                        analysis_id=analysis_id,
                        name=threat_data['name'],
                        category=threat_data.get('category'),
                        description=threat_data['description'],
                        stride_category=threat_data.get('stride_category'),
                        target_assets=threat_data.get('target_assets', []),
                        impact_rating=threat_data.get('impact_rating'),
                        likelihood_rating=threat_data.get('likelihood_rating')
                    )
                    
                    self.db_session.add(threat)
                    threats_created += 1
                    
                    # Track metrics
                    confidence_scores[threat.name] = threat_data.get('confidence_score', 0.7)
                    
                    stride = threat_data.get('stride_category', 'UNKNOWN')
                    stride_coverage[stride] = stride_coverage.get(stride, 0) + 1
                    
                    for asset in threat_data.get('target_assets', []):
                        asset_coverage[asset] = asset_coverage.get(asset, 0) + 1
            
            self.db_session.commit()
            
            # Generate recommendations
            recommendations = await self._generate_threat_recommendations(analysis_id, assets)
            
            return ThreatIdentificationResult(
                threats_identified=threats_created,
                confidence_scores=confidence_scores,
                stride_coverage=stride_coverage,
                asset_coverage=asset_coverage,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to identify threats for analysis {analysis_id}: {str(e)}")
            raise AnalysisError(f"Threat identification failed: {str(e)}")
    
    async def identify_threats_for_asset(self, analysis_id: str, asset_id: str) -> List[Dict[str, Any]]:
        """Identify threats specific to a single asset.
        
        Args:
            analysis_id: ID of analysis
            asset_id: ID of specific asset
            
        Returns:
            List of identified threats for the asset
        """
        asset = self.db_session.query(Asset).filter(
            and_(Asset.analysis_id == analysis_id, Asset.id == asset_id)
        ).first()
        
        if not asset:
            raise AnalysisError(f"Asset not found: {asset_id}")
        
        # Get AI-powered threat identification
        ai_threats = await self.ai_orchestrator.identify_asset_threats([self._asset_to_dict(asset)])
        
        # Apply pattern matching
        pattern_threats = self._identify_threats_for_single_asset(asset)
        
        # Combine results
        return self._combine_threat_sources(ai_threats, pattern_threats, [])
    
    def analyze_threat_coverage(self, analysis_id: str) -> ThreatAnalysisResult:
        """Analyze threat coverage and completeness for analysis.
        
        Args:
            analysis_id: ID of analysis to analyze
            
        Returns:
            Comprehensive threat analysis results
        """
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
        
        # Calculate statistics
        total_threats = len(threats)
        by_category = {}
        by_stride = {}
        by_impact = {}
        attack_paths = 0
        
        for threat in threats:
            # Count by category
            category = threat.category or 'UNKNOWN'
            by_category[category] = by_category.get(category, 0) + 1
            
            # Count by STRIDE
            stride = threat.stride_category or 'UNKNOWN'
            by_stride[stride] = by_stride.get(stride, 0) + 1
            
            # Count by impact
            impact = threat.impact_rating or 'MEDIUM'
            by_impact[impact] = by_impact.get(impact, 0) + 1
            
            # Count attack paths
            if threat.metadata and threat.metadata.get('attack_paths'):
                attack_paths += len(threat.metadata['attack_paths'])
        
        # Analyze coverage
        coverage_analysis = self._analyze_coverage_completeness(threats, assets)
        
        return ThreatAnalysisResult(
            total_threats=total_threats,
            by_category=by_category,
            by_stride=by_stride,
            by_impact=by_impact,
            attack_paths_identified=attack_paths,
            coverage_analysis=coverage_analysis
        )
    
    def get_threats_by_analysis(self, analysis_id: str, filters: Dict[str, Any] = None) -> List[ThreatScenario]:
        """Get threats for analysis with optional filtering.
        
        Args:
            analysis_id: ID of analysis
            filters: Optional filters (category, stride_category, etc.)
            
        Returns:
            List of matching threats
        """
        query = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id)
        
        if filters:
            if 'category' in filters:
                query = query.filter(ThreatScenario.category == filters['category'])
            
            if 'stride_category' in filters:
                query = query.filter(ThreatScenario.stride_category == filters['stride_category'])
            
            if 'impact_rating' in filters:
                query = query.filter(ThreatScenario.impact_rating == filters['impact_rating'])
            
            if 'target_asset' in filters:
                query = query.filter(ThreatScenario.target_assets.contains([filters['target_asset']]))
        
        return query.all()
    
    async def _identify_threats_ai(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Identify threats using AI orchestrator."""
        assets_data = [self._asset_to_dict(asset) for asset in assets]
        return await self.ai_orchestrator.identify_threats(assets_data)
    
    def _identify_threats_patterns(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Identify threats using pattern matching."""
        threats = []
        
        for asset in assets:
            asset_threats = self._identify_threats_for_single_asset(asset)
            threats.extend(asset_threats)
        
        return threats
    
    def _identify_threats_for_single_asset(self, asset: Asset) -> List[Dict[str, Any]]:
        """Identify threats for a single asset using patterns."""
        threats = []
        asset_type = asset.asset_type
        interfaces = asset.interfaces or []
        criticality = asset.criticality
        
        # Check each STRIDE category
        for stride_category, patterns in self.stride_patterns.items():
            if asset_type in patterns['asset_types']:
                # Check interface matches
                interface_matches = [i for i in interfaces if i in patterns['interfaces']]
                
                if interface_matches or not patterns['interfaces']:
                    threat = {
                        'name': f"{stride_category} attack on {asset.name}",
                        'description': f"Potential {stride_category.lower().replace('_', ' ')} attack targeting {asset.name}",
                        'category': 'PATTERN_BASED',
                        'stride_category': stride_category,
                        'target_assets': [asset.name],
                        'impact_rating': self._assess_pattern_impact(criticality, stride_category),
                        'likelihood_rating': self._assess_pattern_likelihood(asset_type, interfaces, stride_category),
                        'confidence_score': 0.6,
                        'source': 'pattern_matching'
                    }
                    threats.append(threat)
        
        return threats
    
    def _identify_automotive_threats(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Identify automotive-specific threats."""
        threats = []
        
        # Group assets by type for targeted analysis
        assets_by_type = {}
        for asset in assets:
            asset_type = asset.asset_type
            if asset_type not in assets_by_type:
                assets_by_type[asset_type] = []
            assets_by_type[asset_type].append(asset)
        
        # Check for specific automotive threat scenarios
        if 'ECU' in assets_by_type or 'CAN_BUS' in assets_by_type:
            threats.extend(self._generate_can_bus_threats(assets))
        
        if 'TELEMATICS' in assets_by_type or 'INFOTAINMENT' in assets_by_type:
            threats.extend(self._generate_wireless_threats(assets))
        
        if any(asset.interfaces and 'ETHERNET' in asset.interfaces for asset in assets):
            threats.extend(self._generate_ethernet_threats(assets))
        
        return threats
    
    def _generate_can_bus_threats(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Generate CAN bus specific threats."""
        threats = []
        can_assets = [a for a in assets if 'CAN' in (a.interfaces or []) or a.asset_type in ['ECU', 'CAN_BUS', 'GATEWAY']]
        
        if can_assets:
            threats.append({
                'name': 'CAN Bus Message Injection',
                'description': 'Unauthorized injection of CAN messages to control vehicle functions',
                'category': 'CAN_BUS_ATTACKS',
                'stride_category': 'TAMPERING',
                'target_assets': [a.name for a in can_assets],
                'impact_rating': 'HIGH',
                'likelihood_rating': 'MEDIUM',
                'confidence_score': 0.8,
                'source': 'automotive_specific'
            })
            
            threats.append({
                'name': 'CAN Bus Denial of Service',
                'description': 'Flooding CAN bus with messages to disrupt normal communication',
                'category': 'CAN_BUS_ATTACKS',
                'stride_category': 'DENIAL_OF_SERVICE',
                'target_assets': [a.name for a in can_assets],
                'impact_rating': 'HIGH',
                'likelihood_rating': 'MEDIUM',
                'confidence_score': 0.8,
                'source': 'automotive_specific'
            })
        
        return threats
    
    def _generate_wireless_threats(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Generate wireless interface threats."""
        threats = []
        wireless_assets = [a for a in assets if any(w in (a.interfaces or []) for w in ['WIFI', 'BLUETOOTH', 'CELLULAR'])]
        
        if wireless_assets:
            threats.append({
                'name': 'Wireless Interface Exploitation',
                'description': 'Remote exploitation through wireless communication interfaces',
                'category': 'WIRELESS_ATTACKS',
                'stride_category': 'ELEVATION_OF_PRIVILEGE',
                'target_assets': [a.name for a in wireless_assets],
                'impact_rating': 'HIGH',
                'likelihood_rating': 'MEDIUM',
                'confidence_score': 0.7,
                'source': 'automotive_specific'
            })
        
        return threats
    
    def _generate_ethernet_threats(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Generate Ethernet-specific threats."""
        threats = []
        ethernet_assets = [a for a in assets if 'ETHERNET' in (a.interfaces or [])]
        
        if ethernet_assets:
            threats.append({
                'name': 'Ethernet Network Intrusion',
                'description': 'Network-based attacks through automotive Ethernet connections',
                'category': 'NETWORK_ATTACKS',
                'stride_category': 'INFORMATION_DISCLOSURE',
                'target_assets': [a.name for a in ethernet_assets],
                'impact_rating': 'MEDIUM',
                'likelihood_rating': 'MEDIUM',
                'confidence_score': 0.7,
                'source': 'automotive_specific'
            })
        
        return threats
    
    def _combine_threat_sources(self, ai_threats: List[Dict], pattern_threats: List[Dict], 
                              automotive_threats: List[Dict]) -> List[Dict[str, Any]]:
        """Combine threats from different sources and remove duplicates."""
        all_threats = []
        seen_names = set()
        
        # Prioritize AI threats (highest confidence)
        for threat in ai_threats:
            name_key = threat['name'].lower().strip()
            if name_key not in seen_names:
                all_threats.append(threat)
                seen_names.add(name_key)
        
        # Add automotive-specific threats (medium confidence)
        for threat in automotive_threats:
            name_key = threat['name'].lower().strip()
            if name_key not in seen_names:
                all_threats.append(threat)
                seen_names.add(name_key)
        
        # Add pattern-based threats (lower confidence)
        for threat in pattern_threats:
            name_key = threat['name'].lower().strip()
            if name_key not in seen_names:
                all_threats.append(threat)
                seen_names.add(name_key)
        
        return all_threats
    
    def _assess_pattern_impact(self, asset_criticality: str, stride_category: str) -> str:
        """Assess impact rating based on asset criticality and STRIDE category."""
        # Impact matrix
        high_impact_strides = ['TAMPERING', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE']
        
        if asset_criticality == 'CRITICAL':
            return 'HIGH'
        elif asset_criticality == 'HIGH' and stride_category in high_impact_strides:
            return 'HIGH'
        elif stride_category in high_impact_strides:
            return 'MEDIUM'
        else:
            return 'MEDIUM'
    
    def _assess_pattern_likelihood(self, asset_type: str, interfaces: List[str], stride_category: str) -> str:
        """Assess likelihood rating based on asset characteristics."""
        # Higher likelihood for exposed interfaces
        exposed_interfaces = ['WIFI', 'BLUETOOTH', 'CELLULAR', 'ETHERNET']
        has_exposed = any(i in interfaces for i in exposed_interfaces)
        
        # Higher likelihood for common attack vectors
        common_attacks = ['TAMPERING', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE']
        
        if has_exposed and stride_category in common_attacks:
            return 'MEDIUM'
        elif has_exposed or stride_category in common_attacks:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _analyze_coverage_completeness(self, threats: List[ThreatScenario], assets: List[Asset]) -> Dict[str, Any]:
        """Analyze completeness of threat coverage."""
        # Check STRIDE coverage
        stride_categories = [s.value for s in StrideCategory]
        covered_strides = set(t.stride_category for t in threats if t.stride_category)
        missing_strides = [s for s in stride_categories if s not in covered_strides]
        
        # Check asset coverage
        asset_names = [a.name for a in assets]
        threatened_assets = set()
        for threat in threats:
            threatened_assets.update(threat.target_assets or [])
        
        uncovered_assets = [a for a in asset_names if a not in threatened_assets]
        
        # Check interface coverage
        all_interfaces = set()
        for asset in assets:
            all_interfaces.update(asset.interfaces or [])
        
        interface_threats = {}
        for interface in all_interfaces:
            interface_threats[interface] = sum(1 for threat in threats 
                                             if any(asset in (threat.target_assets or []) 
                                                  for asset in asset_names
                                                  for a in assets 
                                                  if a.name == asset and interface in (a.interfaces or [])))
        
        return {
            'stride_coverage': {
                'covered': list(covered_strides),
                'missing': missing_strides,
                'coverage_percentage': len(covered_strides) / len(stride_categories) * 100
            },
            'asset_coverage': {
                'covered_assets': len(asset_names) - len(uncovered_assets),
                'total_assets': len(asset_names),
                'uncovered_assets': uncovered_assets,
                'coverage_percentage': (len(asset_names) - len(uncovered_assets)) / len(asset_names) * 100 if asset_names else 100
            },
            'interface_coverage': interface_threats
        }
    
    async def _generate_threat_recommendations(self, analysis_id: str, assets: List[Asset]) -> List[str]:
        """Generate recommendations for improving threat coverage."""
        recommendations = []
        
        # Analyze current threats
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        coverage = self._analyze_coverage_completeness(threats, assets)
        
        # Recommendations based on coverage gaps
        if coverage['stride_coverage']['missing']:
            recommendations.append(f"Consider threats for missing STRIDE categories: {', '.join(coverage['stride_coverage']['missing'])}")
        
        if coverage['asset_coverage']['uncovered_assets']:
            recommendations.append(f"Identify threats for uncovered assets: {', '.join(coverage['asset_coverage']['uncovered_assets'][:3])}{'...' if len(coverage['asset_coverage']['uncovered_assets']) > 3 else ''}")
        
        # AI-powered recommendations
        ai_recommendations = await self.ai_orchestrator.recommend_threat_improvements(
            [self._threat_to_dict(threat) for threat in threats],
            [self._asset_to_dict(asset) for asset in assets]
        )
        recommendations.extend(ai_recommendations[:5])
        
        return recommendations[:10]
    
    def _asset_to_dict(self, asset: Asset) -> Dict[str, Any]:
        """Convert Asset model to dictionary."""
        return {
            'id': asset.id,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'criticality': asset.criticality,
            'interfaces': asset.interfaces or [],
            'description': asset.description,
            'location': asset.location,
            'manufacturer': asset.manufacturer
        }
    
    def _threat_to_dict(self, threat: ThreatScenario) -> Dict[str, Any]:
        """Convert ThreatScenario model to dictionary."""
        return {
            'id': threat.id,
            'name': threat.name,
            'category': threat.category,
            'description': threat.description,
            'stride_category': threat.stride_category,
            'target_assets': threat.target_assets or [],
            'impact_rating': threat.impact_rating,
            'likelihood_rating': threat.likelihood_rating
        }