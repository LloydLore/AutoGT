"""RiskValue model for AutoGT TARA platform.

Reference: data-model.md lines 142-168 (RiskValue entity definition)
Calculated combination of impact rating and attack feasibility.
"""

from enum import Enum
from uuid import UUID
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class RiskValue(BaseModel):
    """RiskValue model representing calculated risk combination."""
    
    __tablename__ = "risk_values"
    
    # Core fields
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    threat_scenario_id: Mapped[UUID] = mapped_column(ForeignKey("threat_scenarios.id"), nullable=False)
    impact_rating_id: Mapped[UUID] = mapped_column(ForeignKey("impact_ratings.id"), nullable=False)
    attack_feasibility_id: Mapped[UUID] = mapped_column(ForeignKey("attack_feasibilities.id"), nullable=False)
    
    # Risk calculation
    risk_level: Mapped[RiskLevel] = mapped_column(nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(100), nullable=False, default="ISO_SAE_21434")
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="risk_values")
    threat_scenario: Mapped["ThreatScenario"] = relationship("ThreatScenario", back_populates="risk_values")
    impact_rating: Mapped["ImpactRating"] = relationship("ImpactRating", back_populates="risk_values")
    attack_feasibility: Mapped["AttackFeasibility"] = relationship("AttackFeasibility", back_populates="risk_values")
    risk_treatment: Mapped["RiskTreatment"] = relationship(
        "RiskTreatment", back_populates="risk_value", cascade="all, delete-orphan", uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<RiskValue(id={self.id}, level={self.risk_level.value}, score={self.risk_score})>"
    
    def calculate_risk_score(self) -> float:
        """Calculate risk score = impact_score × feasibility_score.
        
        Reference: data-model.md validation rules
        """
        if not (self.impact_rating and self.attack_feasibility):
            return 0.0
            
        return round(self.impact_rating.impact_score * self.attack_feasibility.feasibility_score, 3)
    
    def derive_risk_level_from_score(self, risk_score: float) -> RiskLevel:
        """Derive risk level from score thresholds per ISO/SAE 21434.
        
        Reference: data-model.md validation rules
        """
        if risk_score >= 0.8:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def validate_risk_calculation(self) -> bool:
        """Validate risk score calculation and level derivation.
        
        Reference: data-model.md validation rules
        """
        if not (self.impact_rating and self.attack_feasibility):
            return False
            
        expected_score = self.calculate_risk_score()
        expected_level = self.derive_risk_level_from_score(expected_score)
        
        return (abs(self.risk_score - expected_score) < 0.001 and
                self.risk_level == expected_level)
    
    def validate_referenced_entities_exist(self) -> bool:
        """Validate all referenced entities exist.
        
        Reference: data-model.md validation rules
        """
        return all([
            self.asset is not None,
            self.threat_scenario is not None,
            self.impact_rating is not None,
            self.attack_feasibility is not None,
        ])
    
    def update_calculated_values(self) -> None:
        """Update risk score and level based on current impact and feasibility."""
        self.risk_score = self.calculate_risk_score()
        self.risk_level = self.derive_risk_level_from_score(self.risk_score)