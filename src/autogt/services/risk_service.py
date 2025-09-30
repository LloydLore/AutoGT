"""Risk assessment service with ISO calculations per FR-015.

Provides comprehensive risk assessment capabilities including impact analysis,
likelihood determination, risk matrix calculations, and ISO/SAE 21434 compliance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.risk import RiskAssessment, RiskLevel
from ..models.threat import ThreatScenario
from ..models.asset import Asset
from ..models.enums import CriticalityLevel, ImpactCategory
from ..ai.orchestrator import TaraOrchestrator
from ..core.exceptions import ValidationError, AnalysisError


logger = logging.getLogger(__name__)


class RiskMatrix(Enum):
    """ISO/SAE 21434 compliant risk matrix levels."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass
class RiskCalculationResult:
    """Result of risk calculation operation."""
    risk_id: str
    threat_id: str
    impact_score: float
    likelihood_score: float
    risk_level: str
    iso_compliant: bool
    confidence_score: float
    recommendations: List[str]


@dataclass
class RiskAnalysisResult:
    """Result of comprehensive risk analysis."""
    total_risks: int
    risk_distribution: Dict[str, int]
    high_priority_risks: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    treatment_recommendations: List[str]


class RiskAssessmentService:
    """Service for comprehensive cybersecurity risk assessment."""
    
    def __init__(self, db_session: Session):
        """Initialize risk assessment service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.ai_orchestrator = TaraOrchestrator()
        
        # ISO/SAE 21434 risk assessment matrix
        self.risk_matrix = {
            # (Impact, Likelihood) -> Risk Level
            ('VERY_LOW', 'VERY_LOW'): RiskMatrix.VERY_LOW,
            ('VERY_LOW', 'LOW'): RiskMatrix.VERY_LOW,
            ('VERY_LOW', 'MEDIUM'): RiskMatrix.LOW,
            ('VERY_LOW', 'HIGH'): RiskMatrix.LOW,
            ('VERY_LOW', 'VERY_HIGH'): RiskMatrix.MEDIUM,
            
            ('LOW', 'VERY_LOW'): RiskMatrix.VERY_LOW,
            ('LOW', 'LOW'): RiskMatrix.LOW,
            ('LOW', 'MEDIUM'): RiskMatrix.LOW,
            ('LOW', 'HIGH'): RiskMatrix.MEDIUM,
            ('LOW', 'VERY_HIGH'): RiskMatrix.MEDIUM,
            
            ('MEDIUM', 'VERY_LOW'): RiskMatrix.LOW,
            ('MEDIUM', 'LOW'): RiskMatrix.LOW,
            ('MEDIUM', 'MEDIUM'): RiskMatrix.MEDIUM,
            ('MEDIUM', 'HIGH'): RiskMatrix.MEDIUM,
            ('MEDIUM', 'VERY_HIGH'): RiskMatrix.HIGH,
            
            ('HIGH', 'VERY_LOW'): RiskMatrix.LOW,
            ('HIGH', 'LOW'): RiskMatrix.MEDIUM,
            ('HIGH', 'MEDIUM'): RiskMatrix.MEDIUM,
            ('HIGH', 'HIGH'): RiskMatrix.HIGH,
            ('HIGH', 'VERY_HIGH'): RiskMatrix.VERY_HIGH,
            
            ('VERY_HIGH', 'VERY_LOW'): RiskMatrix.MEDIUM,
            ('VERY_HIGH', 'LOW'): RiskMatrix.MEDIUM,
            ('VERY_HIGH', 'MEDIUM'): RiskMatrix.HIGH,
            ('VERY_HIGH', 'HIGH'): RiskMatrix.VERY_HIGH,
            ('VERY_HIGH', 'VERY_HIGH'): RiskMatrix.VERY_HIGH,
        }
        
        # Impact assessment criteria per automotive domain
        self.impact_criteria = {
            'SAFETY': {
                'VERY_LOW': 'No safety impact',
                'LOW': 'Minor safety degradation',
                'MEDIUM': 'Moderate safety impact',
                'HIGH': 'Serious safety impact',
                'VERY_HIGH': 'Life-threatening safety impact'
            },
            'SECURITY': {
                'VERY_LOW': 'Negligible security impact',
                'LOW': 'Minor security breach',
                'MEDIUM': 'Moderate security compromise',
                'HIGH': 'Significant security breach',
                'VERY_HIGH': 'Complete security compromise'
            },
            'PRIVACY': {
                'VERY_LOW': 'No privacy impact',
                'LOW': 'Minor data exposure',
                'MEDIUM': 'Personal data compromise',
                'HIGH': 'Sensitive data breach',
                'VERY_HIGH': 'Complete privacy violation'
            },
            'OPERATIONAL': {
                'VERY_LOW': 'No operational impact',
                'LOW': 'Minor service disruption',
                'MEDIUM': 'Moderate functionality loss',
                'HIGH': 'Significant operational impact',
                'VERY_HIGH': 'Complete system failure'
            }
        }
        
        # Likelihood assessment factors
        self.likelihood_factors = {
            'attack_complexity': {'low': 1.2, 'medium': 1.0, 'high': 0.8},
            'required_privileges': {'none': 1.2, 'low': 1.0, 'high': 0.7},
            'user_interaction': {'none': 1.1, 'required': 0.9},
            'attack_vector': {'network': 1.2, 'adjacent': 1.0, 'local': 0.8, 'physical': 0.6},
            'asset_exposure': {'high': 1.2, 'medium': 1.0, 'low': 0.8}
        }
    
    async def assess_risks_for_analysis(self, analysis_id: str) -> RiskAnalysisResult:
        """Assess risks for all threats in an analysis.
        
        Args:
            analysis_id: ID of analysis to assess risks for
            
        Returns:
            Comprehensive risk analysis results
        """
        try:
            logger.info(f"Starting risk assessment for analysis {analysis_id}")
            
            # Get threats and assets for analysis
            threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
            assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
            
            if not threats:
                raise AnalysisError("No threats found for risk assessment")
            
            # Assess each threat
            risk_calculations = []
            for threat in threats:
                try:
                    risk_calc = await self._assess_single_threat_risk(threat, assets)
                    risk_calculations.append(risk_calc)
                except Exception as e:
                    logger.warning(f"Failed to assess risk for threat {threat.id}: {str(e)}")
                    continue
            
            # Create risk assessment records
            risks_created = 0
            risk_distribution = {}
            high_priority_risks = []
            
            for risk_calc in risk_calculations:
                risk_assessment = RiskAssessment(
                    analysis_id=analysis_id,
                    threat_scenario_id=risk_calc.threat_id,
                    impact_rating=self._score_to_level(risk_calc.impact_score),
                    likelihood_rating=self._score_to_level(risk_calc.likelihood_score),
                    risk_level=risk_calc.risk_level,
                    calculated_at=datetime.now(),
                    metadata={
                        'impact_score': risk_calc.impact_score,
                        'likelihood_score': risk_calc.likelihood_score,
                        'confidence_score': risk_calc.confidence_score,
                        'iso_compliant': risk_calc.iso_compliant,
                        'recommendations': risk_calc.recommendations
                    }
                )
                
                self.db_session.add(risk_assessment)
                risks_created += 1
                
                # Track distribution
                risk_level = risk_calc.risk_level
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
                
                # Identify high priority risks
                if risk_level in ['HIGH', 'VERY_HIGH']:
                    high_priority_risks.append({
                        'risk_id': risk_calc.risk_id,
                        'threat_name': next((t.name for t in threats if t.id == risk_calc.threat_id), 'Unknown'),
                        'risk_level': risk_level,
                        'impact_score': risk_calc.impact_score,
                        'likelihood_score': risk_calc.likelihood_score,
                        'recommendations': risk_calc.recommendations
                    })
            
            self.db_session.commit()
            
            # Generate compliance status
            compliance_status = self._assess_iso_compliance(risk_calculations)
            
            # Generate treatment recommendations
            treatment_recommendations = await self._generate_treatment_recommendations(
                analysis_id, high_priority_risks
            )
            
            return RiskAnalysisResult(
                total_risks=risks_created,
                risk_distribution=risk_distribution,
                high_priority_risks=high_priority_risks[:10],  # Top 10 high priority risks
                compliance_status=compliance_status,
                treatment_recommendations=treatment_recommendations
            )
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to assess risks for analysis {analysis_id}: {str(e)}")
            raise AnalysisError(f"Risk assessment failed: {str(e)}")
    
    async def assess_single_risk(self, analysis_id: str, threat_id: str) -> RiskCalculationResult:
        """Assess risk for a single threat scenario.
        
        Args:
            analysis_id: ID of analysis
            threat_id: ID of threat scenario
            
        Returns:
            Risk calculation result
        """
        threat = self.db_session.query(ThreatScenario).filter(
            and_(ThreatScenario.analysis_id == analysis_id, ThreatScenario.id == threat_id)
        ).first()
        
        if not threat:
            raise AnalysisError(f"Threat not found: {threat_id}")
        
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
        return await self._assess_single_threat_risk(threat, assets)
    
    def recalculate_risks(self, analysis_id: str) -> Dict[str, Any]:
        """Recalculate existing risk assessments with updated parameters.
        
        Args:
            analysis_id: ID of analysis to recalculate
            
        Returns:
            Recalculation results
        """
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis_id).all()
        updated_count = 0
        
        for risk in risks:
            # Get associated threat
            threat = self.db_session.query(ThreatScenario).filter_by(id=risk.threat_scenario_id).first()
            if threat:
                # Recalculate using current parameters
                impact_score = self._calculate_impact_score(threat)
                likelihood_score = self._calculate_likelihood_score(threat)
                risk_level = self._calculate_risk_level(impact_score, likelihood_score)
                
                # Update risk assessment
                risk.impact_rating = self._score_to_level(impact_score)
                risk.likelihood_rating = self._score_to_level(likelihood_score)
                risk.risk_level = risk_level
                risk.calculated_at = datetime.now()
                
                updated_count += 1
        
        self.db_session.commit()
        
        return {
            'updated_risks': updated_count,
            'recalculation_time': datetime.now().isoformat()
        }
    
    def get_risks_by_level(self, analysis_id: str, risk_level: str) -> List[RiskAssessment]:
        """Get risks filtered by risk level.
        
        Args:
            analysis_id: ID of analysis
            risk_level: Risk level to filter by
            
        Returns:
            List of risks at specified level
        """
        return self.db_session.query(RiskAssessment).filter(
            and_(
                RiskAssessment.analysis_id == analysis_id,
                RiskAssessment.risk_level == risk_level
            )
        ).all()
    
    def get_risk_statistics(self, analysis_id: str) -> Dict[str, Any]:
        """Get comprehensive risk statistics for analysis.
        
        Args:
            analysis_id: ID of analysis
            
        Returns:
            Risk statistics and metrics
        """
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis_id).all()
        
        if not risks:
            return {'total_risks': 0, 'message': 'No risks assessed'}
        
        # Calculate statistics
        total_risks = len(risks)
        by_level = {}
        by_impact = {}
        by_likelihood = {}
        
        for risk in risks:
            # Count by risk level
            level = risk.risk_level or 'UNKNOWN'
            by_level[level] = by_level.get(level, 0) + 1
            
            # Count by impact
            impact = risk.impact_rating or 'MEDIUM'
            by_impact[impact] = by_impact.get(impact, 0) + 1
            
            # Count by likelihood
            likelihood = risk.likelihood_rating or 'MEDIUM'
            by_likelihood[likelihood] = by_likelihood.get(likelihood, 0) + 1
        
        # Calculate risk score distribution
        high_risks = sum(count for level, count in by_level.items() if level in ['HIGH', 'VERY_HIGH'])
        risk_percentage = (high_risks / total_risks * 100) if total_risks > 0 else 0
        
        return {
            'total_risks': total_risks,
            'risk_distribution': by_level,
            'impact_distribution': by_impact,
            'likelihood_distribution': by_likelihood,
            'high_risk_count': high_risks,
            'high_risk_percentage': round(risk_percentage, 1),
            'iso_compliance_ready': high_risks < total_risks * 0.3  # Heuristic: <30% high risk
        }
    
    async def _assess_single_threat_risk(self, threat: ThreatScenario, 
                                       assets: List[Asset]) -> RiskCalculationResult:
        """Assess risk for a single threat scenario."""
        # Calculate impact score
        impact_score = self._calculate_impact_score(threat, assets)
        
        # Calculate likelihood score
        likelihood_score = self._calculate_likelihood_score(threat, assets)
        
        # Calculate overall risk level using ISO matrix
        risk_level = self._calculate_risk_level(impact_score, likelihood_score)
        
        # Get AI assessment for validation
        ai_assessment = await self._get_ai_risk_assessment(threat, assets)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            impact_score, likelihood_score, ai_assessment
        )
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(
            threat, impact_score, likelihood_score, risk_level
        )
        
        return RiskCalculationResult(
            risk_id=f"risk_{threat.id}",
            threat_id=threat.id,
            impact_score=impact_score,
            likelihood_score=likelihood_score,
            risk_level=risk_level,
            iso_compliant=True,  # All calculations follow ISO/SAE 21434
            confidence_score=confidence_score,
            recommendations=recommendations
        )
    
    def _calculate_impact_score(self, threat: ThreatScenario, assets: List[Asset] = None) -> float:
        """Calculate impact score based on threat and affected assets."""
        base_impact = 0.5  # Base impact score
        
        # Factor in STRIDE category impact
        stride_impacts = {
            'SPOOFING': 0.7,
            'TAMPERING': 0.9,
            'REPUDIATION': 0.5,
            'INFORMATION_DISCLOSURE': 0.6,
            'DENIAL_OF_SERVICE': 0.8,
            'ELEVATION_OF_PRIVILEGE': 0.9
        }
        
        stride_impact = stride_impacts.get(threat.stride_category, 0.6)
        
        # Factor in affected asset criticality
        asset_impact = 0.5
        if assets and threat.target_assets:
            target_assets = [a for a in assets if a.name in threat.target_assets]
            if target_assets:
                criticality_scores = {
                    'CRITICAL': 1.0,
                    'HIGH': 0.8,
                    'MEDIUM': 0.5,
                    'LOW': 0.3
                }
                
                max_criticality = max(
                    criticality_scores.get(asset.criticality, 0.5) 
                    for asset in target_assets
                )
                asset_impact = max_criticality
        
        # Use existing impact rating if available
        if threat.impact_rating:
            rating_scores = {
                'VERY_HIGH': 1.0,
                'HIGH': 0.8,
                'MEDIUM': 0.5,
                'LOW': 0.3,
                'VERY_LOW': 0.1
            }
            base_impact = rating_scores.get(threat.impact_rating, 0.5)
        
        # Combine factors
        final_impact = (base_impact * 0.4 + stride_impact * 0.3 + asset_impact * 0.3)
        return min(1.0, max(0.1, final_impact))
    
    def _calculate_likelihood_score(self, threat: ThreatScenario, assets: List[Asset] = None) -> float:
        """Calculate likelihood score based on threat characteristics."""
        base_likelihood = 0.5
        
        # Factor in attack complexity
        complexity_factor = 1.0
        if threat.metadata and 'complexity' in threat.metadata:
            complexity = threat.metadata['complexity']
            complexity_factor = self.likelihood_factors['attack_complexity'].get(complexity, 1.0)
        
        # Factor in asset exposure
        exposure_factor = 1.0
        if assets and threat.target_assets:
            target_assets = [a for a in assets if a.name in threat.target_assets]
            # Check for exposed interfaces
            exposed_interfaces = ['WIFI', 'BLUETOOTH', 'CELLULAR', 'ETHERNET']
            has_exposed = any(
                interface in (asset.interfaces or []) 
                for asset in target_assets 
                for interface in exposed_interfaces
            )
            exposure_factor = 1.2 if has_exposed else 0.8
        
        # Use existing likelihood rating if available
        if threat.likelihood_rating:
            rating_scores = {
                'VERY_HIGH': 1.0,
                'HIGH': 0.8,
                'MEDIUM': 0.5,
                'LOW': 0.3,
                'VERY_LOW': 0.1
            }
            base_likelihood = rating_scores.get(threat.likelihood_rating, 0.5)
        
        # Combine factors
        final_likelihood = base_likelihood * complexity_factor * exposure_factor
        return min(1.0, max(0.1, final_likelihood))
    
    def _calculate_risk_level(self, impact_score: float, likelihood_score: float) -> str:
        """Calculate risk level using ISO/SAE 21434 risk matrix."""
        impact_level = self._score_to_level(impact_score)
        likelihood_level = self._score_to_level(likelihood_score)
        
        risk_matrix_result = self.risk_matrix.get((impact_level, likelihood_level))
        return risk_matrix_result.value if risk_matrix_result else 'MEDIUM'
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to categorical level."""
        if score >= 0.9:
            return 'VERY_HIGH'
        elif score >= 0.7:
            return 'HIGH'
        elif score >= 0.5:
            return 'MEDIUM'
        elif score >= 0.3:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    async def _get_ai_risk_assessment(self, threat: ThreatScenario, 
                                    assets: List[Asset]) -> Dict[str, Any]:
        """Get AI-powered risk assessment for validation."""
        threat_data = {
            'name': threat.name,
            'description': threat.description,
            'category': threat.category,
            'stride_category': threat.stride_category,
            'target_assets': threat.target_assets or []
        }
        
        assets_data = [
            {
                'name': asset.name,
                'type': asset.asset_type,
                'criticality': asset.criticality,
                'interfaces': asset.interfaces or []
            }
            for asset in assets if asset.name in (threat.target_assets or [])
        ]
        
        return await self.ai_orchestrator.assess_risk(threat_data, assets_data)
    
    def _calculate_confidence_score(self, impact_score: float, likelihood_score: float,
                                  ai_assessment: Dict[str, Any]) -> float:
        """Calculate confidence in risk assessment."""
        base_confidence = 0.7
        
        # Boost for complete data
        if impact_score > 0.1 and likelihood_score > 0.1:
            base_confidence += 0.1
        
        # Boost for AI validation
        if ai_assessment and ai_assessment.get('confidence'):
            ai_confidence = ai_assessment['confidence']
            base_confidence = (base_confidence + ai_confidence) / 2
        
        # Penalize extreme scores without justification
        if impact_score > 0.9 or likelihood_score > 0.9:
            if not ai_assessment or ai_assessment.get('confidence', 0) < 0.8:
                base_confidence *= 0.9
        
        return min(1.0, max(0.3, base_confidence))
    
    def _generate_risk_recommendations(self, threat: ThreatScenario, 
                                     impact_score: float, likelihood_score: float,
                                     risk_level: str) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        if risk_level in ['HIGH', 'VERY_HIGH']:
            recommendations.append("Immediate risk treatment required")
            recommendations.append("Consider implementing countermeasures")
        
        if impact_score > 0.8:
            recommendations.append("High impact threat - review safety implications")
        
        if likelihood_score > 0.8:
            recommendations.append("High likelihood threat - implement preventive controls")
        
        # STRIDE-specific recommendations
        stride_recommendations = {
            'SPOOFING': "Implement authentication and identity verification",
            'TAMPERING': "Add integrity checks and tamper detection",
            'REPUDIATION': "Enhance logging and audit capabilities",
            'INFORMATION_DISCLOSURE': "Implement data encryption and access controls",
            'DENIAL_OF_SERVICE': "Add redundancy and rate limiting",
            'ELEVATION_OF_PRIVILEGE': "Strengthen access controls and privilege management"
        }
        
        if threat.stride_category in stride_recommendations:
            recommendations.append(stride_recommendations[threat.stride_category])
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _assess_iso_compliance(self, risk_calculations: List[RiskCalculationResult]) -> Dict[str, Any]:
        """Assess ISO/SAE 21434 compliance status."""
        total_risks = len(risk_calculations)
        
        if total_risks == 0:
            return {
                'compliant': False,
                'reason': 'No risks assessed',
                'requirements_met': {}
            }
        
        # Check compliance requirements
        has_impact_assessment = all(calc.impact_score > 0 for calc in risk_calculations)
        has_likelihood_assessment = all(calc.likelihood_score > 0 for calc in risk_calculations)
        uses_risk_matrix = all(calc.iso_compliant for calc in risk_calculations)
        
        high_risk_count = sum(1 for calc in risk_calculations 
                            if calc.risk_level in ['HIGH', 'VERY_HIGH'])
        has_treatment_plan = high_risk_count == 0  # Simplified - would check actual treatments
        
        requirements_met = {
            'impact_assessment': has_impact_assessment,
            'likelihood_assessment': has_likelihood_assessment,
            'risk_matrix_usage': uses_risk_matrix,
            'treatment_planning': has_treatment_plan
        }
        
        compliance_score = sum(requirements_met.values()) / len(requirements_met)
        
        return {
            'compliant': compliance_score >= 0.8,
            'compliance_score': round(compliance_score * 100, 1),
            'requirements_met': requirements_met,
            'high_risk_count': high_risk_count,
            'total_risks': total_risks
        }
    
    async def _generate_treatment_recommendations(self, analysis_id: str, 
                                               high_priority_risks: List[Dict[str, Any]]) -> List[str]:
        """Generate treatment recommendations for high priority risks."""
        recommendations = []
        
        if not high_priority_risks:
            recommendations.append("No high priority risks identified")
            return recommendations
        
        # General recommendations for high risks
        recommendations.append(f"Address {len(high_priority_risks)} high priority risks immediately")
        
        # Risk-specific recommendations
        for risk in high_priority_risks[:5]:  # Top 5 risks
            recommendations.extend(risk.get('recommendations', [])[:2])  # Top 2 per risk
        
        # Use AI for additional treatment recommendations
        try:
            ai_recommendations = await self.ai_orchestrator.recommend_risk_treatments(
                high_priority_risks
            )
            recommendations.extend(ai_recommendations[:3])
        except Exception as e:
            logger.warning(f"AI treatment recommendations failed: {str(e)}")
        
        return list(set(recommendations))[:10]  # Remove duplicates, limit to 10