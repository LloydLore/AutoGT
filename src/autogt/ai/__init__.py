"""AutoGT AI Module - AutoGen-based TARA Analysis Agents.

This module contains specialized AutoGen agents for automotive cybersecurity
threat analysis and risk assessment (TARA) per ISO/SAE 21434.

Components:
- TaraBaseAgent: Foundation agent with Gemini API integration
- AssetIdentificationAgent: Automated asset discovery and analysis
- ThreatAnalysisAgent: STRIDE-based threat scenario identification  
- RiskAssessmentAgent: Multi-dimensional risk calculation and assessment
- QualityAssuranceAgent: Multi-factor confidence validation per FR-016
- TaraOrchestrator: 8-step TARA workflow coordination and management
- ConfidenceService: Multi-factor confidence assessment service
- ReviewService: Expert review and approval workflow management
"""

from .base_agent import TaraBaseAgent, TaraAgentError
from .asset_agent import AssetIdentificationAgent
from .threat_agent import ThreatAnalysisAgent
from .risk_agent import RiskAssessmentAgent
from .qa_agent import QualityAssuranceAgent
from .orchestrator import TaraOrchestrator, WorkflowPhase
from .confidence_service import (
    ConfidenceService,
    ConfidenceComponents,
    ConfidenceFactor,
    DataCompletenessMetrics,
    ModelConfidenceMetrics,
    ValidationMetrics
)
from .review_service import (
    ReviewService,
    ReviewTask,
    ReviewResult,
    ReviewType,
    ReviewPriority,
    ReviewDecision,
    ReviewCriteria,
    ReviewerRequirements
)

__all__ = [
    # Base agent and error classes
    'TaraBaseAgent',
    'TaraAgentError',
    
    # Specialized TARA agents
    'AssetIdentificationAgent',
    'ThreatAnalysisAgent', 
    'RiskAssessmentAgent',
    'QualityAssuranceAgent',
    
    # Orchestration
    'TaraOrchestrator',
    'WorkflowPhase',
    
    # Confidence assessment
    'ConfidenceService',
    'ConfidenceComponents',
    'ConfidenceFactor',
    'DataCompletenessMetrics',
    'ModelConfidenceMetrics',
    'ValidationMetrics',
    
    # Review and approval
    'ReviewService',
    'ReviewTask',
    'ReviewResult',
    'ReviewType',
    'ReviewPriority',
    'ReviewDecision',
    'ReviewCriteria',
    'ReviewerRequirements'
]

# Module version information
__version__ = "0.1.0"
__author__ = "AutoGT Development Team"
__description__ = "AutoGen-based AI agents for automotive cybersecurity TARA analysis"