"""Asset model for AutoGT TARA platform.

Reference: data-model.md lines 5-33 (Asset entity definition)
Represents vehicle system components subject to cybersecurity analysis.
"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class AssetType(Enum):
    """Asset type enumeration."""
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    COMMUNICATION = "COMMUNICATION"
    DATA = "DATA"
    ECU = "ECU"


class CriticalityLevel(Enum):
    """Asset criticality level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Asset(BaseModel):
    """Asset model representing vehicle system components."""
    
    __tablename__ = "assets"
    
    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(nullable=False)
    criticality_level: Mapped[CriticalityLevel] = mapped_column(nullable=False)
    
    # JSON fields for complex data
    interfaces: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    data_flows: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    security_properties: Mapped[Dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # ISO/SAE 21434 traceability
    iso_section: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Foreign key to TaraAnalysis
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("tara_analyses.id"), nullable=False)
    
    # Relationships
    analysis: Mapped["TaraAnalysis"] = relationship("TaraAnalysis", back_populates="assets")
    threat_scenarios: Mapped[List["ThreatScenario"]] = relationship(
        "ThreatScenario", back_populates="asset", cascade="all, delete-orphan"
    )
    impact_ratings: Mapped[List["ImpactRating"]] = relationship(
        "ImpactRating", back_populates="asset", cascade="all, delete-orphan"
    )
    risk_values: Mapped[List["RiskValue"]] = relationship(
        "RiskValue", back_populates="asset", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', type={self.asset_type.value})>"
    
    def validate_name_uniqueness(self, session) -> bool:
        """Validate name uniqueness within analysis.
        
        Reference: data-model.md validation rules
        """
        from sqlalchemy import and_
        
        existing = session.query(Asset).filter(
            and_(
                Asset.analysis_id == self.analysis_id,
                Asset.name == self.name,
                Asset.id != self.id
            )
        ).first()
        return existing is None
    
    def validate_iso_section(self) -> bool:
        """Validate ISO section reference format.
        
        Reference: data-model.md validation rules
        """
        # ISO/SAE 21434 section format validation
        import re
        pattern = r'^ISO\/SAE\s21434-\d+(\.\d+)*$|^21434-\d+(\.\d+)*$'
        return bool(re.match(pattern, self.iso_section))
    
    def validate_criticality_alignment(self) -> bool:
        """Validate criticality level aligns with safety requirements.
        
        Reference: data-model.md validation rules
        """
        # Safety-critical assets should have HIGH or VERY_HIGH criticality
        safety_props = self.security_properties.get('safety', {})
        is_safety_critical = safety_props.get('critical', False)
        
        if is_safety_critical:
            return self.criticality_level in [CriticalityLevel.HIGH, CriticalityLevel.VERY_HIGH]
        return True