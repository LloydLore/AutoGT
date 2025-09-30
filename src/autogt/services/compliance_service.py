"""Compliance validation utilities for ISO/SAE 21434 per NFR-017.

Provides comprehensive compliance checking, validation rules, and audit trail
capabilities to ensure automotive cybersecurity compliance throughout TARA.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.analysis import TaraAnalysis
from ..models.asset import Asset
from ..models.threat import ThreatScenario
from ..models.risk import RiskAssessment
from ..models.treatment import TreatmentPlan
from ..core.exceptions import ValidationError, ComplianceError


logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Supported cybersecurity compliance standards."""
    ISO_SAE_21434 = "ISO_SAE_21434"
    UNECE_WP29 = "UNECE_WP29"
    ISO_27001 = "ISO_27001"
    NIST_CSF = "NIST_CSF"
    AUTOSAR = "AUTOSAR"


class ComplianceLevel(Enum):
    """Compliance assessment levels."""
    FULLY_COMPLIANT = "FULLY_COMPLIANT"
    MOSTLY_COMPLIANT = "MOSTLY_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"


@dataclass
class ComplianceRequirement:
    """Individual compliance requirement."""
    id: str
    standard: str
    section: str
    title: str
    description: str
    mandatory: bool
    validation_method: str
    evidence_required: List[str]


@dataclass
class ComplianceValidationResult:
    """Result of compliance validation check."""
    requirement_id: str
    compliant: bool
    confidence: float
    evidence_found: List[str]
    gaps_identified: List[str]
    recommendations: List[str]


@dataclass
class ComplianceAssessment:
    """Overall compliance assessment result."""
    standard: str
    analysis_id: str
    compliance_level: str
    overall_score: float
    requirements_total: int
    requirements_met: int
    critical_gaps: List[str]
    recommendations: List[str]
    assessment_date: datetime


class ComplianceValidatorService:
    """Service for automotive cybersecurity compliance validation."""
    
    def __init__(self, db_session: Session):
        """Initialize compliance validator service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        
        # ISO/SAE 21434 compliance requirements
        self.iso_sae_21434_requirements = [
            ComplianceRequirement(
                id="ISO_21434_5.4.1",
                standard="ISO_SAE_21434",
                section="5.4.1",
                title="Asset identification and categorization",
                description="All relevant assets must be identified and categorized",
                mandatory=True,
                validation_method="asset_inventory_check",
                evidence_required=["asset_list", "categorization_criteria", "asset_interfaces"]
            ),
            ComplianceRequirement(
                id="ISO_21434_5.4.2",
                standard="ISO_SAE_21434",
                section="5.4.2", 
                title="Threat scenario identification",
                description="Cybersecurity threats must be systematically identified",
                mandatory=True,
                validation_method="threat_coverage_check",
                evidence_required=["threat_model", "stride_coverage", "attack_vectors"]
            ),
            ComplianceRequirement(
                id="ISO_21434_5.4.3",
                standard="ISO_SAE_21434",
                section="5.4.3",
                title="Impact rating determination",
                description="Impact of threats must be rated considering safety, security, privacy",
                mandatory=True,
                validation_method="impact_assessment_check",
                evidence_required=["impact_ratings", "rating_methodology", "safety_analysis"]
            ),
            ComplianceRequirement(
                id="ISO_21434_5.4.4",
                standard="ISO_SAE_21434",
                section="5.4.4",
                title="Attack path analysis",
                description="Attack paths and feasibility must be analyzed",
                mandatory=True,
                validation_method="attack_path_check",
                evidence_required=["attack_paths", "feasibility_analysis", "attack_complexity"]
            ),
            ComplianceRequirement(
                id="ISO_21434_5.4.5",
                standard="ISO_SAE_21434",
                section="5.4.5",
                title="Risk determination",
                description="Risk levels must be calculated using standard risk matrix",
                mandatory=True,
                validation_method="risk_calculation_check",
                evidence_required=["risk_matrix", "risk_calculations", "risk_levels"]
            ),
            ComplianceRequirement(
                id="ISO_21434_6.4.1",
                standard="ISO_SAE_21434",
                section="6.4.1",
                title="Risk treatment decision",
                description="Risks must be treated through avoid, reduce, share, or retain",
                mandatory=True,
                validation_method="treatment_strategy_check",
                evidence_required=["treatment_decisions", "strategy_rationale", "residual_risk"]
            ),
            ComplianceRequirement(
                id="ISO_21434_6.4.2",
                standard="ISO_SAE_21434",
                section="6.4.2",
                title="Cybersecurity goals",
                description="Cybersecurity goals must be defined and linked to risks",
                mandatory=True,
                validation_method="cybersecurity_goals_check",
                evidence_required=["goals_definition", "risk_linkage", "goal_verification"]
            ),
            ComplianceRequirement(
                id="ISO_21434_7.4.1",
                standard="ISO_SAE_21434",
                section="7.4.1",
                title="Traceability",
                description="Full traceability from assets through risks to goals required",
                mandatory=True,
                validation_method="traceability_check",
                evidence_required=["traceability_matrix", "change_tracking", "version_control"]
            ),
            ComplianceRequirement(
                id="ISO_21434_8.2.1",
                standard="ISO_SAE_21434",
                section="8.2.1",
                title="Documentation",
                description="All cybersecurity activities must be documented",
                mandatory=True,
                validation_method="documentation_check",
                evidence_required=["tara_report", "analysis_documentation", "review_records"]
            ),
            ComplianceRequirement(
                id="ISO_21434_8.3.1",
                standard="ISO_SAE_21434",
                section="8.3.1",
                title="Review and approval",
                description="TARA must be reviewed and approved by competent personnel",
                mandatory=True,
                validation_method="review_approval_check",
                evidence_required=["review_records", "approval_signatures", "competency_evidence"]
            )
        ]
        
        # Validation methods mapping
        self.validation_methods = {
            "asset_inventory_check": self._validate_asset_inventory,
            "threat_coverage_check": self._validate_threat_coverage,
            "impact_assessment_check": self._validate_impact_assessment,
            "attack_path_check": self._validate_attack_paths,
            "risk_calculation_check": self._validate_risk_calculations,
            "treatment_strategy_check": self._validate_treatment_strategies,
            "cybersecurity_goals_check": self._validate_cybersecurity_goals,
            "traceability_check": self._validate_traceability,
            "documentation_check": self._validate_documentation,
            "review_approval_check": self._validate_review_approval
        }
        
        # Compliance scoring weights
        self.scoring_weights = {
            "mandatory_requirement": 10,
            "optional_requirement": 5,
            "critical_gap": -20,
            "major_gap": -10,
            "minor_gap": -2
        }
    
    def validate_full_compliance(self, analysis_id: str, 
                               standard: ComplianceStandard = ComplianceStandard.ISO_SAE_21434) -> ComplianceAssessment:
        """Perform comprehensive compliance validation for analysis.
        
        Args:
            analysis_id: ID of analysis to validate
            standard: Compliance standard to validate against
            
        Returns:
            Complete compliance assessment
        """
        try:
            logger.info(f"Starting compliance validation for analysis {analysis_id} against {standard.value}")
            
            # Get analysis data
            analysis = self.db_session.query(TaraAnalysis).filter_by(id=analysis_id).first()
            if not analysis:
                raise ValidationError(f"Analysis not found: {analysis_id}")
            
            # Select requirements based on standard
            if standard == ComplianceStandard.ISO_SAE_21434:
                requirements = self.iso_sae_21434_requirements
            else:
                raise ValidationError(f"Standard not supported: {standard.value}")
            
            # Validate each requirement
            validation_results = []
            total_score = 0
            max_possible_score = 0
            
            for requirement in requirements:
                try:
                    result = self._validate_requirement(analysis_id, requirement)
                    validation_results.append(result)
                    
                    # Calculate scoring
                    weight = self.scoring_weights["mandatory_requirement"] if requirement.mandatory else self.scoring_weights["optional_requirement"]
                    max_possible_score += weight
                    
                    if result.compliant:
                        total_score += weight
                    else:
                        # Deduct for gaps
                        if requirement.mandatory:
                            total_score += self.scoring_weights["critical_gap"]
                        else:
                            total_score += self.scoring_weights["major_gap"]
                    
                except Exception as e:
                    logger.warning(f"Failed to validate requirement {requirement.id}: {str(e)}")
                    # Treat validation failures as non-compliance
                    validation_results.append(ComplianceValidationResult(
                        requirement_id=requirement.id,
                        compliant=False,
                        confidence=0.0,
                        evidence_found=[],
                        gaps_identified=[f"Validation failed: {str(e)}"],
                        recommendations=[f"Fix validation issues for {requirement.title}"]
                    ))
            
            # Calculate overall compliance metrics
            requirements_met = sum(1 for result in validation_results if result.compliant)
            compliance_percentage = (requirements_met / len(requirements)) * 100 if requirements else 0
            
            # Determine compliance level
            compliance_level = self._determine_compliance_level(compliance_percentage)
            
            # Identify critical gaps
            critical_gaps = []
            recommendations = []
            
            for result in validation_results:
                if not result.compliant:
                    critical_gaps.extend(result.gaps_identified)
                    recommendations.extend(result.recommendations)
            
            # Remove duplicates
            critical_gaps = list(set(critical_gaps))
            recommendations = list(set(recommendations))
            
            return ComplianceAssessment(
                standard=standard.value,
                analysis_id=analysis_id,
                compliance_level=compliance_level.value,
                overall_score=compliance_percentage,
                requirements_total=len(requirements),
                requirements_met=requirements_met,
                critical_gaps=critical_gaps[:10],  # Top 10 critical gaps
                recommendations=recommendations[:10],  # Top 10 recommendations
                assessment_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Compliance validation failed for analysis {analysis_id}: {str(e)}")
            raise ComplianceError(f"Compliance validation failed: {str(e)}")
    
    def validate_specific_requirement(self, analysis_id: str, 
                                    requirement_id: str) -> ComplianceValidationResult:
        """Validate specific compliance requirement.
        
        Args:
            analysis_id: ID of analysis to validate
            requirement_id: Specific requirement ID to validate
            
        Returns:
            Validation result for specific requirement
        """
        # Find requirement
        requirement = None
        for req in self.iso_sae_21434_requirements:
            if req.id == requirement_id:
                requirement = req
                break
        
        if not requirement:
            raise ValidationError(f"Requirement not found: {requirement_id}")
        
        return self._validate_requirement(analysis_id, requirement)
    
    def get_compliance_gaps(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get detailed compliance gaps and recommendations.
        
        Args:
            analysis_id: ID of analysis to check
            
        Returns:
            List of compliance gaps with remediation guidance
        """
        assessment = self.validate_full_compliance(analysis_id)
        
        gaps = []
        for gap in assessment.critical_gaps:
            gaps.append({
                'gap_description': gap,
                'severity': 'HIGH' if 'mandatory' in gap.lower() else 'MEDIUM',
                'standard_reference': assessment.standard,
                'remediation_effort': self._estimate_remediation_effort(gap)
            })
        
        return gaps
    
    def generate_compliance_report(self, analysis_id: str) -> Dict[str, Any]:
        """Generate comprehensive compliance report.
        
        Args:
            analysis_id: ID of analysis to report on
            
        Returns:
            Detailed compliance report
        """
        assessment = self.validate_full_compliance(analysis_id)
        
        # Get analysis metadata
        analysis = self.db_session.query(TaraAnalysis).filter_by(id=analysis_id).first()
        
        # Get data counts for context
        assets_count = self.db_session.query(func.count(Asset.id)).filter_by(analysis_id=analysis_id).scalar()
        threats_count = self.db_session.query(func.count(ThreatScenario.id)).filter_by(analysis_id=analysis_id).scalar()
        risks_count = self.db_session.query(func.count(RiskAssessment.id)).filter_by(analysis_id=analysis_id).scalar()
        treatments_count = self.db_session.query(func.count(TreatmentPlan.id)).filter_by(analysis_id=analysis_id).scalar()
        
        return {
            'analysis_info': {
                'id': analysis_id,
                'name': analysis.name if analysis else 'Unknown',
                'created_at': analysis.created_at.isoformat() if analysis else None,
                'assets_count': assets_count,
                'threats_count': threats_count,
                'risks_count': risks_count,
                'treatments_count': treatments_count
            },
            'compliance_assessment': {
                'standard': assessment.standard,
                'compliance_level': assessment.compliance_level,
                'overall_score': assessment.overall_score,
                'requirements_met': f"{assessment.requirements_met}/{assessment.requirements_total}",
                'assessment_date': assessment.assessment_date.isoformat()
            },
            'gaps_and_recommendations': {
                'critical_gaps': assessment.critical_gaps,
                'recommendations': assessment.recommendations,
                'estimated_effort': self._estimate_total_remediation_effort(assessment.critical_gaps)
            },
            'next_steps': self._generate_next_steps(assessment)
        }
    
    def _validate_requirement(self, analysis_id: str, 
                            requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate individual compliance requirement."""
        validation_method = self.validation_methods.get(requirement.validation_method)
        
        if not validation_method:
            return ComplianceValidationResult(
                requirement_id=requirement.id,
                compliant=False,
                confidence=0.0,
                evidence_found=[],
                gaps_identified=[f"Validation method not implemented: {requirement.validation_method}"],
                recommendations=[f"Implement validation for {requirement.title}"]
            )
        
        return validation_method(analysis_id, requirement)
    
    def _validate_asset_inventory(self, analysis_id: str, 
                                requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate asset identification and categorization compliance."""
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check asset existence
        if not assets:
            gaps_identified.append("No assets defined in analysis")
            recommendations.append("Define system assets and components")
        else:
            evidence_found.append(f"Found {len(assets)} assets")
        
        # Check asset categorization
        uncategorized_assets = [a for a in assets if not a.asset_type or not a.criticality]
        if uncategorized_assets:
            gaps_identified.append(f"{len(uncategorized_assets)} assets lack proper categorization")
            recommendations.append("Categorize all assets by type and criticality")
        else:
            evidence_found.append("All assets are properly categorized")
        
        # Check interface documentation
        assets_without_interfaces = [a for a in assets if not a.interfaces]
        if assets_without_interfaces:
            gaps_identified.append(f"{len(assets_without_interfaces)} assets missing interface documentation")
            recommendations.append("Document asset interfaces and communication paths")
        else:
            evidence_found.append("Asset interfaces are documented")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.9 if compliant else max(0.3, 1.0 - len(gaps_identified) * 0.2)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_threat_coverage(self, analysis_id: str,
                                requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate threat scenario identification compliance."""
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check threat existence
        if not threats:
            gaps_identified.append("No threat scenarios identified")
            recommendations.append("Conduct systematic threat identification")
        else:
            evidence_found.append(f"Found {len(threats)} threat scenarios")
        
        # Check STRIDE coverage
        stride_categories = set(t.stride_category for t in threats if t.stride_category)
        expected_stride = {'SPOOFING', 'TAMPERING', 'REPUDIATION', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE'}
        missing_stride = expected_stride - stride_categories
        
        if missing_stride:
            gaps_identified.append(f"Missing STRIDE categories: {', '.join(missing_stride)}")
            recommendations.append("Ensure comprehensive STRIDE threat coverage")
        else:
            evidence_found.append("Complete STRIDE category coverage")
        
        # Check threat descriptions
        incomplete_threats = [t for t in threats if not t.description or len(t.description) < 20]
        if incomplete_threats:
            gaps_identified.append(f"{len(incomplete_threats)} threats have insufficient descriptions")
            recommendations.append("Provide detailed threat descriptions and attack vectors")
        else:
            evidence_found.append("Threats have adequate descriptions")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.85 if compliant else max(0.2, 1.0 - len(gaps_identified) * 0.25)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_impact_assessment(self, analysis_id: str,
                                  requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate impact rating determination compliance."""
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        if not threats:
            gaps_identified.append("No threats available for impact assessment")
            recommendations.append("Define threat scenarios before impact assessment")
            return ComplianceValidationResult(
                requirement_id=requirement.id,
                compliant=False,
                confidence=0.0,
                evidence_found=evidence_found,
                gaps_identified=gaps_identified,
                recommendations=recommendations
            )
        
        # Check impact ratings
        threats_without_impact = [t for t in threats if not t.impact_rating]
        if threats_without_impact:
            gaps_identified.append(f"{len(threats_without_impact)} threats missing impact ratings")
            recommendations.append("Assign impact ratings to all threat scenarios")
        else:
            evidence_found.append("All threats have impact ratings")
        
        # Check for safety impact consideration
        safety_considered = any('safety' in (t.description or '').lower() for t in threats)
        if not safety_considered:
            gaps_identified.append("Safety impact not explicitly considered")
            recommendations.append("Explicitly assess safety implications of threats")
        else:
            evidence_found.append("Safety impact considerations found")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.8 if compliant else max(0.3, 1.0 - len(gaps_identified) * 0.3)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_attack_paths(self, analysis_id: str,
                             requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate attack path analysis compliance."""
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        if not threats:
            gaps_identified.append("No threats available for attack path analysis")
            return ComplianceValidationResult(
                requirement_id=requirement.id,
                compliant=False,
                confidence=0.0,
                evidence_found=evidence_found,
                gaps_identified=gaps_identified,
                recommendations=["Define threat scenarios before attack path analysis"]
            )
        
        # Check for attack path documentation
        threats_with_paths = [t for t in threats if t.attack_vector or (t.metadata and 'attack_path' in t.metadata)]
        if len(threats_with_paths) < len(threats):
            missing_count = len(threats) - len(threats_with_paths)
            gaps_identified.append(f"{missing_count} threats missing attack path analysis")
            recommendations.append("Document attack paths and vectors for all threats")
        else:
            evidence_found.append("Attack paths documented for all threats")
        
        # Check feasibility analysis
        threats_with_feasibility = [t for t in threats if t.likelihood_rating or (t.metadata and 'feasibility' in t.metadata)]
        if len(threats_with_feasibility) < len(threats):
            missing_count = len(threats) - len(threats_with_feasibility)
            gaps_identified.append(f"{missing_count} threats missing feasibility analysis")
            recommendations.append("Analyze attack feasibility for all threat scenarios")
        else:
            evidence_found.append("Attack feasibility analyzed for all threats")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.75 if compliant else max(0.25, 1.0 - len(gaps_identified) * 0.25)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_risk_calculations(self, analysis_id: str,
                                  requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate risk determination compliance."""
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        if not risks:
            gaps_identified.append("No risk assessments found")
            recommendations.append("Perform risk calculations for identified threats")
        else:
            evidence_found.append(f"Found {len(risks)} risk assessments")
        
        # Check risk matrix usage
        risks_with_matrix = [r for r in risks if r.impact_rating and r.likelihood_rating and r.risk_level]
        if len(risks_with_matrix) < len(risks):
            missing_count = len(risks) - len(risks_with_matrix)
            gaps_identified.append(f"{missing_count} risks missing complete matrix calculations")
            recommendations.append("Apply standard risk matrix to all risk assessments")
        else:
            evidence_found.append("Risk matrix applied to all assessments")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.9 if compliant else max(0.4, 1.0 - len(gaps_identified) * 0.3)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_treatment_strategies(self, analysis_id: str,
                                    requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate risk treatment decisions compliance."""
        treatments = self.db_session.query(TreatmentPlan).filter_by(analysis_id=analysis_id).all()
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check treatment coverage
        high_risks = [r for r in risks if r.risk_level in ['HIGH', 'VERY_HIGH']]
        if high_risks and not treatments:
            gaps_identified.append("High risks identified but no treatment plans created")
            recommendations.append("Create treatment plans for high and very high risks")
        elif treatments:
            evidence_found.append(f"Found {len(treatments)} treatment plans")
        
        # Check treatment strategies
        valid_strategies = {'AVOID', 'MITIGATE', 'TRANSFER', 'ACCEPT'}
        invalid_strategies = [t for t in treatments if t.treatment_strategy not in valid_strategies]
        if invalid_strategies:
            gaps_identified.append(f"{len(invalid_strategies)} treatments have invalid strategies")
            recommendations.append("Use only valid treatment strategies: avoid, mitigate, transfer, accept")
        else:
            evidence_found.append("All treatments use valid strategies")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.8 if compliant else max(0.3, 1.0 - len(gaps_identified) * 0.25)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_cybersecurity_goals(self, analysis_id: str,
                                   requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate cybersecurity goals definition compliance."""
        analysis = self.db_session.query(TaraAnalysis).filter_by(id=analysis_id).first()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check if goals are documented (simplified check)
        if not analysis or not analysis.metadata or 'cybersecurity_goals' not in analysis.metadata:
            gaps_identified.append("Cybersecurity goals not documented")
            recommendations.append("Define and document cybersecurity goals")
        else:
            goals = analysis.metadata.get('cybersecurity_goals', [])
            if not goals:
                gaps_identified.append("No cybersecurity goals defined")
                recommendations.append("Define specific cybersecurity goals")
            else:
                evidence_found.append(f"Found {len(goals)} cybersecurity goals")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.7 if compliant else 0.2
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_traceability(self, analysis_id: str,
                             requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate traceability compliance."""
        # Check if all elements are linked
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis_id).all()
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis_id).all()
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis_id).all()
        treatments = self.db_session.query(TreatmentPlan).filter_by(analysis_id=analysis_id).all()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check threat-asset linkage
        threats_with_assets = [t for t in threats if t.target_assets]
        if len(threats_with_assets) < len(threats):
            missing_count = len(threats) - len(threats_with_assets)
            gaps_identified.append(f"{missing_count} threats not linked to assets")
            recommendations.append("Link all threats to their target assets")
        else:
            evidence_found.append("All threats linked to target assets")
        
        # Check risk-threat linkage
        risks_with_threats = [r for r in risks if r.threat_scenario_id]
        if len(risks_with_threats) < len(risks):
            missing_count = len(risks) - len(risks_with_threats)
            gaps_identified.append(f"{missing_count} risks not linked to threats")
            recommendations.append("Link all risks to their threat scenarios")
        else:
            evidence_found.append("All risks linked to threat scenarios")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.8 if compliant else max(0.3, 1.0 - len(gaps_identified) * 0.2)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_documentation(self, analysis_id: str,
                              requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate documentation compliance."""
        analysis = self.db_session.query(TaraAnalysis).filter_by(analysis_id=analysis_id).first()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        if not analysis:
            gaps_identified.append("Analysis record not found")
            recommendations.append("Ensure analysis is properly documented")
        else:
            evidence_found.append("Analysis record exists")
            
            # Check basic documentation
            if not analysis.description:
                gaps_identified.append("Analysis description missing")
                recommendations.append("Provide comprehensive analysis description")
            
            if not analysis.scope:
                gaps_identified.append("Analysis scope not documented")
                recommendations.append("Document analysis scope and boundaries")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.7 if compliant else max(0.2, 1.0 - len(gaps_identified) * 0.3)
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _validate_review_approval(self, analysis_id: str,
                                requirement: ComplianceRequirement) -> ComplianceValidationResult:
        """Validate review and approval compliance."""
        analysis = self.db_session.query(TaraAnalysis).filter_by(analysis_id=analysis_id).first()
        
        evidence_found = []
        gaps_identified = []
        recommendations = []
        
        # Check review status
        if not analysis or analysis.status != 'APPROVED':
            gaps_identified.append("Analysis not marked as reviewed and approved")
            recommendations.append("Complete formal review and approval process")
        else:
            evidence_found.append("Analysis marked as approved")
        
        # Check reviewer information
        if not analysis or not analysis.metadata or 'reviewers' not in analysis.metadata:
            gaps_identified.append("Reviewer information not documented")
            recommendations.append("Document reviewer qualifications and approval")
        
        compliant = len(gaps_identified) == 0
        confidence = 0.6 if compliant else 0.1
        
        return ComplianceValidationResult(
            requirement_id=requirement.id,
            compliant=compliant,
            confidence=confidence,
            evidence_found=evidence_found,
            gaps_identified=gaps_identified,
            recommendations=recommendations
        )
    
    def _determine_compliance_level(self, compliance_percentage: float) -> ComplianceLevel:
        """Determine compliance level based on percentage."""
        if compliance_percentage >= 95:
            return ComplianceLevel.FULLY_COMPLIANT
        elif compliance_percentage >= 80:
            return ComplianceLevel.MOSTLY_COMPLIANT
        elif compliance_percentage >= 60:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return ComplianceLevel.NON_COMPLIANT
    
    def _estimate_remediation_effort(self, gap: str) -> str:
        """Estimate effort required to remediate compliance gap."""
        if any(keyword in gap.lower() for keyword in ['missing', 'not found', 'no ']):
            return 'HIGH'
        elif any(keyword in gap.lower() for keyword in ['insufficient', 'incomplete', 'lack']):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _estimate_total_remediation_effort(self, gaps: List[str]) -> Dict[str, Any]:
        """Estimate total effort for all remediation activities."""
        effort_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for gap in gaps:
            effort = self._estimate_remediation_effort(gap)
            effort_counts[effort] += 1
        
        # Estimate total weeks based on effort distribution
        total_weeks = (effort_counts['HIGH'] * 4 + 
                      effort_counts['MEDIUM'] * 2 + 
                      effort_counts['LOW'] * 1)
        
        return {
            'total_gaps': len(gaps),
            'effort_distribution': effort_counts,
            'estimated_weeks': total_weeks,
            'estimated_cost_usd': total_weeks * 5000  # Rough estimate
        }
    
    def _generate_next_steps(self, assessment: ComplianceAssessment) -> List[str]:
        """Generate prioritized next steps for compliance improvement."""
        steps = []
        
        if assessment.compliance_level == ComplianceLevel.NON_COMPLIANT.value:
            steps.append("Address critical compliance gaps immediately")
            steps.append("Conduct comprehensive TARA review")
        elif assessment.compliance_level == ComplianceLevel.PARTIALLY_COMPLIANT.value:
            steps.append("Focus on mandatory requirement gaps")
            steps.append("Enhance documentation and traceability")
        elif assessment.compliance_level == ComplianceLevel.MOSTLY_COMPLIANT.value:
            steps.append("Complete remaining minor compliance items")
            steps.append("Prepare for formal compliance review")
        else:
            steps.append("Maintain compliance through regular reviews")
            steps.append("Consider compliance monitoring automation")
        
        return steps