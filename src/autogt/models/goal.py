"""CybersecurityGoal model for AutoGT TARA platform.

Reference: data-model.md lines 196-222 (CybersecurityGoal entity definition)
Specific security objectives derived from risk analysis.
"""

from enum import Enum
from typing import List, Optional
from uuid import UUID
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ProtectionLevel(Enum):
    """Protection level enumeration per ISO/SAE 21434."""
    CAL1 = "CAL1"
    CAL2 = "CAL2" 
    CAL3 = "CAL3"
    CAL4 = "CAL4"


class ImplementationPhase(Enum):
    """Implementation phase enumeration."""
    DESIGN = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    INTEGRATION = "INTEGRATION"
    VALIDATION = "VALIDATION"


class CybersecurityGoal(BaseModel):
    """CybersecurityGoal model representing specific security objectives."""
    
    __tablename__ = "cybersecurity_goals"
    
    # Core fields
    risk_treatment_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("risk_treatments.id"), nullable=True)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("tara_analyses.id"), nullable=False)
    
    goal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    protection_level: Mapped[ProtectionLevel] = mapped_column(nullable=False)
    implementation_phase: Mapped[ImplementationPhase] = mapped_column(nullable=False)
    
    # Goal details
    security_controls: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    verification_method: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ISO/SAE 21434 traceability
    iso_section: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    risk_treatment: Mapped["RiskTreatment"] = relationship("RiskTreatment", back_populates="cybersecurity_goals")
    analysis: Mapped["TaraAnalysis"] = relationship("TaraAnalysis", back_populates="cybersecurity_goals")
    
    def __repr__(self) -> str:
        return f"<CybersecurityGoal(id={self.id}, name='{self.goal_name}', level={self.protection_level.value})>"
    
    def validate_protection_level_alignment(self) -> bool:
        """Validate protection level aligns with residual risk requirements.
        
        Reference: data-model.md validation rules
        """
        if not self.risk_treatment:
            return False
            
        # Protection level should be inverse to residual risk level
        risk_to_protection = {
            "VERY_HIGH": [ProtectionLevel.VERY_HIGH],
            "HIGH": [ProtectionLevel.HIGH, ProtectionLevel.VERY_HIGH],
            "MEDIUM": [ProtectionLevel.MEDIUM, ProtectionLevel.HIGH, ProtectionLevel.VERY_HIGH],
            "LOW": [ProtectionLevel.BASIC, ProtectionLevel.MEDIUM, ProtectionLevel.HIGH, ProtectionLevel.VERY_HIGH],
        }
        
        residual_risk = self.risk_treatment.residual_risk_level.value
        acceptable_levels = risk_to_protection.get(residual_risk, [])
        
        return self.protection_level in acceptable_levels
    
    def validate_security_controls_implementable(self) -> bool:
        """Validate security controls are implementable and verifiable.
        
        Reference: data-model.md validation rules
        """
        if not self.security_controls:
            return False
            
        # Common implementable security controls
        valid_controls = [
            "authentication", "authorization", "encryption", "access_control",
            "logging", "monitoring", "integrity_verification", "digital_signature",
            "secure_communication", "input_validation", "output_encoding",
            "error_handling", "session_management", "cryptographic_storage"
        ]
        
        for control in self.security_controls:
            # Each control should match a known implementable pattern
            if not any(valid_control in control.lower() for valid_control in valid_controls):
                return False
        return True
    
    def validate_verification_method_measurable(self) -> bool:
        """Validate verification method is measurable.
        
        Reference: data-model.md validation rules
        """
        if not self.verification_method or len(self.verification_method.strip()) < 10:
            return False
            
        # Check for measurable verification keywords
        measurable_keywords = [
            "test", "verify", "validate", "measure", "check", "audit",
            "assess", "evaluate", "inspect", "review", "analyze", "confirm"
        ]
        
        return any(keyword in self.verification_method.lower() for keyword in measurable_keywords)
    
    def validate_goal_name_uniqueness(self, session) -> bool:
        """Validate goal name is unique within analysis."""
        from sqlalchemy import and_
        
        existing = session.query(CybersecurityGoal).filter(
            and_(
                CybersecurityGoal.analysis_id == self.analysis_id,
                CybersecurityGoal.goal_name == self.goal_name,
                CybersecurityGoal.id != self.id
            )
        ).first()
        return existing is None