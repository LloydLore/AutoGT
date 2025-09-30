"""Asset definition service with AI integration per FR-008.

Provides comprehensive asset management capabilities including definition,
validation, enhancement, and impact assessment with AI automation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.asset import Asset
from ..models.enums import AssetType, CriticalityLevel
from ..ai.orchestrator import TaraOrchestrator
from ..core.exceptions import ValidationError, AnalysisError


logger = logging.getLogger(__name__)


@dataclass
class AssetDefinitionResult:
    """Result of asset definition operation."""
    asset_id: str
    name: str
    validation_status: str
    ai_enhancements: Dict[str, Any]
    confidence_score: float
    suggestions: List[str]


@dataclass
class AssetAnalysisResult:
    """Result of asset analysis and enhancement."""
    assets_processed: int
    enhancements_applied: int
    validation_issues: List[str]
    recommendations: List[str]
    confidence_scores: Dict[str, float]


class AssetDefinitionService:
    """Service for managing asset definition and AI-powered enhancement."""
    
    def __init__(self, db_session: Session):
        """Initialize asset definition service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.ai_orchestrator = TaraOrchestrator()
        
        # Asset validation rules per FR-008
        self.validation_rules = {
            'name': {
                'required': True,
                'min_length': 3,
                'max_length': 100,
                'pattern': r'^[A-Za-z0-9\s\-_\.]+$'
            },
            'asset_type': {
                'required': True,
                'valid_values': [t.value for t in AssetType]
            },
            'criticality': {
                'required': True,
                'valid_values': [c.value for c in CriticalityLevel]
            },
            'interfaces': {
                'max_count': 20,
                'valid_protocols': ['CAN', 'LIN', 'FLEXRAY', 'ETHERNET', 'MOST', 'USB', 'SPI', 'I2C', 'UART', 'WIFI', 'BLUETOOTH', 'CELLULAR', '4G', '5G', 'LTE']
            }
        }
        
    async def define_asset_interactive(self, analysis_id: str, 
                                     initial_data: Dict[str, Any] = None) -> AssetDefinitionResult:
        """Define asset interactively with AI assistance.
        
        Args:
            analysis_id: ID of analysis to add asset to
            initial_data: Optional initial asset data
            
        Returns:
            Asset definition result with AI enhancements
        """
        try:
            logger.info(f"Starting interactive asset definition for analysis {analysis_id}")
            
            # Get AI suggestions for asset definition
            suggestions = await self.ai_orchestrator.suggest_asset_definition(
                analysis_id, initial_data or {}
            )
            
            # Validate and enhance the asset data
            enhanced_data = await self._enhance_asset_data(initial_data or {})
            
            # Create asset record
            asset = Asset(
                analysis_id=analysis_id,
                name=enhanced_data['name'],
                asset_type=enhanced_data['asset_type'],
                criticality=enhanced_data['criticality'],
                interfaces=enhanced_data.get('interfaces', []),
                description=enhanced_data.get('description'),
                location=enhanced_data.get('location'),
                manufacturer=enhanced_data.get('manufacturer')
            )
            
            # Validate asset
            validation_result = self.validate_asset_data(asset.__dict__)
            
            if validation_result['is_valid']:
                self.db_session.add(asset)
                self.db_session.commit()
                
                return AssetDefinitionResult(
                    asset_id=asset.id,
                    name=asset.name,
                    validation_status='valid',
                    ai_enhancements=enhanced_data.get('ai_enhancements', {}),
                    confidence_score=enhanced_data.get('confidence_score', 0.8),
                    suggestions=suggestions
                )
            else:
                raise ValidationError(f"Asset validation failed: {validation_result['errors']}")
                
        except Exception as e:
            logger.error(f"Failed to define asset interactively: {str(e)}")
            raise AnalysisError(f"Interactive asset definition failed: {str(e)}")
    
    async def define_assets_batch(self, analysis_id: str, 
                                assets_data: List[Dict[str, Any]]) -> AssetAnalysisResult:
        """Define multiple assets in batch with AI enhancement.
        
        Args:
            analysis_id: ID of analysis to add assets to
            assets_data: List of asset data dictionaries
            
        Returns:
            Batch processing results with enhancements
        """
        try:
            logger.info(f"Starting batch asset definition for analysis {analysis_id} ({len(assets_data)} assets)")
            
            processed_count = 0
            enhanced_count = 0
            validation_issues = []
            confidence_scores = {}
            
            # Process assets in batches for AI enhancement
            enhanced_assets = await self.ai_orchestrator.enhance_assets_batch(assets_data)
            
            for i, asset_data in enumerate(assets_data):
                try:
                    # Use AI enhancement if available
                    if i < len(enhanced_assets):
                        enhanced_data = enhanced_assets[i]
                        enhanced_count += 1
                    else:
                        enhanced_data = asset_data
                    
                    # Create asset
                    asset = Asset(
                        analysis_id=analysis_id,
                        name=enhanced_data['name'],
                        asset_type=enhanced_data.get('asset_type', 'HARDWARE_COMPONENT'),
                        criticality=enhanced_data.get('criticality', 'MEDIUM'),
                        interfaces=enhanced_data.get('interfaces', []),
                        description=enhanced_data.get('description'),
                        location=enhanced_data.get('location'),
                        manufacturer=enhanced_data.get('manufacturer')
                    )
                    
                    # Validate asset
                    validation_result = self.validate_asset_data(asset.__dict__)
                    
                    if validation_result['is_valid']:
                        self.db_session.add(asset)
                        processed_count += 1
                        confidence_scores[asset.name] = enhanced_data.get('confidence_score', 0.7)
                    else:
                        validation_issues.extend([f"{asset.name}: {error}" for error in validation_result['errors']])
                        
                except Exception as e:
                    validation_issues.append(f"Asset {i+1}: {str(e)}")
            
            self.db_session.commit()
            
            # Generate recommendations
            recommendations = await self._generate_asset_recommendations(analysis_id)
            
            return AssetAnalysisResult(
                assets_processed=processed_count,
                enhancements_applied=enhanced_count,
                validation_issues=validation_issues,
                recommendations=recommendations,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to define assets in batch: {str(e)}")
            raise AnalysisError(f"Batch asset definition failed: {str(e)}")
    
    def validate_asset_data(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate asset data against business rules.
        
        Args:
            asset_data: Asset data to validate
            
        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []
        
        # Validate required fields
        for field, rules in self.validation_rules.items():
            if field not in asset_data:
                if rules.get('required', False):
                    errors.append(f"Required field '{field}' is missing")
                continue
                
            value = asset_data[field]
            
            # Validate field-specific rules
            if field == 'name':
                if not value or len(str(value).strip()) < rules['min_length']:
                    errors.append(f"Asset name must be at least {rules['min_length']} characters")
                elif len(str(value)) > rules['max_length']:
                    errors.append(f"Asset name must not exceed {rules['max_length']} characters")
                
                import re
                if not re.match(rules['pattern'], str(value)):
                    errors.append("Asset name contains invalid characters")
            
            elif field in ['asset_type', 'criticality']:
                if value not in rules['valid_values']:
                    errors.append(f"Invalid {field}: {value}. Valid values: {rules['valid_values']}")
            
            elif field == 'interfaces':
                if isinstance(value, list):
                    if len(value) > rules['max_count']:
                        warnings.append(f"Asset has {len(value)} interfaces, which may be excessive")
                    
                    invalid_protocols = [p for p in value if p.upper() not in rules['valid_protocols']]
                    if invalid_protocols:
                        warnings.append(f"Unknown interface protocols: {invalid_protocols}")
        
        # Business logic validation
        if asset_data.get('criticality') == 'CRITICAL' and not asset_data.get('description'):
            warnings.append("Critical assets should have detailed descriptions")
        
        # Check for duplicate names in the same analysis
        if 'analysis_id' in asset_data and 'name' in asset_data:
            existing = self.db_session.query(Asset).filter(
                and_(
                    Asset.analysis_id == asset_data['analysis_id'],
                    Asset.name == asset_data['name']
                )
            ).first()
            
            if existing:
                errors.append(f"Asset with name '{asset_data['name']}' already exists in this analysis")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def enhance_existing_assets(self, analysis_id: str) -> AssetAnalysisResult:
        """Enhance existing assets with AI capabilities.
        
        Args:
            analysis_id: ID of analysis to enhance assets for
            
        Returns:
            Enhancement results
        """
        try:
            logger.info(f"Enhancing existing assets for analysis {analysis_id}")
            
            # Get existing assets
            assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
            
            if not assets:
                return AssetAnalysisResult(
                    assets_processed=0,
                    enhancements_applied=0,
                    validation_issues=[],
                    recommendations=["No assets found to enhance"],
                    confidence_scores={}
                )
            
            # Prepare asset data for AI enhancement
            assets_data = [self._asset_to_dict(asset) for asset in assets]
            
            # Get AI enhancements
            enhanced_assets = await self.ai_orchestrator.enhance_assets_batch(assets_data)
            
            enhancements_applied = 0
            confidence_scores = {}
            
            # Apply enhancements
            for i, asset in enumerate(assets):
                if i < len(enhanced_assets):
                    enhanced_data = enhanced_assets[i]
                    
                    # Update asset with enhancements
                    if enhanced_data.get('description') and not asset.description:
                        asset.description = enhanced_data['description']
                        enhancements_applied += 1
                    
                    if enhanced_data.get('interfaces') and not asset.interfaces:
                        asset.interfaces = enhanced_data['interfaces']
                        enhancements_applied += 1
                    
                    # Store AI metadata
                    asset.metadata = asset.metadata or {}
                    asset.metadata['ai_enhanced'] = True
                    asset.metadata['enhancement_timestamp'] = datetime.now().isoformat()
                    
                    confidence_scores[asset.name] = enhanced_data.get('confidence_score', 0.8)
            
            self.db_session.commit()
            
            # Generate recommendations
            recommendations = await self._generate_asset_recommendations(analysis_id)
            
            return AssetAnalysisResult(
                assets_processed=len(assets),
                enhancements_applied=enhancements_applied,
                validation_issues=[],
                recommendations=recommendations,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to enhance existing assets: {str(e)}")
            raise AnalysisError(f"Asset enhancement failed: {str(e)}")
    
    def get_assets_by_analysis(self, analysis_id: str, filters: Dict[str, Any] = None) -> List[Asset]:
        """Get assets for analysis with optional filtering.
        
        Args:
            analysis_id: ID of analysis
            filters: Optional filters (asset_type, criticality, etc.)
            
        Returns:
            List of matching assets
        """
        query = self.db_session.query(Asset).filter_by(analysis_id=analysis_id)
        
        if filters:
            if 'asset_type' in filters:
                query = query.filter(Asset.asset_type == filters['asset_type'])
            
            if 'criticality' in filters:
                query = query.filter(Asset.criticality == filters['criticality'])
            
            if 'interfaces' in filters:
                # Filter assets that have any of the specified interfaces
                interface_filter = filters['interfaces']
                if isinstance(interface_filter, str):
                    interface_filter = [interface_filter]
                
                query = query.filter(
                    or_(*[Asset.interfaces.contains([interface]) for interface in interface_filter])
                )
        
        return query.all()
    
    def get_asset_statistics(self, analysis_id: str) -> Dict[str, Any]:
        """Get asset statistics for analysis.
        
        Args:
            analysis_id: ID of analysis
            
        Returns:
            Asset statistics and metrics
        """
        assets = self.get_assets_by_analysis(analysis_id)
        
        # Calculate statistics
        total_count = len(assets)
        type_counts = {}
        criticality_counts = {}
        interface_counts = {}
        
        for asset in assets:
            # Count by type
            asset_type = asset.asset_type or 'UNKNOWN'
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            # Count by criticality
            criticality = asset.criticality or 'MEDIUM'
            criticality_counts[criticality] = criticality_counts.get(criticality, 0) + 1
            
            # Count interfaces
            for interface in asset.interfaces or []:
                interface_counts[interface] = interface_counts.get(interface, 0) + 1
        
        return {
            'total_assets': total_count,
            'asset_types': type_counts,
            'criticality_levels': criticality_counts,
            'interface_usage': interface_counts,
            'has_descriptions': sum(1 for asset in assets if asset.description),
            'has_locations': sum(1 for asset in assets if asset.location),
            'ai_enhanced': sum(1 for asset in assets if asset.metadata and asset.metadata.get('ai_enhanced'))
        }
    
    async def _enhance_asset_data(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance asset data using AI capabilities."""
        # Use AI orchestrator to enhance individual asset
        enhanced = await self.ai_orchestrator.enhance_single_asset(asset_data)
        
        # Add confidence scoring
        enhanced['confidence_score'] = self._calculate_asset_confidence(enhanced)
        
        return enhanced
    
    def _calculate_asset_confidence(self, asset_data: Dict[str, Any]) -> float:
        """Calculate confidence score for asset definition."""
        score = 0.5  # Base score
        
        # Boost for required fields
        if asset_data.get('name'):
            score += 0.2
        if asset_data.get('asset_type'):
            score += 0.1
        
        # Boost for completeness
        if asset_data.get('description'):
            score += 0.1
        if asset_data.get('interfaces'):
            score += 0.05
        if asset_data.get('location'):
            score += 0.05
        
        # Boost for AI enhancement
        if asset_data.get('ai_enhancements'):
            score += 0.1
        
        return min(1.0, score)
    
    async def _generate_asset_recommendations(self, analysis_id: str) -> List[str]:
        """Generate recommendations for asset improvements."""
        assets = self.get_assets_by_analysis(analysis_id)
        recommendations = []
        
        # Check for missing descriptions on critical assets
        critical_without_desc = [a for a in assets 
                               if a.criticality == 'CRITICAL' and not a.description]
        if critical_without_desc:
            recommendations.append(f"Add descriptions to {len(critical_without_desc)} critical assets")
        
        # Check for assets without interfaces
        no_interfaces = [a for a in assets if not a.interfaces]
        if no_interfaces:
            recommendations.append(f"Define interfaces for {len(no_interfaces)} assets")
        
        # Check for potential duplicates
        names = [a.name.lower() for a in assets]
        duplicates = len(names) - len(set(names))
        if duplicates > 0:
            recommendations.append(f"Review {duplicates} potential duplicate asset names")
        
        # Use AI for additional recommendations
        ai_recommendations = await self.ai_orchestrator.recommend_asset_improvements(
            [self._asset_to_dict(asset) for asset in assets]
        )
        recommendations.extend(ai_recommendations)
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
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
            'manufacturer': asset.manufacturer,
            'metadata': asset.metadata or {}
        }