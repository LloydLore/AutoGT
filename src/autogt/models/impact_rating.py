"""Impact Rating model implementation per data-model.md specification lines 136-166."""

from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel, ISO21434Mixin
from .enums import ImpactCategory, ImpactSeverity, ConfidenceLevel


class ImpactRating(BaseModel, ISO21434Mixin):
    """Represents cybersecurity impact assessment for threat scenarios.
    
    Per data-model.md ImpactRating entity specification with multi-dimensional
    impact assessment covering safety, financial, operational, privacy, and reputation.
    """
    
    __tablename__ = "impact_ratings"
    
    # Impact categorization per data-model.md
    impact_category = Column(SQLEnum(ImpactCategory), nullable=False,
                           comment="Impact domain: SAFETY, FINANCIAL, OPERATIONAL, PRIVACY, REPUTATION")
    impact_severity = Column(SQLEnum(ImpactSeverity), nullable=False,
                           comment="Severity level: NEGLIGIBLE, MINOR, MAJOR, SEVERE, CATASTROPHIC")
    
    # Quantitative impact assessment
    impact_score = Column(Float, nullable=False,
                         comment="Numerical impact score (0.0-10.0)")
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False,
                            comment="Assessment confidence: LOW, MEDIUM, HIGH")
    
    # Detailed impact analysis
    impact_description = Column(Text, nullable=True,
                              comment="Detailed description of potential impact")
    affected_stakeholders = Column(JSON, nullable=True,
                                 comment="List of stakeholders affected by this impact")
    impact_timeline = Column(String(100), nullable=True,
                           comment="Expected timeline for impact realization")
    
    # Quantitative metrics per impact category
    financial_impact = Column(Float, nullable=True,
                            comment="Estimated financial loss in currency units")
    safety_impact_scope = Column(String(100), nullable=True,
                               comment="Scope of safety impact (e.g., 'single vehicle', 'fleet-wide')")
    operational_downtime = Column(Float, nullable=True,
                                comment="Expected system downtime in hours")
    
    # Regulatory and compliance implications
    regulatory_violations = Column(JSON, nullable=True,
                                 comment="List of potential regulatory violations")
    compliance_impact = Column(Text, nullable=True,
                             comment="Impact on regulatory compliance status")
    
    # AI assessment metadata per FR-009, FR-012
    assessment_methodology = Column(String(100), nullable=True,
                                  comment="Method used for impact assessment")
    confidence_score = Column(Float, nullable=True,
                            comment="AI assessment confidence (0.0-1.0)")
    
    # Foreign key relationships
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False,
                     comment="Asset experiencing the impact")
    threat_scenario_id = Column(String(36), ForeignKey("threat_scenarios.id"), nullable=False,
                              comment="Threat scenario causing the impact")
    analysis_id = Column(String(36), ForeignKey("tara_analyses.id"), nullable=False,
                        comment="Parent TARA analysis session")
    
    # Relationships per data-model.md relationship specifications
    asset = relationship("Asset", back_populates="impact_ratings")
    threat_scenario = relationship("ThreatScenario", back_populates="impact_ratings")
    analysis = relationship("TaraAnalysis", back_populates="impact_ratings")
    
    def __repr__(self):
        return f"<ImpactRating(id={self.id}, category={self.impact_category}, severity={self.impact_severity}, score={self.impact_score})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate impact rating per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Impact score must align with severity level
        severity_ranges = {
            ImpactSeverity.NEGLIGIBLE: (0.0, 2.0),
            ImpactSeverity.MINOR: (2.0, 4.0),
            ImpactSeverity.MAJOR: (4.0, 6.0),
            ImpactSeverity.SEVERE: (6.0, 8.0),
            ImpactSeverity.CATASTROPHIC: (8.0, 10.0)
        }
        
        min_score, max_score = severity_ranges.get(self.impact_severity, (0.0, 10.0))
        if not (min_score <= self.impact_score <= max_score):
            errors.append(f"{self.impact_severity.value} severity requires impact score between {min_score} and {max_score}")
            
        # Impact score range validation
        if not (0.0 <= self.impact_score <= 10.0):
            errors.append("Impact score must be between 0.0 and 10.0")
            
        # Financial impact validation for FINANCIAL category
        if self.impact_category == ImpactCategory.FINANCIAL:
            if self.financial_impact is None:
                errors.append("Financial impact category requires financial_impact value")
            elif self.financial_impact < 0:
                errors.append("Financial impact cannot be negative")
                
        # Safety impact validation for SAFETY category
        if self.impact_category == ImpactCategory.SAFETY:
            if not self.safety_impact_scope:
                errors.append("Safety impact category requires safety_impact_scope")
                
        # Operational downtime validation for OPERATIONAL category
        if self.impact_category == ImpactCategory.OPERATIONAL:
            if self.operational_downtime is not None and self.operational_downtime < 0:
                errors.append("Operational downtime cannot be negative")
                
        # Confidence score validation per FR-012
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                errors.append("Confidence score must be between 0.0 and 1.0")
                
        return len(errors) == 0, errors
    
    def calculate_normalized_impact(self) -> float:
        """Calculate normalized impact score accounting for confidence level.
        
        Adjusts raw impact score based on assessment confidence per FR-012.
        """
        confidence_multipliers = {
            ConfidenceLevel.LOW: 0.7,
            ConfidenceLevel.MEDIUM: 0.9,
            ConfidenceLevel.HIGH: 1.0
        }
        
        multiplier = confidence_multipliers.get(self.confidence_level, 0.9)
        return self.impact_score * multiplier
    
    def assess_regulatory_risk(self) -> Dict[str, Any]:
        """Assess regulatory compliance risk based on impact category and severity.
        
        Returns regulatory risk assessment with violation likelihood and penalties.
        """
        # Base regulatory risk by impact category
        category_risk_levels = {
            ImpactCategory.SAFETY: 0.9,      # High regulatory scrutiny
            ImpactCategory.PRIVACY: 0.8,     # GDPR/privacy regulations
            ImpactCategory.OPERATIONAL: 0.4, # Moderate regulatory concern
            ImpactCategory.FINANCIAL: 0.3,   # Lower direct regulatory risk
            ImpactCategory.REPUTATION: 0.2   # Mainly business risk
        }
        
        # Severity multipliers
        severity_multipliers = {
            ImpactSeverity.NEGLIGIBLE: 0.1,
            ImpactSeverity.MINOR: 0.3,
            ImpactSeverity.MAJOR: 0.6,
            ImpactSeverity.SEVERE: 0.8,
            ImpactSeverity.CATASTROPHIC: 1.0
        }
        
        base_risk = category_risk_levels.get(self.impact_category, 0.5)
        severity_factor = severity_multipliers.get(self.impact_severity, 0.5)
        regulatory_risk_score = base_risk * severity_factor
        
        # Estimate potential penalties based on regulatory violations
        penalty_estimate = 0.0
        if self.regulatory_violations:
            violation_penalties = {
                'ISO_21434': 50000,    # Automotive cybersecurity standard violations
                'GDPR': 100000,        # Privacy regulation violations
                'UNECE_WP29': 75000,   # Vehicle type approval violations
                'NHTSA': 30000         # US automotive safety violations
            }
            
            for violation in self.regulatory_violations:
                penalty_estimate += violation_penalties.get(violation, 10000)
        
        return {
            'regulatory_risk_score': regulatory_risk_score,
            'violation_likelihood': min(1.0, regulatory_risk_score * 1.2),
            'estimated_penalties': penalty_estimate,
            'compliance_urgency': 'HIGH' if regulatory_risk_score > 0.7 else 'MEDIUM' if regulatory_risk_score > 0.4 else 'LOW'
        }
    
    def calculate_business_impact_score(self) -> float:
        """Calculate comprehensive business impact score combining multiple factors."""
        # Base impact score
        base_score = self.impact_score
        
        # Category-specific adjustments
        category_weights = {
            ImpactCategory.SAFETY: 1.2,      # Higher weight for safety impacts
            ImpactCategory.FINANCIAL: 1.0,   # Direct financial impact
            ImpactCategory.OPERATIONAL: 0.8, # Operational disruption
            ImpactCategory.PRIVACY: 0.9,     # Privacy/legal implications
            ImpactCategory.REPUTATION: 0.7   # Reputation damage
        }
        
        weight = category_weights.get(self.impact_category, 1.0)
        weighted_score = base_score * weight
        
        # Confidence adjustment
        confidence_adjustment = self.calculate_normalized_impact() / self.impact_score
        
        return min(10.0, weighted_score * confidence_adjustment)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling and calculated fields."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.impact_category:
            result['impact_category'] = self.impact_category.value
        if self.impact_severity:
            result['impact_severity'] = self.impact_severity.value
        if self.confidence_level:
            result['confidence_level'] = self.confidence_level.value
            
        # Include calculated fields
        result['normalized_impact'] = self.calculate_normalized_impact()
        result['business_impact_score'] = self.calculate_business_impact_score()
        result['regulatory_risk'] = self.assess_regulatory_risk()
        
        return result
    
    @classmethod
    def from_impact_analysis(cls, impact_data: Dict[str, Any], asset_id: str, 
                           threat_scenario_id: str, analysis_id: str) -> 'ImpactRating':
        """Create ImpactRating from automated impact analysis results.
        
        Args:
            impact_data: Impact analysis output
            asset_id: Target asset ID
            threat_scenario_id: Associated threat scenario ID
            analysis_id: Parent analysis ID
        """
        return cls(
            impact_category=ImpactCategory(impact_data.get('category')),
            impact_severity=ImpactSeverity(impact_data.get('severity')),
            impact_score=impact_data.get('score', 5.0),
            confidence_level=ConfidenceLevel(impact_data.get('confidence_level', 'MEDIUM')),
            impact_description=impact_data.get('description'),
            affected_stakeholders=impact_data.get('stakeholders', []),
            impact_timeline=impact_data.get('timeline'),
            financial_impact=impact_data.get('financial_loss'),
            safety_impact_scope=impact_data.get('safety_scope'),
            operational_downtime=impact_data.get('downtime_hours'),
            regulatory_violations=impact_data.get('regulatory_violations', []),
            compliance_impact=impact_data.get('compliance_description'),
            assessment_methodology=impact_data.get('methodology', 'AI_ANALYSIS'),
            confidence_score=impact_data.get('ai_confidence', 0.8),
            asset_id=asset_id,
            threat_scenario_id=threat_scenario_id,
            analysis_id=analysis_id,
            iso_section='6.4.4'  # ISO/SAE 21434 impact assessment section
        )