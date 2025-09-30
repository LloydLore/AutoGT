"""Security Control model implementation per data-model.md specification lines 100-135."""

from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Text, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel, ISO21434Mixin
from .enums import ControlType, ControlEffectiveness, ImplementationStatus, ReviewStatus


class SecurityControl(BaseModel, ISO21434Mixin):
    """Represents cybersecurity controls for threat mitigation.
    
    Per data-model.md SecurityControl entity specification with control effectiveness
    assessment, implementation tracking, and residual risk calculation.
    """
    
    __tablename__ = "security_controls"
    
    # Core control identification fields
    name = Column(String(255), nullable=False,
                 comment="Descriptive control name (e.g., 'ECU Code Signing', 'Network Segmentation')")
    description = Column(Text, nullable=False,
                        comment="Detailed control implementation description")
    
    # Control classification per data-model.md
    control_type = Column(SQLEnum(ControlType), nullable=False,
                         comment="Control category: PREVENTIVE, DETECTIVE, CORRECTIVE, COMPENSATING")
    effectiveness = Column(SQLEnum(ControlEffectiveness), nullable=False,
                          comment="Expected effectiveness: LOW, MEDIUM, HIGH, VERY_HIGH")
    
    # Implementation tracking fields
    implementation_status = Column(SQLEnum(ImplementationStatus), 
                                 default=ImplementationStatus.PLANNED, nullable=False,
                                 comment="Current implementation state")
    implementation_cost = Column(Float, nullable=True,
                               comment="Estimated or actual implementation cost")
    implementation_effort = Column(String(50), nullable=True,
                                 comment="Development effort estimate (e.g., '2 person-months')")
    
    # Control effectiveness quantification
    risk_reduction_factor = Column(Float, nullable=False, default=0.5,
                                 comment="Decimal factor by which control reduces risk (0.0-1.0)")
    coverage_percentage = Column(Float, nullable=True,
                               comment="Percentage of threat scenario covered by control")
    
    # ISO/SAE 21434 compliance fields
    is_regulatory_requirement = Column(Boolean, default=False,
                                     comment="Whether control is mandated by regulations")
    compliance_frameworks = Column(JSON, nullable=True,
                                 comment="List of applicable compliance frameworks")
    
    # Control validation and testing
    verification_methods = Column(JSON, nullable=True,
                                comment="Methods to verify control effectiveness")
    test_results = Column(JSON, nullable=True,
                         comment="Historical testing and validation results")
    
    # AI analysis fields per FR-009, FR-012
    confidence_score = Column(Float, nullable=True,
                            comment="AI control recommendation confidence (0.0-1.0)")
    review_status = Column(SQLEnum(ReviewStatus), 
                          default=ReviewStatus.IDENTIFIED, nullable=False,
                          comment="Manual review state for AI-recommended controls")
    
    # Foreign key relationships
    threat_scenario_id = Column(String(36), ForeignKey("threat_scenarios.id"), nullable=False,
                              comment="Threat scenario this control mitigates")
    analysis_id = Column(String(36), ForeignKey("tara_analyses.id"), nullable=False,
                        comment="Parent TARA analysis session")
    
    # Relationships per data-model.md relationship specifications
    threat_scenario = relationship("ThreatScenario", back_populates="controls")
    analysis = relationship("TaraAnalysis", back_populates="controls")
    risk_values = relationship("RiskValue", back_populates="control")
    
    def __repr__(self):
        return f"<SecurityControl(id={self.id}, name='{self.name}', type={self.control_type}, effectiveness={self.effectiveness})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate security control per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Control name must be descriptive and non-empty
        if not self.name or not self.name.strip():
            errors.append("Security control name must be non-empty")
        if self.name and len(self.name.strip()) < 5:
            errors.append("Control name should be descriptive (minimum 5 characters)")
            
        # Description must provide implementation guidance
        if not self.description or len(self.description.strip()) < 30:
            errors.append("Control description must be detailed (minimum 30 characters)")
            
        # Risk reduction factor validation
        if not (0.0 <= self.risk_reduction_factor <= 1.0):
            errors.append("Risk reduction factor must be between 0.0 and 1.0")
            
        # Coverage percentage validation
        if self.coverage_percentage is not None:
            if not (0.0 <= self.coverage_percentage <= 100.0):
                errors.append("Coverage percentage must be between 0.0 and 100.0")
                
        # Implementation cost validation
        if self.implementation_cost is not None and self.implementation_cost < 0:
            errors.append("Implementation cost cannot be negative")
            
        # Confidence score validation per FR-012
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                errors.append("Confidence score must be between 0.0 and 1.0")
                
        # Effectiveness vs. risk reduction consistency
        effectiveness_minimums = {
            ControlEffectiveness.LOW: 0.1,
            ControlEffectiveness.MEDIUM: 0.3,
            ControlEffectiveness.HIGH: 0.6,
            ControlEffectiveness.VERY_HIGH: 0.8
        }
        
        min_reduction = effectiveness_minimums.get(self.effectiveness, 0.0)
        if self.risk_reduction_factor < min_reduction:
            errors.append(f"{self.effectiveness.value} effectiveness requires risk reduction >= {min_reduction}")
            
        return len(errors) == 0, errors
    
    def calculate_residual_risk_factor(self) -> float:
        """Calculate residual risk factor after control application.
        
        Residual Risk = Original Risk × (1 - Risk Reduction Factor × Coverage Factor)
        """
        coverage_factor = (self.coverage_percentage or 100.0) / 100.0
        effective_reduction = self.risk_reduction_factor * coverage_factor
        
        # Account for implementation status
        implementation_factors = {
            ImplementationStatus.PLANNED: 0.0,      # No risk reduction until implemented
            ImplementationStatus.IN_PROGRESS: 0.3,  # Partial effectiveness during implementation
            ImplementationStatus.IMPLEMENTED: 1.0,  # Full effectiveness when complete
            ImplementationStatus.VERIFIED: 1.0,     # Maintained full effectiveness
            ImplementationStatus.FAILED: 0.0        # No protection if implementation failed
        }
        
        implementation_factor = implementation_factors.get(self.implementation_status, 0.0)
        actual_reduction = effective_reduction * implementation_factor
        
        return 1.0 - actual_reduction
    
    def transition_implementation_status(self, new_status: ImplementationStatus, reason: str = None) -> bool:
        """Handle implementation status transitions per data-model.md state rules."""
        valid_transitions = {
            ImplementationStatus.PLANNED: [ImplementationStatus.IN_PROGRESS, ImplementationStatus.FAILED],
            ImplementationStatus.IN_PROGRESS: [ImplementationStatus.IMPLEMENTED, ImplementationStatus.FAILED],
            ImplementationStatus.IMPLEMENTED: [ImplementationStatus.VERIFIED, ImplementationStatus.FAILED],
            ImplementationStatus.VERIFIED: [ImplementationStatus.FAILED],  # Can fail after verification
            ImplementationStatus.FAILED: [ImplementationStatus.PLANNED]    # Can restart implementation
        }
        
        if new_status in valid_transitions.get(self.implementation_status, []):
            self.implementation_status = new_status
            return True
        return False
    
    def assess_cost_effectiveness(self) -> Dict[str, float]:
        """Calculate control cost-effectiveness metrics.
        
        Returns cost per unit of risk reduction and ROI estimates.
        """
        if not self.implementation_cost or self.implementation_cost <= 0:
            return {'cost_per_risk_reduction': 0.0, 'roi_score': 1.0}
            
        # Cost per unit of risk reduction
        risk_reduction = self.risk_reduction_factor * ((self.coverage_percentage or 100.0) / 100.0)
        cost_effectiveness = self.implementation_cost / max(risk_reduction, 0.01)
        
        # ROI score (inverse cost effectiveness, normalized)
        roi_score = min(1.0, 1.0 / max(cost_effectiveness / 10000, 0.1))
        
        return {
            'cost_per_risk_reduction': cost_effectiveness,
            'roi_score': roi_score,
            'risk_reduction': risk_reduction
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling and calculated fields."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.control_type:
            result['control_type'] = self.control_type.value
        if self.effectiveness:
            result['effectiveness'] = self.effectiveness.value
        if self.implementation_status:
            result['implementation_status'] = self.implementation_status.value
        if self.review_status:
            result['review_status'] = self.review_status.value
            
        # Include calculated fields
        result['residual_risk_factor'] = self.calculate_residual_risk_factor()
        result['cost_effectiveness'] = self.assess_cost_effectiveness()
        
        return result
    
    @classmethod
    def from_nist_catalog(cls, nist_data: Dict[str, Any], threat_scenario_id: str, analysis_id: str) -> 'SecurityControl':
        """Create SecurityControl from NIST Cybersecurity Framework catalog.
        
        Args:
            nist_data: NIST control specification
            threat_scenario_id: Target threat scenario ID
            analysis_id: Parent analysis ID
        """
        # Map NIST control families to our control types
        family_mapping = {
            'PR': ControlType.PREVENTIVE,    # Protect
            'DE': ControlType.DETECTIVE,     # Detect
            'RS': ControlType.CORRECTIVE,    # Respond
            'RC': ControlType.CORRECTIVE     # Recover
        }
        
        nist_family = nist_data.get('id', '').split('.')[0]
        control_type = family_mapping.get(nist_family, ControlType.PREVENTIVE)
        
        return cls(
            name=nist_data.get('name'),
            description=nist_data.get('description'),
            control_type=control_type,
            effectiveness=ControlEffectiveness(nist_data.get('effectiveness', 'MEDIUM')),
            risk_reduction_factor=nist_data.get('risk_reduction', 0.5),
            coverage_percentage=nist_data.get('coverage', 100.0),
            implementation_cost=nist_data.get('cost_estimate'),
            implementation_effort=nist_data.get('effort_estimate'),
            verification_methods=nist_data.get('verification_methods', []),
            compliance_frameworks=['NIST CSF'],
            confidence_score=nist_data.get('confidence', 0.8),
            threat_scenario_id=threat_scenario_id,
            analysis_id=analysis_id,
            iso_section='7.4.3'  # ISO/SAE 21434 risk treatment section
        )