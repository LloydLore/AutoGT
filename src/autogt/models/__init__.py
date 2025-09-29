"""Data models for AutoGT TARA platform."""

# Import base first
from .base import Base, BaseModel, AuditMixin, GUID

# Import all models
from .analysis import TaraAnalysis, AnalysisPhase, CompletionStatus
from .asset import Asset, AssetType, CriticalityLevel
from .threat import ThreatScenario, ThreatActor
from .attack_path import AttackPath
from .attack_feasibility import (
    AttackFeasibility, ElapsedTime, SpecialistExpertise, 
    KnowledgeOfTarget, WindowOfOpportunity, EquipmentRequired
)
from .impact import (
    ImpactRating, SafetyImpact, FinancialImpact, 
    OperationalImpact, PrivacyImpact
)
from .risk import RiskValue, RiskLevel
from .treatment import RiskTreatment, TreatmentDecision, ResidualRiskLevel
from .goal import CybersecurityGoal, ProtectionLevel, ImplementationPhase

# Export all models and enums
__all__ = [
    # Base classes
    "Base", "BaseModel", "AuditMixin", "GUID",
    
    # Models
    "TaraAnalysis", "Asset", "ThreatScenario", "AttackPath", 
    "AttackFeasibility", "ImpactRating", "RiskValue", 
    "RiskTreatment", "CybersecurityGoal",
    
    # Enums
    "AnalysisPhase", "CompletionStatus", "AssetType", "CriticalityLevel",
    "ThreatActor", "ElapsedTime", "SpecialistExpertise", "KnowledgeOfTarget", 
    "WindowOfOpportunity", "EquipmentRequired", "SafetyImpact", "FinancialImpact",
    "OperationalImpact", "PrivacyImpact", "RiskLevel", "TreatmentDecision", 
    "ResidualRiskLevel", "ProtectionLevel", "ImplementationPhase"
]