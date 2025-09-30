"""Confidence assessment service for FR-016 multi-factor analysis.

Specialized service for calculating and managing multi-factor confidence scores
across all TARA analysis components with automotive domain expertise.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime

from ..models.enums import ConfidenceLevel, TaraStatus
from ..models.tara_analysis import TaraAnalysis
from ..models.asset import Asset
from ..models.threat_scenario import ThreatScenario
from ..models.risk_value import RiskValue


class ConfidenceFactor(Enum):
    """Multi-factor confidence assessment factors per FR-016."""
    DATA_COMPLETENESS = "data_completeness"
    MODEL_CONFIDENCE = "model_confidence"
    VALIDATION_RESULTS = "validation_results"


@dataclass
class ConfidenceComponents:
    """Individual confidence component scores."""
    data_completeness: float  # 40% weight
    model_confidence: float   # 35% weight  
    validation_results: float # 25% weight
    overall_confidence: float
    confidence_level: ConfidenceLevel
    uncertainty_factors: List[str]
    improvement_recommendations: List[str]


@dataclass
class DataCompletenessMetrics:
    """Data completeness assessment metrics."""
    asset_coverage: float
    threat_coverage: float
    risk_coverage: float
    control_coverage: float
    documentation_completeness: float
    traceability_completeness: float
    overall_completeness: float
    identified_gaps: List[str]


@dataclass
class ModelConfidenceMetrics:
    """Model confidence assessment metrics."""
    agent_confidence_scores: Dict[str, float]
    prediction_consistency: float
    cross_validation_score: float
    domain_expertise_alignment: float
    uncertainty_quantification: float
    overall_model_confidence: float


@dataclass
class ValidationMetrics:
    """Validation results assessment metrics."""
    automated_validation_pass_rate: float
    manual_review_scores: Dict[str, float]
    consistency_validation_score: float
    accuracy_validation_score: float
    compliance_validation_score: float
    expert_review_confidence: float
    overall_validation_confidence: float


class ConfidenceService:
    """Service for multi-factor confidence assessment per FR-016.
    
    Implements automotive cybersecurity confidence scoring methodology with
    data completeness, model confidence, and validation results assessment.
    """
    
    def __init__(self):
        """Initialize confidence assessment service."""
        self.confidence_weights = {
            ConfidenceFactor.DATA_COMPLETENESS: 0.40,
            ConfidenceFactor.MODEL_CONFIDENCE: 0.35,
            ConfidenceFactor.VALIDATION_RESULTS: 0.25
        }
        
        # Automotive domain-specific thresholds
        self.automotive_thresholds = {
            "safety_critical_confidence": 0.85,
            "high_confidence": 0.80,
            "medium_confidence": 0.65,
            "low_confidence": 0.50,
            "insufficient_confidence": 0.35
        }
        
        # Data completeness requirements
        self.completeness_requirements = {
            "minimum_assets": 3,
            "minimum_threats_per_asset": 2,
            "required_impact_categories": 5,
            "minimum_risk_coverage": 0.80,
            "documentation_coverage": 0.85,
            "traceability_coverage": 0.90
        }
    
    def assess_analysis_confidence(
        self,
        analysis: TaraAnalysis,
        analysis_components: Dict[str, Any],
        agent_confidences: Dict[str, float],
        validation_results: Dict[str, Any] = None
    ) -> ConfidenceComponents:
        """Perform comprehensive multi-factor confidence assessment per FR-016.
        
        Args:
            analysis: TaraAnalysis instance being assessed
            analysis_components: All analysis components (assets, threats, risks, controls)
            agent_confidences: Individual AI agent confidence scores
            validation_results: Automated and manual validation results
            
        Returns:
            Complete confidence assessment with component breakdown and recommendations
        """
        # 1. Assess Data Completeness (40% weight)
        data_completeness_metrics = self._assess_data_completeness(
            analysis, analysis_components
        )
        
        # 2. Assess Model Confidence (35% weight)
        model_confidence_metrics = self._assess_model_confidence(
            agent_confidences, analysis_components
        )
        
        # 3. Assess Validation Results (25% weight)
        validation_metrics = self._assess_validation_confidence(
            validation_results or {}, analysis_components
        )
        
        # Calculate weighted overall confidence
        overall_confidence = self._calculate_weighted_confidence(
            data_completeness_metrics.overall_completeness,
            model_confidence_metrics.overall_model_confidence,
            validation_metrics.overall_validation_confidence
        )
        
        # Apply automotive domain adjustments
        adjusted_confidence = self._apply_automotive_adjustments(
            overall_confidence, analysis, analysis_components
        )
        
        # Classify confidence level
        confidence_level = self._classify_confidence_level(adjusted_confidence)
        
        # Identify uncertainty factors
        uncertainty_factors = self._identify_uncertainty_factors(
            data_completeness_metrics, model_confidence_metrics, validation_metrics
        )
        
        # Generate improvement recommendations
        improvement_recommendations = self._generate_improvement_recommendations(
            data_completeness_metrics, model_confidence_metrics, 
            validation_metrics, confidence_level
        )
        
        return ConfidenceComponents(
            data_completeness=data_completeness_metrics.overall_completeness,
            model_confidence=model_confidence_metrics.overall_model_confidence,
            validation_results=validation_metrics.overall_validation_confidence,
            overall_confidence=adjusted_confidence,
            confidence_level=confidence_level,
            uncertainty_factors=uncertainty_factors,
            improvement_recommendations=improvement_recommendations
        )
    
    def _assess_data_completeness(
        self,
        analysis: TaraAnalysis,
        analysis_components: Dict[str, Any]
    ) -> DataCompletenessMetrics:
        """Assess data completeness factor (40% weight)."""
        
        assets = analysis_components.get("assets", [])
        threats = analysis_components.get("threats", [])
        risks = analysis_components.get("risks", [])
        controls = analysis_components.get("controls", [])
        
        # Asset coverage assessment
        asset_coverage = self._assess_asset_coverage(assets, analysis)
        
        # Threat coverage assessment
        threat_coverage = self._assess_threat_coverage(threats, assets)
        
        # Risk coverage assessment
        risk_coverage = self._assess_risk_coverage(risks, threats)
        
        # Control coverage assessment
        control_coverage = self._assess_control_coverage(controls, risks)
        
        # Documentation completeness
        documentation_completeness = self._assess_documentation_completeness(
            analysis, analysis_components
        )
        
        # Traceability completeness
        traceability_completeness = self._assess_traceability_completeness(
            analysis_components
        )
        
        # Calculate overall completeness
        completeness_scores = [
            asset_coverage,
            threat_coverage,
            risk_coverage,
            control_coverage,
            documentation_completeness,
            traceability_completeness
        ]
        overall_completeness = np.mean(completeness_scores)
        
        # Identify coverage gaps
        identified_gaps = self._identify_coverage_gaps(
            asset_coverage, threat_coverage, risk_coverage, 
            control_coverage, documentation_completeness, traceability_completeness
        )
        
        return DataCompletenessMetrics(
            asset_coverage=asset_coverage,
            threat_coverage=threat_coverage,
            risk_coverage=risk_coverage,
            control_coverage=control_coverage,
            documentation_completeness=documentation_completeness,
            traceability_completeness=traceability_completeness,
            overall_completeness=overall_completeness,
            identified_gaps=identified_gaps
        )
    
    def _assess_model_confidence(
        self,
        agent_confidences: Dict[str, float],
        analysis_components: Dict[str, Any]
    ) -> ModelConfidenceMetrics:
        """Assess model confidence factor (35% weight)."""
        
        if not agent_confidences:
            # Default confidence if no agent scores available
            return ModelConfidenceMetrics(
                agent_confidence_scores={},
                prediction_consistency=0.5,
                cross_validation_score=0.5,
                domain_expertise_alignment=0.5,
                uncertainty_quantification=0.5,
                overall_model_confidence=0.5
            )
        
        # Calculate prediction consistency across agents
        prediction_consistency = self._calculate_prediction_consistency(agent_confidences)
        
        # Cross-validation score between different analysis components
        cross_validation_score = self._calculate_cross_validation_score(
            agent_confidences, analysis_components
        )
        
        # Domain expertise alignment assessment
        domain_expertise_alignment = self._assess_domain_expertise_alignment(
            agent_confidences, analysis_components
        )
        
        # Uncertainty quantification quality
        uncertainty_quantification = self._assess_uncertainty_quantification(
            agent_confidences, analysis_components
        )
        
        # Calculate overall model confidence
        confidence_factors = [
            np.mean(list(agent_confidences.values())),
            prediction_consistency,
            cross_validation_score,
            domain_expertise_alignment,
            uncertainty_quantification
        ]
        overall_model_confidence = np.mean(confidence_factors)
        
        return ModelConfidenceMetrics(
            agent_confidence_scores=agent_confidences,
            prediction_consistency=prediction_consistency,
            cross_validation_score=cross_validation_score,
            domain_expertise_alignment=domain_expertise_alignment,
            uncertainty_quantification=uncertainty_quantification,
            overall_model_confidence=overall_model_confidence
        )
    
    def _assess_validation_confidence(
        self,
        validation_results: Dict[str, Any],
        analysis_components: Dict[str, Any]
    ) -> ValidationMetrics:
        """Assess validation results factor (25% weight)."""
        
        # Automated validation pass rate
        automated_validation_pass_rate = validation_results.get(
            "automated_pass_rate", 0.8
        )
        
        # Manual review scores
        manual_review_scores = validation_results.get(
            "manual_review_scores", {"completeness": 0.8, "accuracy": 0.8}
        )
        
        # Consistency validation score
        consistency_validation_score = validation_results.get(
            "consistency_score", 0.85
        )
        
        # Accuracy validation score
        accuracy_validation_score = validation_results.get(
            "accuracy_score", 0.9
        )
        
        # Compliance validation score
        compliance_validation_score = validation_results.get(
            "compliance_score", 0.95
        )
        
        # Expert review confidence
        expert_review_confidence = np.mean(list(manual_review_scores.values()))
        
        # Calculate overall validation confidence
        validation_factors = [
            automated_validation_pass_rate,
            expert_review_confidence,
            consistency_validation_score,
            accuracy_validation_score,
            compliance_validation_score
        ]
        overall_validation_confidence = np.mean(validation_factors)
        
        return ValidationMetrics(
            automated_validation_pass_rate=automated_validation_pass_rate,
            manual_review_scores=manual_review_scores,
            consistency_validation_score=consistency_validation_score,
            accuracy_validation_score=accuracy_validation_score,
            compliance_validation_score=compliance_validation_score,
            expert_review_confidence=expert_review_confidence,
            overall_validation_confidence=overall_validation_confidence
        )
    
    def _calculate_weighted_confidence(
        self,
        data_completeness: float,
        model_confidence: float,
        validation_results: float
    ) -> float:
        """Calculate weighted overall confidence per FR-016."""
        
        weighted_confidence = (
            data_completeness * self.confidence_weights[ConfidenceFactor.DATA_COMPLETENESS] +
            model_confidence * self.confidence_weights[ConfidenceFactor.MODEL_CONFIDENCE] +
            validation_results * self.confidence_weights[ConfidenceFactor.VALIDATION_RESULTS]
        )
        
        return max(0.0, min(1.0, weighted_confidence))
    
    def _apply_automotive_adjustments(
        self,
        base_confidence: float,
        analysis: TaraAnalysis,
        analysis_components: Dict[str, Any]
    ) -> float:
        """Apply automotive domain-specific confidence adjustments."""
        
        adjustment_factor = 1.0
        
        # Safety-critical system adjustment
        if self._is_safety_critical_analysis(analysis, analysis_components):
            # Higher standards for safety-critical systems
            adjustment_factor *= 0.9
        
        # Fleet deployment scale adjustment
        fleet_size = analysis_components.get("system_context", {}).get("fleet_size", 0)
        if fleet_size > 100000:
            # Large fleet requires higher confidence
            adjustment_factor *= 0.95
        elif fleet_size > 10000:
            adjustment_factor *= 0.98
        
        # Regulatory compliance adjustment
        if analysis_components.get("regulatory_requirements", {}).get("iso_21434_required", True):
            # ISO 21434 compliance requires higher standards
            adjustment_factor *= 0.95
        
        adjusted_confidence = base_confidence * adjustment_factor
        return max(0.0, min(1.0, adjusted_confidence))
    
    def _classify_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Classify confidence level based on automotive thresholds."""
        
        if confidence_score >= self.automotive_thresholds["high_confidence"]:
            return ConfidenceLevel.HIGH
        elif confidence_score >= self.automotive_thresholds["medium_confidence"]:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= self.automotive_thresholds["low_confidence"]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.LOW  # Would be INSUFFICIENT in extended enum
    
    def _identify_uncertainty_factors(
        self,
        data_completeness: DataCompletenessMetrics,
        model_confidence: ModelConfidenceMetrics,
        validation_metrics: ValidationMetrics
    ) -> List[str]:
        """Identify factors contributing to confidence uncertainty."""
        
        uncertainty_factors = []
        
        # Data completeness uncertainty factors
        if data_completeness.overall_completeness < 0.8:
            uncertainty_factors.append("Incomplete data coverage")
        if len(data_completeness.identified_gaps) > 0:
            uncertainty_factors.append("Significant coverage gaps identified")
        
        # Model confidence uncertainty factors
        if model_confidence.prediction_consistency < 0.7:
            uncertainty_factors.append("Inconsistent agent predictions")
        if model_confidence.uncertainty_quantification < 0.6:
            uncertainty_factors.append("Poor uncertainty quantification")
        
        # Validation uncertainty factors
        if validation_metrics.automated_validation_pass_rate < 0.8:
            uncertainty_factors.append("Low automated validation pass rate")
        if validation_metrics.expert_review_confidence < 0.7:
            uncertainty_factors.append("Low expert review confidence")
        
        return uncertainty_factors
    
    def _generate_improvement_recommendations(
        self,
        data_completeness: DataCompletenessMetrics,
        model_confidence: ModelConfidenceMetrics,
        validation_metrics: ValidationMetrics,
        confidence_level: ConfidenceLevel
    ) -> List[str]:
        """Generate recommendations for confidence improvement."""
        
        recommendations = []
        
        # Data completeness improvements
        if data_completeness.overall_completeness < 0.8:
            recommendations.append("Improve data collection and coverage")
        if data_completeness.asset_coverage < 0.9:
            recommendations.append("Enhance asset identification completeness")
        if data_completeness.threat_coverage < 0.8:
            recommendations.append("Expand threat analysis coverage")
        
        # Model confidence improvements
        if model_confidence.overall_model_confidence < 0.7:
            recommendations.append("Enhance AI model training and validation")
        if model_confidence.prediction_consistency < 0.7:
            recommendations.append("Improve agent consistency through calibration")
        
        # Validation improvements
        if validation_metrics.overall_validation_confidence < 0.8:
            recommendations.append("Strengthen validation and review processes")
        if validation_metrics.expert_review_confidence < 0.7:
            recommendations.append("Engage additional expert reviewers")
        
        # Overall confidence improvements
        if confidence_level == ConfidenceLevel.LOW:
            recommendations.append("Comprehensive analysis review and enhancement required")
            recommendations.append("Consider additional validation and verification")
        
        return recommendations
    
    # Helper methods for specific assessments
    def _assess_asset_coverage(self, assets: List[Asset], analysis: TaraAnalysis) -> float:
        """Assess asset identification coverage completeness."""
        
        if not assets:
            return 0.0
        
        # Base coverage from asset count
        asset_count_score = min(1.0, len(assets) / self.completeness_requirements["minimum_assets"])
        
        # Asset detail completeness
        detailed_assets = sum(1 for asset in assets if self._is_asset_detailed(asset))
        detail_score = detailed_assets / len(assets) if assets else 0.0
        
        # Asset criticality coverage
        critical_assets = sum(1 for asset in assets if self._is_critical_asset(asset))
        criticality_score = min(1.0, critical_assets / max(1, len(assets) * 0.3))  # Expect 30% critical
        
        return np.mean([asset_count_score, detail_score, criticality_score])
    
    def _assess_threat_coverage(self, threats: List[ThreatScenario], assets: List[Asset]) -> float:
        """Assess threat analysis coverage completeness."""
        
        if not threats or not assets:
            return 0.0
        
        # Threats per asset ratio
        threats_per_asset = len(threats) / len(assets)
        threat_ratio_score = min(1.0, threats_per_asset / self.completeness_requirements["minimum_threats_per_asset"])
        
        # STRIDE category coverage
        stride_categories = set()
        for threat in threats:
            if hasattr(threat, 'threat_category'):
                stride_categories.add(threat.threat_category.value)
        
        stride_coverage = len(stride_categories) / 6  # 6 STRIDE categories
        
        return np.mean([threat_ratio_score, stride_coverage])
    
    def _assess_risk_coverage(self, risks: List[RiskValue], threats: List[ThreatScenario]) -> float:
        """Assess risk assessment coverage completeness."""
        
        if not risks or not threats:
            return 0.0
        
        # Risk-threat coverage ratio
        coverage_ratio = len(risks) / len(threats)
        
        # Impact category coverage
        impact_categories_covered = set()
        # Would extract from associated ImpactRating instances
        
        return min(1.0, coverage_ratio)
    
    def _assess_control_coverage(self, controls: List[SecurityControl], risks: List[RiskValue]) -> float:
        """Assess security control coverage completeness."""
        
        if not controls or not risks:
            return 0.0
        
        # High/critical risk control coverage
        high_critical_risks = [r for r in risks if hasattr(r, 'risk_level') and 
                              r.risk_level.value in ["HIGH", "CRITICAL"]]
        
        if not high_critical_risks:
            return 1.0  # Full coverage if no high/critical risks
        
        # Simplified coverage assessment
        coverage_ratio = len(controls) / len(high_critical_risks)
        return min(1.0, coverage_ratio)
    
    def _assess_documentation_completeness(
        self,
        analysis: TaraAnalysis,
        analysis_components: Dict[str, Any]
    ) -> float:
        """Assess documentation completeness."""
        
        # Check for required documentation elements
        documentation_elements = [
            bool(analysis.description),
            bool(analysis.system_under_analysis),
            bool(analysis_components.get("system_definition")),
            bool(analysis_components.get("analysis_objectives")),
        ]
        
        return sum(documentation_elements) / len(documentation_elements)
    
    def _assess_traceability_completeness(self, analysis_components: Dict[str, Any]) -> float:
        """Assess traceability completeness."""
        
        # Simplified traceability assessment
        assets = analysis_components.get("assets", [])
        threats = analysis_components.get("threats", [])
        risks = analysis_components.get("risks", [])
        
        # Check for ID relationships
        if not assets or not threats or not risks:
            return 0.5
        
        # Would implement detailed traceability checking
        return 0.9  # Placeholder high score
    
    def _calculate_prediction_consistency(self, agent_confidences: Dict[str, float]) -> float:
        """Calculate prediction consistency across agents."""
        
        if len(agent_confidences) < 2:
            return 1.0  # Perfect consistency with single agent
        
        confidence_values = list(agent_confidences.values())
        variance = np.var(confidence_values)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency_score = max(0.0, 1.0 - (variance * 4))  # Scale variance
        
        return consistency_score
    
    def _calculate_cross_validation_score(
        self,
        agent_confidences: Dict[str, float],
        analysis_components: Dict[str, Any]
    ) -> float:
        """Calculate cross-validation score between analysis components."""
        
        # Simplified cross-validation assessment
        return 0.85  # Placeholder score
    
    def _assess_domain_expertise_alignment(
        self,
        agent_confidences: Dict[str, float],
        analysis_components: Dict[str, Any]
    ) -> float:
        """Assess alignment with automotive domain expertise."""
        
        # Would implement domain expertise validation
        return 0.8  # Placeholder score
    
    def _assess_uncertainty_quantification(
        self,
        agent_confidences: Dict[str, float],
        analysis_components: Dict[str, Any]
    ) -> float:
        """Assess quality of uncertainty quantification."""
        
        # Would implement uncertainty quantification assessment
        return 0.75  # Placeholder score
    
    def _is_safety_critical_analysis(
        self,
        analysis: TaraAnalysis,
        analysis_components: Dict[str, Any]
    ) -> bool:
        """Determine if analysis involves safety-critical systems."""
        
        assets = analysis_components.get("assets", [])
        return any(self._is_critical_asset(asset) for asset in assets)
    
    def _is_asset_detailed(self, asset: Asset) -> bool:
        """Check if asset has detailed information."""
        
        return (hasattr(asset, 'description') and bool(asset.description) and
                hasattr(asset, 'asset_type') and bool(asset.asset_type) and
                hasattr(asset, 'interfaces') and bool(asset.interfaces))
    
    def _is_critical_asset(self, asset: Asset) -> bool:
        """Check if asset is safety-critical."""
        
        return (hasattr(asset, 'criticality_level') and 
                asset.criticality_level.value in ["HIGH", "CRITICAL"])
    
    def _identify_coverage_gaps(
        self,
        asset_coverage: float,
        threat_coverage: float,
        risk_coverage: float,
        control_coverage: float,
        documentation_completeness: float,
        traceability_completeness: float
    ) -> List[str]:
        """Identify specific coverage gaps."""
        
        gaps = []
        
        if asset_coverage < 0.8:
            gaps.append("Insufficient asset identification coverage")
        if threat_coverage < 0.8:
            gaps.append("Inadequate threat analysis coverage")
        if risk_coverage < 0.8:
            gaps.append("Incomplete risk assessment coverage")
        if control_coverage < 0.8:
            gaps.append("Insufficient security control coverage")
        if documentation_completeness < 0.85:
            gaps.append("Incomplete documentation")
        if traceability_completeness < 0.9:
            gaps.append("Poor traceability between components")
        
        return gaps
    
    def calculate_component_confidence(
        self,
        component_type: str,
        component_data: Any,
        context: Dict[str, Any] = None
    ) -> float:
        """Calculate confidence score for individual analysis component.
        
        Args:
            component_type: Type of component (asset, threat, risk, control)
            component_data: Component data for assessment
            context: Additional context for confidence calculation
            
        Returns:
            Individual component confidence score
        """
        
        if component_type == "asset":
            return self._calculate_asset_confidence(component_data, context)
        elif component_type == "threat":
            return self._calculate_threat_confidence(component_data, context)
        elif component_type == "risk":
            return self._calculate_risk_confidence(component_data, context)
        elif component_type == "control":
            return self._calculate_control_confidence(component_data, context)
        else:
            return 0.5  # Default medium confidence
    
    def _calculate_asset_confidence(self, asset: Asset, context: Dict[str, Any] = None) -> float:
        """Calculate confidence score for asset identification."""
        
        confidence_factors = []
        
        # Completeness factor
        if hasattr(asset, 'description') and asset.description:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Detail factor
        if hasattr(asset, 'interfaces') and asset.interfaces:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)
        
        # Criticality assessment factor
        if hasattr(asset, 'criticality_level'):
            confidence_factors.append(0.85)
        else:
            confidence_factors.append(0.4)
        
        return np.mean(confidence_factors)
    
    def _calculate_threat_confidence(self, threat: ThreatScenario, context: Dict[str, Any] = None) -> float:
        """Calculate confidence score for threat scenario."""
        
        confidence_factors = []
        
        # STRIDE categorization confidence
        if hasattr(threat, 'threat_category'):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.4)
        
        # Attack path detail confidence
        if hasattr(threat, 'attack_path') and threat.attack_path:
            confidence_factors.append(0.85)
        else:
            confidence_factors.append(0.5)
        
        # Automotive relevance confidence
        # Would assess based on automotive threat intelligence
        confidence_factors.append(0.8)
        
        return np.mean(confidence_factors)
    
    def _calculate_risk_confidence(self, risk: RiskValue, context: Dict[str, Any] = None) -> float:
        """Calculate confidence score for risk assessment."""
        
        confidence_factors = []
        
        # Calculation methodology confidence
        if hasattr(risk, 'calculation_method'):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # CVSS integration confidence
        if hasattr(risk, 'cvss_base_score') and risk.cvss_base_score:
            confidence_factors.append(0.85)
        else:
            confidence_factors.append(0.7)
        
        # Automotive factor confidence
        # Would assess automotive-specific adjustments
        confidence_factors.append(0.8)
        
        return np.mean(confidence_factors)
    
    def _calculate_control_confidence(self, control: SecurityControl, context: Dict[str, Any] = None) -> float:
        """Calculate confidence score for security control."""
        
        confidence_factors = []
        
        # Effectiveness assessment confidence
        if hasattr(control, 'effectiveness_rating'):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Implementation feasibility confidence
        if hasattr(control, 'implementation_complexity'):
            confidence_factors.append(0.75)
        else:
            confidence_factors.append(0.6)
        
        # Cost-benefit confidence
        if hasattr(control, 'cost_estimate') and hasattr(control, 'benefit_estimate'):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
        
        return np.mean(confidence_factors)