"""Base TARA agent configuration with Gemini API client integration.

Per research.md lines 44-51: AutoGen 0.7.4 with Gemini API integration
using OpenAI-compatible interface and specialized TARA agent patterns.
"""

import os
from typing import Optional, Dict, Any, List
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import ChatAgent
from autogen_agentchat.messages import ChatMessage

from ..core.config import get_config


class TaraBaseAgent:
    """Base configuration for TARA-specialized AutoGen agents.
    
    Provides Gemini API client setup, common TARA patterns,
    and automotive cybersecurity context management.
    """
    
    def __init__(self, name: str, system_message: str, 
                 model: str = "gemini-2.0-flash",
                 context_buffer_size: int = 5):
        """Initialize base TARA agent configuration.
        
        Args:
            name: Agent identifier for conversation tracking
            system_message: Role-specific system prompt
            model: Gemini model to use (default: gemini-2.0-flash)
            context_buffer_size: Message buffer size for context management
        """
        self.name = name
        self.system_message = system_message
        self.model = model
        self.context_buffer_size = context_buffer_size
        
        # Initialize Gemini API client per research.md authentication pattern
        config = get_config()
        self.model_client = self._create_gemini_client(config.gemini_api_key)
        
        # TARA-specific configuration
        self.automotive_context = self._load_automotive_context()
        self.iso_sections = self._load_iso_21434_references()
        
    def _create_gemini_client(self, api_key: str) -> OpenAIChatCompletionClient:
        """Create Gemini API client using OpenAI-compatible interface.
        
        Per research.md lines 44-51: Uses experimental OpenAI interface
        with custom base URL for Gemini API integration.
        """
        if not api_key:
            raise ValueError("Gemini API key not configured. Set AUTOGT_GEMINI_API_KEY environment variable.")
            
        return OpenAIChatCompletionClient(
            model=self.model,
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            # TARA-optimized configuration per research.md
            max_tokens=4000,
            temperature=0.1,  # Low temperature for consistent cybersecurity analysis
            timeout=30.0,
        )
    
    def _load_automotive_context(self) -> Dict[str, Any]:
        """Load automotive cybersecurity domain knowledge.
        
        Returns domain-specific context for TARA analysis including
        common vehicle assets, threat patterns, and risk factors.
        """
        return {
            "vehicle_assets": [
                "ECU Gateway", "Infotainment System", "Telematics Control Unit",
                "Engine Control Module", "Body Control Module", "CAN Bus Network",
                "Ethernet Backbone", "V2X Communication Module", "OTA Update System",
                "Diagnostics Port", "Wireless Communication", "Sensor Networks"
            ],
            "threat_categories": [
                "Remote Code Execution", "Network Eavesdropping", "Message Injection",
                "Replay Attacks", "Physical Tampering", "Supply Chain Compromise",
                "Firmware Modification", "Key Extraction", "Side Channel Analysis"
            ],
            "automotive_standards": [
                "ISO/SAE 21434", "UN ECE WP.29", "SAE J3061", "ISO 26262",
                "NIST Cybersecurity Framework", "ETSI TS 103 645"
            ],
            "risk_factors": {
                "attack_vectors": ["Network", "Physical", "Supply Chain", "Insider"],
                "asset_criticality": ["Safety-related", "Security-related", "Privacy-related"],
                "impact_domains": ["Vehicle Safety", "Data Privacy", "Financial", "Reputation"]
            }
        }
    
    def _load_iso_21434_references(self) -> Dict[str, str]:
        """Load ISO/SAE 21434 section references for traceability.
        
        Returns mapping of TARA steps to ISO sections for compliance tracking.
        """
        return {
            "asset_identification": "5.4.1",
            "impact_rating": "5.4.2", 
            "threat_scenario_identification": "6.4.2",
            "attack_path_analysis": "6.4.3",
            "attack_feasibility_rating": "6.4.4",
            "impact_determination": "6.4.4",
            "risk_value_determination": "6.4.5",
            "risk_treatment_decision": "7.4.3"
        }
    
    def create_assistant_agent(self, tools: Optional[List] = None) -> AssistantAgent:
        """Create AutoGen AssistantAgent with TARA-specific configuration.
        
        Args:
            tools: Optional list of FunctionTool objects for agent capabilities
            
        Returns:
            Configured AssistantAgent ready for TARA workflow integration
        """
        # Enhanced system message with automotive context
        enhanced_system_message = f"""{self.system_message}

AUTOMOTIVE CYBERSECURITY CONTEXT:
- You are analyzing vehicle systems per ISO/SAE 21434 standard
- Focus on automotive-specific threats and vulnerabilities
- Consider vehicle safety implications in all assessments
- Use automotive industry terminology and standards
- Maintain traceability to ISO sections: {self.iso_sections}

ANALYSIS APPROACH:
- Be systematic and thorough in cybersecurity analysis
- Provide quantitative assessments when possible
- Consider both technical and business impact
- Flag uncertain assessments for manual review
- Document assumptions and decision rationale

AUTOMOTIVE ASSETS CONTEXT:
Common vehicle components: {', '.join(self.automotive_context['vehicle_assets'])}

THREAT LANDSCAPE:
Typical automotive threats: {', '.join(self.automotive_context['threat_categories'])}
"""
        
        agent = AssistantAgent(
            name=self.name,
            model_client=self.model_client,
            system_message=enhanced_system_message,
            tools=tools or []
        )
        
        return agent
    
    def format_tara_output(self, analysis_result: Dict[str, Any], 
                          iso_section: str, confidence_score: float) -> Dict[str, Any]:
        """Format agent output with TARA-specific metadata.
        
        Args:
            analysis_result: Raw analysis output from agent
            iso_section: Relevant ISO/SAE 21434 section
            confidence_score: AI confidence in analysis (0.0-1.0)
            
        Returns:
            Formatted output with TARA metadata for database storage
        """
        return {
            "analysis": analysis_result,
            "metadata": {
                "agent_name": self.name,
                "model_used": self.model,
                "iso_section": iso_section,
                "confidence_score": confidence_score,
                "analysis_timestamp": self._get_timestamp(),
                "automotive_context": True,
                "requires_manual_review": confidence_score < 0.8
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get ISO format timestamp for analysis tracking."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_confidence_score(self, score: float) -> bool:
        """Validate confidence score is within acceptable range.
        
        Per FR-012 multi-factor confidence scoring requirements.
        """
        return 0.0 <= score <= 1.0
    
    def should_flag_for_review(self, confidence_score: float, 
                             complexity_indicators: List[str]) -> bool:
        """Determine if analysis should be flagged for manual review.
        
        Per FR-011 manual review workflow for uncertain assets.
        """
        # Low confidence threshold
        if confidence_score < 0.8:
            return True
            
        # High complexity indicators
        high_complexity_terms = [
            "novel attack", "unknown vulnerability", "complex interaction",
            "multiple dependencies", "regulatory uncertainty"
        ]
        
        for indicator in complexity_indicators:
            if any(term in indicator.lower() for term in high_complexity_terms):
                return True
                
        return False


class TaraAgentError(Exception):
    """Base exception for TARA agent operations."""
    pass


class GeminiAPIError(TaraAgentError):
    """Exception for Gemini API communication issues."""
    pass


class ConfidenceValidationError(TaraAgentError):
    """Exception for confidence score validation failures."""
    pass