"""TaraAnalysis model for AutoGT TARA platform.

Reference: data-model.md lines 223-271 (TaraAnalysis entity definition)
Complete assessment workflow container.
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class AnalysisPhase(Enum):
    """Analysis phase enumeration."""
    CONCEPT = "CONCEPT"
    DESIGN = "DESIGN"
    IMPLEMENTATION = "IMPLEMENTATION"
    INTEGRATION = "INTEGRATION"


class CompletionStatus(Enum):
    """Completion status enumeration."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class TaraAnalysis(BaseModel):
    """TaraAnalysis model representing complete assessment workflow container."""
    
    __tablename__ = "tara_analyses"
    
    # Core identification
    analysis_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    vehicle_model: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Analysis metadata
    analysis_phase: Mapped[AnalysisPhase] = mapped_column(nullable=False)
    completion_status: Mapped[CompletionStatus] = mapped_column(
        nullable=False, default=CompletionStatus.IN_PROGRESS
    )
    
    # File paths  
    input_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    output_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)    # ISO/SAE 21434 traceability
    iso_section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Completion tracking
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships - One-to-many with all other entities
    assets: Mapped[List["Asset"]] = relationship(
        "Asset", back_populates="analysis", cascade="all, delete-orphan"
    )
    cybersecurity_goals: Mapped[List["CybersecurityGoal"]] = relationship(
        "CybersecurityGoal", back_populates="analysis", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TaraAnalysis(id={self.id}, name='{self.analysis_name}', status={self.completion_status.value})>"
    
    def validate_analysis_name_uniqueness(self, session) -> bool:
        """Validate analysis name is unique per user session.
        
        Reference: data-model.md validation rules
        """
        from sqlalchemy import and_
        
        existing = session.query(TaraAnalysis).filter(
            and_(
                TaraAnalysis.analysis_name == self.analysis_name,
                TaraAnalysis.id != self.id
            )
        ).first()
        return existing is None
    
    def validate_input_file_format(self) -> bool:
        """Validate input file format is supported.
        
        Reference: data-model.md validation rules
        """
        if not self.input_file_path:
            return True  # No file is valid for interactive analyses
            
        supported_extensions = ['.xlsx', '.xls', '.csv', '.json', '.txt']
        return any(self.input_file_path.lower().endswith(ext) for ext in supported_extensions)
    
    def validate_output_file_generated_on_completion(self) -> bool:
        """Validate output file is generated only upon completion.
        
        Reference: data-model.md validation rules
        """
        if self.completion_status == CompletionStatus.IN_PROGRESS:
            return self.output_file_path is None
        else:
            return self.output_file_path is not None
    
    def validate_completion_timestamp(self) -> bool:
        """Validate completion timestamp is set when status is completed."""
        if self.completion_status in [CompletionStatus.COMPLETED, CompletionStatus.VALIDATED]:
            return self.completed_at is not None
        else:
            return self.completed_at is None
    
    def get_current_step(self) -> int:
        """Get current step in 8-step TARA process based on completed entities."""
        if not self.assets:
            return 1  # Step 1: Asset definition
        
        # Check if all assets have impact ratings (Step 2)
        if not all(asset.impact_ratings for asset in self.assets):
            return 2  # Step 2: Impact rating
        
        # Check if all assets have threat scenarios (Step 3)
        if not all(asset.threat_scenarios for asset in self.assets):
            return 3  # Step 3: Threat identification
        
        # Check if all threat scenarios have attack paths (Step 4)
        all_have_paths = all(
            scenario.attack_paths 
            for asset in self.assets 
            for scenario in asset.threat_scenarios
        )
        if not all_have_paths:
            return 4  # Step 4: Attack paths
        
        # Check if all attack paths have feasibility assessments (Step 5)
        all_have_feasibility = all(
            path.attack_feasibility 
            for asset in self.assets 
            for scenario in asset.threat_scenarios
            for path in scenario.attack_paths
        )
        if not all_have_feasibility:
            return 5  # Step 5: Attack feasibility
        
        # Check if all combinations have risk values (Step 6)
        if not all(asset.risk_values for asset in self.assets):
            return 6  # Step 6: Risk values
        
        # Check if all risk values have treatments (Step 7)
        all_have_treatments = all(
            risk.risk_treatment 
            for asset in self.assets 
            for risk in asset.risk_values
        )
        if not all_have_treatments:
            return 7  # Step 7: Risk treatment
        
        # Check if all treatments have cybersecurity goals (Step 8)
        if not self.cybersecurity_goals:
            return 8  # Step 8: Cybersecurity goals
        
        return 8  # Complete
    
    def mark_completed(self) -> None:
        """Mark analysis as completed with timestamp."""
        self.completion_status = CompletionStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_validated(self) -> None:
        """Mark analysis as validated."""
        if self.completion_status == CompletionStatus.COMPLETED:
            self.completion_status = CompletionStatus.VALIDATED