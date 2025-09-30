"""Risk Value model implementation per data-model.md specification lines 167-195."""

from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel, ISO21434Mixin
from .enums import RiskLevel, RiskStatus


class RiskValue(BaseModel, ISO21434Mixin):
    """Represents quantified cybersecurity risk assessments.
    
    Per data-model.md RiskValue entity specification with likelihood × impact
    risk calculation, CVSS integration, and risk treatment tracking.
    """
    
    __tablename__ = "risk_values"
    
    # Core risk assessment fields
    likelihood_score = Column(Float, nullable=False,
                            comment="Threat occurrence probability (0.0-10.0)")
    impact_score = Column(Float, nullable=False,
                         comment="Consequence severity score (0.0-10.0)")
    risk_score = Column(Float, nullable=False,
                       comment="Calculated risk value (likelihood × impact)")
    
    # Risk classification per data-model.md
    risk_level = Column(SQLEnum(RiskLevel), nullable=False,
                       comment="Risk classification: LOW, MEDIUM, HIGH, CRITICAL")
    risk_status = Column(SQLEnum(RiskStatus), 
                        default=RiskStatus.IDENTIFIED, nullable=False,
                        comment="Risk management state")
    
    # Risk calculation methodology
    calculation_method = Column(String(100), nullable=False, default='LIKELIHOOD_IMPACT',
                              comment="Risk calculation approach used")
    cvss_base_score = Column(Float, nullable=True,
                           comment="CVSS v3.1 base score if applicable")
    cvss_temporal_score = Column(Float, nullable=True,
                               comment="CVSS temporal score with exploit maturity")
    cvss_environmental_score = Column(Float, nullable=True,
                                    comment="CVSS environmental score for specific context")
    
    # Risk treatment tracking
    treatment_approach = Column(String(100), nullable=True,
                              comment="Risk treatment strategy: AVOID, MITIGATE, TRANSFER, ACCEPT")
    treatment_justification = Column(Text, nullable=True,
                                   comment="Rationale for selected treatment approach")
    residual_risk_score = Column(Float, nullable=True,
                               comment="Risk remaining after control implementation")
    
    # Assessment metadata
    assessment_date = Column(String(20), nullable=False,
                           comment="Date of risk assessment")
    assessor = Column(String(100), nullable=True,
                     comment="Person or system that performed assessment")
    review_date = Column(String(20), nullable=True,
                        comment="Next scheduled risk review date")
    
    # AI analysis integration per FR-012
    confidence_factors = Column(JSON, nullable=True,
                              comment="Multi-factor confidence breakdown")
    uncertainty_range = Column(JSON, nullable=True,
                             comment="Risk score uncertainty bounds")
    
    # Foreign key relationships
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False,
                     comment="Asset subject to risk")
    threat_scenario_id = Column(String(36), ForeignKey("threat_scenarios.id"), nullable=False,
                              comment="Threat scenario creating risk")
    analysis_id = Column(String(36), ForeignKey("tara_analyses.id"), nullable=False,
                        comment="Parent TARA analysis session")
    control_id = Column(String(36), ForeignKey("security_controls.id"), nullable=True,
                       comment="Control used for risk treatment (if applicable)")
    
    # Relationships per data-model.md relationship specifications
    asset = relationship("Asset", back_populates="risk_values")
    threat_scenario = relationship("ThreatScenario", back_populates="risk_values")
    analysis = relationship("TaraAnalysis", back_populates="risk_values")
    control = relationship("SecurityControl", back_populates="risk_values")
    
    def __repr__(self):
        return f"<RiskValue(id={self.id}, risk_score={self.risk_score}, level={self.risk_level}, status={self.risk_status})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate risk value per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Score range validation
        if not (0.0 <= self.likelihood_score <= 10.0):
            errors.append("Likelihood score must be between 0.0 and 10.0")
        if not (0.0 <= self.impact_score <= 10.0):
            errors.append("Impact score must be between 0.0 and 10.0")
        if not (0.0 <= self.risk_score <= 100.0):
            errors.append("Risk score must be between 0.0 and 100.0")
            
        # Risk score calculation validation
        expected_risk = self.likelihood_score * self.impact_score
        if abs(self.risk_score - expected_risk) > 0.1:
            errors.append("Risk score should equal likelihood × impact")
            
        # Risk level alignment validation
        level_thresholds = {
            RiskLevel.LOW: (0.0, 25.0),
            RiskLevel.MEDIUM: (25.0, 50.0),
            RiskLevel.HIGH: (50.0, 75.0),
            RiskLevel.CRITICAL: (75.0, 100.0)
        }
        
        min_risk, max_risk = level_thresholds.get(self.risk_level, (0.0, 100.0))
        if not (min_risk <= self.risk_score <= max_risk):
            errors.append(f"{self.risk_level.value} risk level requires score between {min_risk} and {max_risk}")
            
        # CVSS score validation
        for cvss_field in [self.cvss_base_score, self.cvss_temporal_score, self.cvss_environmental_score]:
            if cvss_field is not None and not (0.0 <= cvss_field <= 10.0):
                errors.append("CVSS scores must be between 0.0 and 10.0")
                
        # Residual risk validation
        if self.residual_risk_score is not None:
            if not (0.0 <= self.residual_risk_score <= 100.0):
                errors.append("Residual risk score must be between 0.0 and 100.0")
            if self.residual_risk_score > self.risk_score:
                errors.append("Residual risk cannot exceed original risk score")
                
        # Treatment approach validation
        valid_treatments = ['AVOID', 'MITIGATE', 'TRANSFER', 'ACCEPT']
        if self.treatment_approach and self.treatment_approach not in valid_treatments:
            errors.append(f"Treatment approach must be one of: {valid_treatments}")
            
        return len(errors) == 0, errors
    
    def calculate_risk_level(self) -> RiskLevel:
        """Calculate risk level based on risk score per data-model.md thresholds."""
        if self.risk_score >= 75.0:
            return RiskLevel.CRITICAL
        elif self.risk_score >= 50.0:
            return RiskLevel.HIGH
        elif self.risk_score >= 25.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def update_risk_calculation(self, likelihood: float, impact: float) -> None:
        """Update risk calculation and derived fields.
        
        Args:
            likelihood: New likelihood score (0.0-10.0)
            impact: New impact score (0.0-10.0)
        """
        self.likelihood_score = likelihood
        self.impact_score = impact
        self.risk_score = likelihood * impact
        self.risk_level = self.calculate_risk_level()
    
    def calculate_cvss_base_from_components(self, attack_vector: str, attack_complexity: str,
                                          privileges_required: str = 'NONE', user_interaction: str = 'NONE',
                                          scope: str = 'UNCHANGED', confidentiality: str = 'HIGH',
                                          integrity: str = 'HIGH', availability: str = 'HIGH') -> float:
        """Calculate CVSS v3.1 base score from component metrics.
        
        Simplified CVSS calculation for automotive cybersecurity context.
        """
        # Exploitability metrics (0-10 scale)
        av_scores = {'NETWORK': 0.85, 'ADJACENT': 0.62, 'LOCAL': 0.55, 'PHYSICAL': 0.2}
        ac_scores = {'LOW': 0.77, 'HIGH': 0.44}
        pr_scores = {'NONE': 0.85, 'LOW': 0.62, 'HIGH': 0.27}
        ui_scores = {'NONE': 0.85, 'REQUIRED': 0.62}
        
        exploitability = 8.22 * av_scores.get(attack_vector, 0.85) * \
                        ac_scores.get(attack_complexity, 0.77) * \
                        pr_scores.get(privileges_required, 0.85) * \
                        ui_scores.get(user_interaction, 0.85)
        
        # Impact metrics
        cia_scores = {'NONE': 0.0, 'LOW': 0.22, 'HIGH': 0.56}
        c_impact = cia_scores.get(confidentiality, 0.56)
        i_impact = cia_scores.get(integrity, 0.56)
        a_impact = cia_scores.get(availability, 0.56)
        
        impact_sub_score = 1 - ((1 - c_impact) * (1 - i_impact) * (1 - a_impact))
        
        if scope == 'UNCHANGED':
            impact = 6.42 * impact_sub_score
        else:
            impact = 7.52 * (impact_sub_score - 0.029) - 3.25 * (impact_sub_score - 0.02) ** 15
        
        # Base score calculation
        if impact <= 0:
            base_score = 0.0
        elif scope == 'UNCHANGED':
            base_score = min(10.0, impact + exploitability)
        else:
            base_score = min(10.0, 1.08 * (impact + exploitability))
        
        # Round to one decimal place
        self.cvss_base_score = round(base_score, 1)
        return self.cvss_base_score
    
    def assess_risk_treatment_options(self) -> Dict[str, Any]:
        """Assess available risk treatment options based on risk level and context."""
        treatment_options = []
        
        # Risk avoidance (eliminate the risk source)
        if self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            treatment_options.append({
                'approach': 'AVOID',
                'description': 'Eliminate risk source through design changes',
                'effectiveness': 1.0,
                'feasibility': 0.3,  # Often difficult to implement
                'cost_estimate': 'HIGH'
            })
        
        # Risk mitigation (reduce likelihood or impact)
        treatment_options.append({
            'approach': 'MITIGATE',
            'description': 'Implement security controls to reduce risk',
            'effectiveness': 0.7,
            'feasibility': 0.8,
            'cost_estimate': 'MEDIUM'
        })
        
        # Risk transfer (insurance, third-party responsibility)
        if self.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            treatment_options.append({
                'approach': 'TRANSFER',
                'description': 'Transfer risk through insurance or contracts',
                'effectiveness': 0.5,
                'feasibility': 0.6,
                'cost_estimate': 'LOW'
            })
        
        # Risk acceptance (acknowledge and monitor)
        if self.risk_level == RiskLevel.LOW:
            treatment_options.append({
                'approach': 'ACCEPT',
                'description': 'Accept residual risk with monitoring',
                'effectiveness': 0.0,
                'feasibility': 1.0,
                'cost_estimate': 'VERY_LOW'
            })
        
        return {
            'recommended_approach': treatment_options[0]['approach'] if treatment_options else 'MITIGATE',
            'treatment_options': treatment_options,
            'urgency': 'IMMEDIATE' if self.risk_level == RiskLevel.CRITICAL else 
                      'HIGH' if self.risk_level == RiskLevel.HIGH else 'MEDIUM'
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling and calculated fields."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.risk_level:
            result['risk_level'] = self.risk_level.value
        if self.risk_status:
            result['risk_status'] = self.risk_status.value
            
        # Include calculated fields
        result['treatment_options'] = self.assess_risk_treatment_options()
        
        return result
    
    @classmethod
    def from_likelihood_impact(cls, likelihood: float, impact: float, 
                             asset_id: str, threat_scenario_id: str, analysis_id: str,
                             assessor: str = 'AI_SYSTEM') -> 'RiskValue':
        """Create RiskValue from likelihood and impact scores.
        
        Args:
            likelihood: Threat likelihood score (0.0-10.0)
            impact: Impact severity score (0.0-10.0)
            asset_id: Target asset ID
            threat_scenario_id: Associated threat scenario ID
            analysis_id: Parent analysis ID
            assessor: Assessment source identifier
        """
        risk_score = likelihood * impact
        risk_level = RiskLevel.CRITICAL if risk_score >= 75.0 else \
                    RiskLevel.HIGH if risk_score >= 50.0 else \
                    RiskLevel.MEDIUM if risk_score >= 25.0 else RiskLevel.LOW
        
        return cls(
            likelihood_score=likelihood,
            impact_score=impact,
            risk_score=risk_score,
            risk_level=risk_level,
            calculation_method='LIKELIHOOD_IMPACT',
            assessment_date='2024-01-01',  # Would be set to current date
            assessor=assessor,
            asset_id=asset_id,
            threat_scenario_id=threat_scenario_id,
            analysis_id=analysis_id,
            iso_section='6.4.5'  # ISO/SAE 21434 risk assessment section
        )