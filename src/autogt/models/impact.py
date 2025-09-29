"""ImpactRating model for AutoGT TARA platform.

Reference: data-model.md lines 115-141 (ImpactRating entity definition)
Quantified assessment of potential damage levels.
"""

from enum import Enum
from typing import List
from uuid import UUID
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class SafetyImpact(Enum):
    """Safety impact enumeration."""
    NONE = "NONE"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    HAZARDOUS = "HAZARDOUS"


class FinancialImpact(Enum):
    """Financial impact enumeration."""
    NEGLIGIBLE = "NEGLIGIBLE"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    SEVERE = "SEVERE"


class OperationalImpact(Enum):
    """Operational impact enumeration."""
    NONE = "NONE"
    DEGRADED = "DEGRADED"
    MAJOR = "MAJOR"
    LOSS = "LOSS"


class PrivacyImpact(Enum):
    """Privacy impact enumeration."""
    NONE = "NONE"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    SEVERE = "SEVERE"


class ImpactRating(BaseModel):
    """ImpactRating model representing quantified assessment of potential damage."""
    
    __tablename__ = "impact_ratings"
    
    # Core fields
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    
    # Impact categories
    safety_impact: Mapped[SafetyImpact] = mapped_column(nullable=False)
    financial_impact: Mapped[FinancialImpact] = mapped_column(nullable=False)
    operational_impact: Mapped[OperationalImpact] = mapped_column(nullable=False)
    privacy_impact: Mapped[PrivacyImpact] = mapped_column(nullable=False)
    
    # Calculated score
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # ISO/SAE 21434 traceability
    iso_section: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="impact_ratings")
    risk_values: Mapped[List["RiskValue"]] = relationship(
        "RiskValue", back_populates="impact_rating", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ImpactRating(id={self.id}, score={self.impact_score}, asset={self.asset_id})>"
    
    def calculate_impact_score(self) -> float:
        """Calculate impact score from enum values.
        
        Reference: data-model.md validation rules
        """
        safety_scores = {
            SafetyImpact.NONE: 0.0,
            SafetyImpact.MODERATE: 0.3,
            SafetyImpact.MAJOR: 0.7,
            SafetyImpact.HAZARDOUS: 1.0,
        }
        
        financial_scores = {
            FinancialImpact.NEGLIGIBLE: 0.0,
            FinancialImpact.MODERATE: 0.3,
            FinancialImpact.MAJOR: 0.7,
            FinancialImpact.SEVERE: 1.0,
        }
        
        operational_scores = {
            OperationalImpact.NONE: 0.0,
            OperationalImpact.DEGRADED: 0.3,
            OperationalImpact.MAJOR: 0.7,
            OperationalImpact.LOSS: 1.0,
        }
        
        privacy_scores = {
            PrivacyImpact.NONE: 0.0,
            PrivacyImpact.MODERATE: 0.3,
            PrivacyImpact.MAJOR: 0.7,
            PrivacyImpact.SEVERE: 1.0,
        }
        
        # Take maximum impact across categories
        max_impact = max(
            safety_scores[self.safety_impact],
            financial_scores[self.financial_impact],
            operational_scores[self.operational_impact],
            privacy_scores[self.privacy_impact]
        )
        
        return round(max_impact, 3)
    
    def validate_safety_alignment(self) -> bool:
        """Validate safety impact aligns with vehicle safety requirements.
        
        Reference: data-model.md validation rules
        """
        if not self.asset:
            return False
            
        # Safety-critical assets should have appropriate safety impact ratings
        safety_props = self.asset.security_properties.get('safety', {})
        is_safety_critical = safety_props.get('critical', False)
        
        if is_safety_critical and self.safety_impact == SafetyImpact.NONE:
            return False
        return True
    
    def validate_non_zero_impact(self) -> bool:
        """Validate at least one impact category is non-zero.
        
        Reference: data-model.md validation rules
        """
        return any([
            self.safety_impact != SafetyImpact.NONE,
            self.financial_impact != FinancialImpact.NEGLIGIBLE,
            self.operational_impact != OperationalImpact.NONE,
            self.privacy_impact != PrivacyImpact.NONE,
        ])
    
    def update_calculated_score(self) -> None:
        """Update impact score based on current enum values."""
        self.impact_score = self.calculate_impact_score()