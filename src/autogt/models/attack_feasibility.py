"""AttackFeasibility model for AutoGT TARA platform.

Reference: data-model.md lines 88-114 (AttackFeasibility entity definition)
Assessment of attack likelihood and difficulty.
"""

from enum import Enum
from typing import List
from uuid import UUID
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ElapsedTime(Enum):
    """Elapsed time enumeration."""
    MINUTES = "MINUTES"
    HOURS = "HOURS"
    DAYS = "DAYS"
    WEEKS = "WEEKS"
    MONTHS = "MONTHS"


class SpecialistExpertise(Enum):
    """Specialist expertise enumeration."""
    NONE = "NONE"
    LIMITED = "LIMITED"
    PROFICIENT = "PROFICIENT"
    EXPERT = "EXPERT"


class KnowledgeOfTarget(Enum):
    """Knowledge of target enumeration."""
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class WindowOfOpportunity(Enum):
    """Window of opportunity enumeration."""
    UNLIMITED = "UNLIMITED"
    MODERATE = "MODERATE"
    DIFFICULT = "DIFFICULT"
    NONE = "NONE"


class EquipmentRequired(Enum):
    """Equipment required enumeration."""
    STANDARD = "STANDARD"
    SPECIALIZED = "SPECIALIZED"
    BESPOKE = "BESPOKE"
    MULTIPLE_BESPOKE = "MULTIPLE_BESPOKE"


class AttackFeasibility(BaseModel):
    """AttackFeasibility model representing assessment of attack likelihood."""
    
    __tablename__ = "attack_feasibilities"
    
    # Core fields
    attack_path_id: Mapped[UUID] = mapped_column(ForeignKey("attack_paths.id"), nullable=False)
    
    # Feasibility factors
    elapsed_time: Mapped[ElapsedTime] = mapped_column(nullable=False)
    specialist_expertise: Mapped[SpecialistExpertise] = mapped_column(nullable=False)
    knowledge_of_target: Mapped[KnowledgeOfTarget] = mapped_column(nullable=False)
    window_of_opportunity: Mapped[WindowOfOpportunity] = mapped_column(nullable=False)
    equipment_required: Mapped[EquipmentRequired] = mapped_column(nullable=False)
    
    # Calculated score
    feasibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    attack_path: Mapped["AttackPath"] = relationship("AttackPath", back_populates="attack_feasibility")
    risk_values: Mapped[List["RiskValue"]] = relationship(
        "RiskValue", back_populates="attack_feasibility", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AttackFeasibility(id={self.id}, score={self.feasibility_score}, path={self.attack_path_id})>"
    
    def calculate_feasibility_score(self) -> float:
        """Calculate feasibility score from enum values using ISO/SAE 21434 methodology.
        
        Reference: data-model.md validation rules
        """
        # ISO/SAE 21434 scoring matrix
        time_scores = {
            ElapsedTime.MINUTES: 1.0,
            ElapsedTime.HOURS: 0.8,
            ElapsedTime.DAYS: 0.6,
            ElapsedTime.WEEKS: 0.4,
            ElapsedTime.MONTHS: 0.2,
        }
        
        expertise_scores = {
            SpecialistExpertise.NONE: 1.0,
            SpecialistExpertise.LIMITED: 0.8,
            SpecialistExpertise.PROFICIENT: 0.5,
            SpecialistExpertise.EXPERT: 0.2,
        }
        
        knowledge_scores = {
            KnowledgeOfTarget.PUBLIC: 1.0,
            KnowledgeOfTarget.RESTRICTED: 0.7,
            KnowledgeOfTarget.SENSITIVE: 0.4,
            KnowledgeOfTarget.CRITICAL: 0.1,
        }
        
        opportunity_scores = {
            WindowOfOpportunity.UNLIMITED: 1.0,
            WindowOfOpportunity.MODERATE: 0.7,
            WindowOfOpportunity.DIFFICULT: 0.4,
            WindowOfOpportunity.NONE: 0.1,
        }
        
        equipment_scores = {
            EquipmentRequired.STANDARD: 1.0,
            EquipmentRequired.SPECIALIZED: 0.7,
            EquipmentRequired.BESPOKE: 0.4,
            EquipmentRequired.MULTIPLE_BESPOKE: 0.2,
        }
        
        # Calculate weighted average
        total_score = (
            time_scores[self.elapsed_time] * 0.3 +
            expertise_scores[self.specialist_expertise] * 0.25 +
            knowledge_scores[self.knowledge_of_target] * 0.2 +
            opportunity_scores[self.window_of_opportunity] * 0.15 +
            equipment_scores[self.equipment_required] * 0.1
        )
        
        return round(total_score, 3)
    
    def validate_feasibility_score(self) -> bool:
        """Validate feasibility score is between 0.0 and 1.0.
        
        Reference: data-model.md validation rules
        """
        return 0.0 <= self.feasibility_score <= 1.0
    
    def update_calculated_score(self) -> None:
        """Update feasibility score based on current enum values."""
        self.feasibility_score = self.calculate_feasibility_score()