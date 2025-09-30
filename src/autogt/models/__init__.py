"""AutoGT data models package.

Contains SQLAlchemy models for TARA (Threat Analysis and Risk Assessment) data.
Per data-model.md specification with complete entity relationships.
"""

# Database infrastructure
from .database import Base, SessionLocal, get_db, init_db, reset_db

# Base classes and enumerations
from .base import BaseModel, ISO21434Mixin
from .enums import *

# Entity models per data-model.md specification
from .tara_analysis import TaraAnalysis
from .asset import Asset
from .threat_scenario import ThreatScenario
from .security_control import SecurityControl
from .impact_rating import ImpactRating
from .risk_value import RiskValue

__all__ = [
    # Database infrastructure
    "Base", "SessionLocal", "get_db", "init_db", "reset_db",
    
    # Base classes
    "BaseModel", "ISO21434Mixin",
    
    # Entity models
    "TaraAnalysis", "Asset", "ThreatScenario", 
    "SecurityControl", "ImpactRating", "RiskValue",
    
    # Enumerations exported via *
    "AssetType", "CriticalityLevel", "ThreatCategory", "AttackVector", 
    "AttackComplexity", "ControlType", "ControlEffectiveness", 
    "ImplementationStatus", "ImpactCategory", "ImpactSeverity", 
    "ConfidenceLevel", "RiskLevel", "RiskStatus", "AnalysisStatus", 
    "ReviewStatus", "WorkflowState", "ValidationLevel"
]