"""RiskTreatment model for AutoGT TARA platform.

Reference: data-model.md lines 169-195 (RiskTreatment entity definition)
Mitigation strategy decisions for identified risks.
"""

from enum import Enum
from typing import List
from uuid import UUID
from sqlalchemy import String, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class TreatmentDecision(Enum):
    """Treatment decision enumeration."""
    REDUCE = "REDUCE"
    TRANSFER = "TRANSFER"
    AVOID = "AVOID"
    ACCEPT = "ACCEPT"


class ResidualRiskLevel(Enum):
    """Residual risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class RiskTreatment(BaseModel):
    """RiskTreatment model representing mitigation strategy decisions."""
    
    __tablename__ = "risk_treatments"
    
    # Core fields
    risk_value_id: Mapped[UUID] = mapped_column(ForeignKey("risk_values.id"), nullable=False)
    treatment_decision: Mapped[TreatmentDecision] = mapped_column(nullable=False)
    residual_risk_level: Mapped[ResidualRiskLevel] = mapped_column(nullable=False)
    
    # Treatment details
    countermeasures: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    implementation_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ISO/SAE 21434 traceability
    iso_section: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    risk_value: Mapped["RiskValue"] = relationship("RiskValue", back_populates="risk_treatment")
    cybersecurity_goals: Mapped[List["CybersecurityGoal"]] = relationship(
        "CybersecurityGoal", back_populates="risk_treatment", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<RiskTreatment(id={self.id}, decision={self.treatment_decision.value}, cost={self.implementation_cost})>"
    
    def validate_residual_risk_level(self) -> bool:
        """Validate residual risk must be <= original risk level.
        
        Reference: data-model.md validation rules
        """
        if not self.risk_value:
            return False
            
        risk_level_order = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "VERY_HIGH": 4,
        }
        
        original_level = risk_level_order[self.risk_value.risk_level.value]
        residual_level = risk_level_order[self.residual_risk_level.value]
        
        return residual_level <= original_level
    
    def validate_countermeasures_required(self) -> bool:
        """Validate countermeasures required unless decision is ACCEPT.
        
        Reference: data-model.md validation rules
        """
        if self.treatment_decision == TreatmentDecision.ACCEPT:
            return True  # No countermeasures required for acceptance
        return len(self.countermeasures) > 0
    
    def validate_cost_requirements(self) -> bool:
        """Validate cost must be positive for REDUCE/TRANSFER decisions.
        
        Reference: data-model.md validation rules
        """
        cost_required_decisions = [TreatmentDecision.REDUCE, TreatmentDecision.TRANSFER]
        
        if self.treatment_decision in cost_required_decisions:
            return self.implementation_cost > 0.0
        return True
    
    def validate_rationale_completeness(self) -> bool:
        """Validate rationale is provided and meaningful."""
        if not self.rationale or len(self.rationale.strip()) < 10:
            return False
            
        # Check for key decision factors
        decision_keywords = {
            TreatmentDecision.REDUCE: ["mitigate", "control", "implement", "reduce"],
            TreatmentDecision.TRANSFER: ["transfer", "share", "insurance", "third-party"],
            TreatmentDecision.AVOID: ["avoid", "eliminate", "remove", "discontinue"],
            TreatmentDecision.ACCEPT: ["accept", "tolerate", "justify", "acceptable"],
        }
        
        keywords = decision_keywords.get(self.treatment_decision, [])
        return any(keyword in self.rationale.lower() for keyword in keywords)