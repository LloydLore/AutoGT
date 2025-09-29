"""ThreatScenario model for AutoGT TARA platform.

Reference: data-model.md lines 34-61 (ThreatScenario entity definition)
Specific cybersecurity threats applicable to assets.
"""

from enum import Enum
from typing import List
from uuid import UUID
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ThreatActor(Enum):
    """Threat actor enumeration."""
    SCRIPT_KIDDIE = "SCRIPT_KIDDIE"
    CRIMINAL = "CRIMINAL"
    NATION_STATE = "NATION_STATE"
    INSIDER = "INSIDER"


class ThreatScenario(BaseModel):
    """ThreatScenario model representing specific cybersecurity threats."""
    
    __tablename__ = "threat_scenarios"
    
    # Core fields
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    threat_name: Mapped[str] = mapped_column(String(255), nullable=False)
    threat_actor: Mapped[ThreatActor] = mapped_column(nullable=False)
    motivation: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSON fields for complex data
    attack_vectors: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    prerequisites: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    
    # ISO/SAE 21434 traceability
    iso_section: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="threat_scenarios")
    attack_paths: Mapped[List["AttackPath"]] = relationship(
        "AttackPath", back_populates="threat_scenario", cascade="all, delete-orphan"
    )
    risk_values: Mapped[List["RiskValue"]] = relationship(
        "RiskValue", back_populates="threat_scenario", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ThreatScenario(id={self.id}, name='{self.threat_name}', actor={self.threat_actor.value})>"
    
    def validate_attack_vectors_feasibility(self) -> bool:
        """Validate attack vectors are technically feasible for asset type.
        
        Reference: data-model.md validation rules
        """
        if not self.asset:
            return False
            
        asset_type = self.asset.asset_type
        
        # Define feasible attack vectors per asset type
        feasible_vectors = {
            "HARDWARE": ["physical_access", "side_channel", "tampering", "fault_injection"],
            "SOFTWARE": ["code_injection", "buffer_overflow", "privilege_escalation", "malware"],
            "COMMUNICATION": ["eavesdropping", "man_in_middle", "replay", "jamming"],
            "DATA": ["unauthorized_access", "data_corruption", "data_theft", "privacy_breach"]
        }
        
        asset_vectors = feasible_vectors.get(asset_type.value, [])
        return all(vector in asset_vectors for vector in self.attack_vectors)
    
    def validate_prerequisites(self) -> bool:
        """Validate prerequisites are verifiable conditions.
        
        Reference: data-model.md validation rules
        """
        # Prerequisites should be specific, measurable conditions
        verifiable_keywords = ["access", "knowledge", "tool", "credential", "position", "time"]
        
        for prereq in self.prerequisites:
            if not any(keyword in prereq.lower() for keyword in verifiable_keywords):
                return False
        return True