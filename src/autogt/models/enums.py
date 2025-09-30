"""Enumerations for TARA data model as specified in data-model.md."""

from enum import Enum


# Asset Classifications (data-model.md supporting enumerations section)
class AssetType(str, Enum):
    """Asset type classification per ISO/SAE 21434."""
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE" 
    COMMUNICATION = "COMMUNICATION"
    DATA = "DATA"
    HUMAN = "HUMAN"
    PHYSICAL = "PHYSICAL"


class CriticalityLevel(str, Enum):
    """Asset criticality level for safety/security importance."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewStatus(str, Enum):
    """Asset review status for AI confidence workflow per FR-011."""
    IDENTIFIED = "IDENTIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


# Risk Assessment Levels
class ImpactLevel(str, Enum):
    """Impact severity levels per automotive standards."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class LikelihoodLevel(str, Enum):
    """Likelihood assessment levels."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class RiskLevel(str, Enum):
    """Risk level calculation results."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class FeasibilityLevel(str, Enum):
    """Attack feasibility assessment levels."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


# Attack Characteristics
class ThreatCategory(str, Enum):
    """STRIDE threat categories per data-model.md."""
    SPOOFING = "SPOOFING"
    TAMPERING = "TAMPERING" 
    REPUDIATION = "REPUDIATION"
    INFORMATION_DISCLOSURE = "INFORMATION_DISCLOSURE"
    DENIAL_OF_SERVICE = "DENIAL_OF_SERVICE"
    ELEVATION_OF_PRIVILEGE = "ELEVATION_OF_PRIVILEGE"


class AttackVector(str, Enum):
    """CVSS attack vector classification."""
    NETWORK = "NETWORK"
    ADJACENT = "ADJACENT"
    LOCAL = "LOCAL"
    PHYSICAL = "PHYSICAL"


class AttackComplexity(str, Enum):
    """CVSS attack complexity classification."""
    LOW = "LOW"
    HIGH = "HIGH"


class ControlType(str, Enum):
    """Security control classification per data-model.md."""
    PREVENTIVE = "PREVENTIVE"
    DETECTIVE = "DETECTIVE"
    CORRECTIVE = "CORRECTIVE"
    COMPENSATING = "COMPENSATING"


class ControlEffectiveness(str, Enum):
    """Control effectiveness assessment."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ImplementationStatus(str, Enum):
    """Control implementation status tracking."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class ImpactCategory(str, Enum):
    """Impact assessment categories per data-model.md."""
    SAFETY = "SAFETY"
    FINANCIAL = "FINANCIAL"
    OPERATIONAL = "OPERATIONAL"
    PRIVACY = "PRIVACY"
    REPUTATION = "REPUTATION"


class ImpactSeverity(str, Enum):
    """Impact severity levels per data-model.md."""
    NEGLIGIBLE = "NEGLIGIBLE"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    SEVERE = "SEVERE"
    CATASTROPHIC = "CATASTROPHIC"


class ConfidenceLevel(str, Enum):
    """Assessment confidence levels per FR-012."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskStatus(str, Enum):
    """Risk management status tracking."""
    IDENTIFIED = "IDENTIFIED"
    ANALYZED = "ANALYZED"
    TREATED = "TREATED"
    MONITORED = "MONITORED"
    CLOSED = "CLOSED"


class WorkflowState(str, Enum):
    """Generic workflow state management."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ValidationLevel(str, Enum):
    """Validation and verification levels."""
    NONE = "NONE"
    BASIC = "BASIC"
    COMPREHENSIVE = "COMPREHENSIVE"
    CERTIFIED = "CERTIFIED"


class ThreatActor(str, Enum):
    """Threat actor classifications."""
    SCRIPT_KIDDIE = "SCRIPT_KIDDIE"
    CRIMINAL = "CRIMINAL"
    ORGANIZED_CRIME = "ORGANIZED_CRIME"
    NATION_STATE = "NATION_STATE"
    INSIDER = "INSIDER"
    COMPETITOR = "COMPETITOR"


class SkillLevel(str, Enum):
    """Required attacker skill levels per ISO/SAE 21434."""
    LAYPERSON = "LAYPERSON"
    PROFICIENT = "PROFICIENT"
    EXPERT = "EXPERT"
    MULTIPLE_EXPERTS = "MULTIPLE_EXPERTS"


class ResourceLevel(str, Enum):
    """Required attacker resources."""
    MINIMAL = "MINIMAL"
    STANDARD = "STANDARD"
    SPECIALIZED = "SPECIALIZED"
    EXTENSIVE = "EXTENSIVE"


class TimeLevel(str, Enum):
    """Attack execution time requirements."""
    MINUTES = "MINUTES"
    HOURS = "HOURS"
    DAYS = "DAYS"
    WEEKS = "WEEKS"
    MONTHS = "MONTHS"


class ExpertiseLevel(str, Enum):
    """Required technical expertise levels."""
    NONE = "NONE"
    LIMITED = "LIMITED"
    PROFICIENT = "PROFICIENT"
    EXPERT = "EXPERT"


class KnowledgeLevel(str, Enum):
    """Required knowledge of target system."""
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class OpportunityLevel(str, Enum):
    """Window of opportunity constraints."""
    UNLIMITED = "UNLIMITED"
    MODERATE = "MODERATE"
    DIFFICULT = "DIFFICULT"
    NONE = "NONE"


class EquipmentLevel(str, Enum):
    """Required equipment sophistication."""
    STANDARD = "STANDARD"
    SPECIALIZED = "SPECIALIZED"
    BESPOKE = "BESPOKE"
    MULTIPLE_BESPOKE = "MULTIPLE_BESPOKE"


class ComplexityLevel(str, Enum):
    """Attack path complexity assessment."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class DetectabilityLevel(str, Enum):
    """Attack detection difficulty."""
    EASY = "EASY"
    MODERATE = "MODERATE"
    DIFFICULT = "DIFFICULT"
    VERY_DIFFICULT = "VERY_DIFFICULT"


# Treatment Options
class TreatmentDecision(str, Enum):
    """Risk treatment strategy decisions."""
    ACCEPT = "ACCEPT"
    REDUCE = "REDUCE"
    TRANSFER = "TRANSFER"
    AVOID = "AVOID"


class ApprovalStatus(str, Enum):
    """Treatment approval workflow status."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"


class SecurityProperty(str, Enum):
    """Cybersecurity properties per ISO/SAE 21434."""
    CONFIDENTIALITY = "CONFIDENTIALITY"
    INTEGRITY = "INTEGRITY"
    AVAILABILITY = "AVAILABILITY"
    AUTHENTICITY = "AUTHENTICITY"
    AUTHORIZATION = "AUTHORIZATION"
    NON_REPUDIATION = "NON_REPUDIATION"


class PriorityLevel(str, Enum):
    """Implementation priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Workflow States
class TaraStep(str, Enum):
    """8-step TARA process workflow per ISO/SAE 21434."""
    ASSET_DEFINITION = "ASSET_DEFINITION"           # Step 1
    IMPACT_RATING = "IMPACT_RATING"                 # Step 2  
    THREAT_SCENARIO = "THREAT_SCENARIO"             # Step 3
    ATTACK_PATH = "ATTACK_PATH"                     # Step 4
    FEASIBILITY_RATING = "FEASIBILITY_RATING"      # Step 5
    RISK_DETERMINATION = "RISK_DETERMINATION"      # Step 6
    TREATMENT_DECISION = "TREATMENT_DECISION"      # Step 7
    GOAL_SETTING = "GOAL_SETTING"                  # Step 8


class AnalysisStatus(str, Enum):
    """TARA Analysis workflow status per data-model.md."""
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REQUIRES_REVISION = "REQUIRES_REVISION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CompletionStatus(str, Enum):
    """Analysis completion status."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VALIDATED = "VALIDATED"
    ARCHIVED = "ARCHIVED"


class GoalStatus(str, Enum):
    """Cybersecurity goal implementation status."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS" 
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"


class ImplementationPhase(str, Enum):
    """Development lifecycle phases."""
    DESIGN = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    INTEGRATION = "INTEGRATION"
    VALIDATION = "VALIDATION"


class ExportFormat(str, Enum):
    """Available export formats per FR-005 and FR-006."""
    JSON = "JSON"
    EXCEL = "EXCEL"
    YAML = "YAML"
    CSV = "CSV"