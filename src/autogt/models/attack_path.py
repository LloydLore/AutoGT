"""AttackPath model for AutoGT TARA platform.

Reference: data-model.md lines 62-87 (AttackPath entity definition)
Detailed sequence of attack steps for threat scenarios.
"""

from typing import Dict, List
from uuid import UUID
from sqlalchemy import String, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class AttackPath(BaseModel):
    """AttackPath model representing detailed sequence of attack steps."""
    
    __tablename__ = "attack_paths"
    
    # Core fields
    threat_scenario_id: Mapped[UUID] = mapped_column(ForeignKey("threat_scenarios.id"), nullable=False)
    step_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    attack_step: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSON fields for complex data
    intermediate_targets: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    technical_barriers: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    required_resources: Mapped[Dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    threat_scenario: Mapped["ThreatScenario"] = relationship("ThreatScenario", back_populates="attack_paths")
    attack_feasibility: Mapped["AttackFeasibility"] = relationship(
        "AttackFeasibility", back_populates="attack_path", cascade="all, delete-orphan", uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<AttackPath(id={self.id}, step={self.step_sequence}, scenario={self.threat_scenario_id})>"
    
    def validate_step_sequence(self, session) -> bool:
        """Validate step sequence is positive and sequential.
        
        Reference: data-model.md validation rules
        """
        if self.step_sequence <= 0:
            return False
            
        # Check for gaps in sequence within the same threat scenario
        from sqlalchemy import and_
        
        existing_steps = session.query(AttackPath.step_sequence).filter(
            and_(
                AttackPath.threat_scenario_id == self.threat_scenario_id,
                AttackPath.id != self.id
            )
        ).all()
        
        all_steps = sorted([step[0] for step in existing_steps] + [self.step_sequence])
        
        # Check for consecutive sequence starting from 1
        for i, step in enumerate(all_steps, 1):
            if step != i:
                return False
        return True
    
    def validate_intermediate_targets(self, session) -> bool:
        """Validate intermediate targets exist as assets or are external.
        
        Reference: data-model.md validation rules
        """
        if not self.intermediate_targets:
            return True
            
        from .asset import Asset
        
        # Get all asset names in the same analysis
        analysis_assets = session.query(Asset.name).join(Asset.analysis).filter(
            Asset.analysis_id == self.threat_scenario.asset.analysis_id
        ).all()
        
        asset_names = [asset[0] for asset in analysis_assets]
        external_keywords = ["external", "internet", "cloud", "remote", "third_party"]
        
        for target in self.intermediate_targets:
            # Target is either an existing asset or external system
            is_asset = target in asset_names
            is_external = any(keyword in target.lower() for keyword in external_keywords)
            
            if not (is_asset or is_external):
                return False
        return True
    
    def validate_technical_barriers(self) -> bool:
        """Validate technical barriers reference implemented security controls.
        
        Reference: data-model.md validation rules
        """
        if not self.technical_barriers:
            return True
            
        # Common security control types
        control_types = [
            "authentication", "authorization", "encryption", "firewall", "ids", "ips",
            "access_control", "logging", "monitoring", "integrity_check", "signature"
        ]
        
        for barrier in self.technical_barriers:
            # Each barrier should reference a known security control type
            if not any(control in barrier.lower() for control in control_types):
                return False
        return True