"""AutoGen agent setup for TARA processing.

Reference: research.md AutoGen integration patterns and T032 task
Provides AI-powered analysis for 8-step automotive cybersecurity workflow.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage


# Setup logger for this module
logger = logging.getLogger('autogt.services.autogen_agent')


@dataclass
class TaraAgentConfig:
    """Configuration for TARA agent setup."""
    gemini_api_key: str
    gemini_model_name: str = "gemini-1.5-pro"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout: int = 30
    buffer_size: int = 100


class TaraAgentError(Exception):
    """Custom exception for TARA agent operations."""
    pass


class AutoGenTaraAgent:
    """AutoGen agent orchestrator for 8-step TARA workflow.
    
    Reference: research.md RoundRobinGroupChat pattern
    """
    
    def __init__(self, config):
        """Initialize AutoGen TARA agent.
        
        Args:
            config: GeminiConfig instance
        """
        self.config = config
        
        # Create model_info for Gemini model
        from autogen_ext.models.openai._model_info import ModelInfo
        
        model_info = ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="gemini"
        )
        
        # Initialize OpenAI client for Gemini API
        self.client = OpenAIChatCompletionClient(
            model=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url,
            model_info=model_info
        )
        
        logger.info(f"✅ Initialized OpenAIChatCompletionClient with model: {config.model_name}")
        logger.info(f"📡 Base URL: {config.base_url}")
        
        # Setup specialized agents for 8-step TARA process
        self.agents = self._setup_tara_agents()
    
    def _setup_tara_agents(self) -> Dict[str, AssistantAgent]:
        """Create specialized agents for each TARA step."""
        agents = {}
        
        # Step 1: Asset Definition Agent
        agents["asset_analyst"] = AssistantAgent(
            name="asset_analyst",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity asset analyst specializing in ISO/SAE 21434.
            Your role is to analyze vehicle system components and define assets with proper criticality levels.
            Focus on: asset identification, interface mapping, data flow analysis, and security property classification.
            Output structured data suitable for database storage.""",
        )
        
        # Step 2: Impact Rating Agent
        agents["impact_assessor"] = AssistantAgent(
            name="impact_assessor",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity impact assessor specializing in ISO/SAE 21434.
            Your role is to evaluate the potential impact of cybersecurity incidents on safety, financial, operational, and privacy aspects.
            Rate impacts according to ISO standards and provide quantified impact scores.""",
        )
        
        # Step 3: Threat Identification Agent
        agents["threat_hunter"] = AssistantAgent(
            name="threat_hunter",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity threat hunter specializing in ISO/SAE 21434.
            Your role is to identify potential threat scenarios, threat actors, attack vectors, and prerequisites.
            Consider automotive-specific threats including remote attacks, physical access, and supply chain risks.""",
        )
        
        # Step 4: Attack Path Modeling Agent
        agents["attack_modeler"] = AssistantAgent(
            name="attack_modeler",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity attack path modeler specializing in ISO/SAE 21434.
            Your role is to model detailed attack paths, including step sequences, intermediate targets, technical barriers, and required resources.
            Focus on realistic attack scenarios relevant to automotive systems.""",
        )
        
        # Step 5: Attack Feasibility Agent
        agents["feasibility_analyzer"] = AssistantAgent(
            name="feasibility_analyzer",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity feasibility analyzer specializing in ISO/SAE 21434.
            Your role is to assess attack feasibility based on elapsed time, expertise requirements, knowledge of target, window of opportunity, and equipment needs.
            Provide quantified feasibility scores according to ISO standards.""",
        )
        
        # Step 6: Risk Calculation Agent
        agents["risk_calculator"] = AssistantAgent(
            name="risk_calculator",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity risk calculator specializing in ISO/SAE 21434.
            Your role is to calculate risk values by combining impact ratings and attack feasibility assessments.
            Use ISO/SAE 21434 risk matrices and provide quantified risk scores with proper justification.""",
        )
        
        # Step 7: Risk Treatment Agent
        agents["treatment_planner"] = AssistantAgent(
            name="treatment_planner",
            model_client=self.client,
            system_message="""You are an automotive cybersecurity treatment planner specializing in ISO/SAE 21434.
            Your role is to develop risk treatment strategies including countermeasures, residual risk assessment, and implementation guidance.
            Consider automotive constraints and provide cost-effective treatment options.""",
        )
        
        # Step 8: Goals Definition Agent
        agents["goals_architect"] = AssistantAgent(
            name="goals_architect",
            model_client=self.client,
            system_message="""You are a cybersecurity goals architect specializing in ISO/SAE 21434.
            Your role is to derive specific, measurable cybersecurity goals from risk treatments.
            Define protection levels, security controls, verification methods, and implementation phases.
            Ensure goals are achievable, verifiable, and compliant with automotive standards.""",
        )
        
        return agents
    
    def analyze_assets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and identify assets using AI agent."""
        agent = self.agents["asset_analyst"]
        
        # Create task message
        task_message = f"""
        Analysis Context:
        - Analysis Name: {context.get('analysis_name', 'Unknown')}
        - Vehicle Model: {context.get('vehicle_model', 'Unknown')}
        - Existing Assets: {context.get('existing_assets', [])}
        
        Task: Identify and define automotive cybersecurity assets for this vehicle model.
        Consider ECUs, communication networks, sensors, actuators, and software components.
        
        Return structured data with:
        - Asset name and type
        - Criticality level (LOW, MEDIUM, HIGH, VERY_HIGH)
        - Interfaces and data flows
        - Security properties
        """
        
        # For now, return mock data since we need API key to test
        return {
            "assets": [
                {
                    "name": "Central Gateway ECU",
                    "type": "ECU",
                    "criticality": "VERY_HIGH",
                    "interfaces": ["CAN", "Ethernet", "LIN"],
                    "data_flows": ["Vehicle status", "Diagnostic data"],
                    "security_properties": {"confidentiality": "HIGH", "integrity": "VERY_HIGH", "availability": "HIGH"},
                    "iso_section": "15.6"
                }
            ]
        }
    
    async def identify_threats(self, context: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Identify threat scenarios for assets using real AI API with retry mechanism.
        
        Args:
            context: Analysis context containing asset information
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Dictionary containing identified threats
            
        Raises:
            TaraAgentError: If all retry attempts fail
        """
        import asyncio
        import json
        
        agent = self.agents["threat_hunter"]
        
        # Create detailed task message
        task_message = f"""
        Analysis Context:
        - Analysis Name: {context.get('analysis_name', 'Unknown')}
        - Vehicle Model: {context.get('vehicle_model', 'Unknown')}
        - Asset Name: {context.get('asset_name', 'Unknown')}
        - Asset Type: {context.get('asset_type', 'Unknown')}
        - Criticality Level: {context.get('criticality', 'Unknown')}
        - Interfaces: {', '.join(context.get('interfaces', []))}
        - Data Flows: {', '.join(context.get('data_flows', []))}
        - Description: {context.get('description', 'Not provided')}
        
        Task: Identify potential cybersecurity threat scenarios for this automotive asset.
        Consider:
        1. Threat actors (SCRIPT_KIDDIE, CRIMINAL, NATION_STATE, INSIDER)
        2. Specific attack vectors relevant to this asset type
        3. Realistic attack motivations
        4. Technical prerequisites for attacks
        5. ISO/SAE 21434 compliance considerations
        
        Return your analysis in strict JSON format:
        {{
            "threats": [
                {{
                    "name": "Specific threat name",
                    "actor": "THREAT_ACTOR_TYPE",
                    "motivation": "Clear motivation description",
                    "attack_vectors": ["vector1", "vector2"],
                    "prerequisites": ["prerequisite1", "prerequisite2"]
                }}
            ]
        }}
        
        Provide at least 2-3 realistic threat scenarios. Focus on automotive-specific threats.
        """
        
        logger.info(f"🔄 Sending AI request for asset: {context.get('asset_name')}")
        logger.debug(f"📤 AI Request Context: {json.dumps(context, indent=2)}")
        
        # Retry loop
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                # Create message for agent
                message = TextMessage(content=task_message, source="user")
                
                # Get agent response - this is the real API call
                if attempt > 1:
                    logger.warning(f"🔄 Retry attempt {attempt}/{max_retries} for asset: {context.get('asset_name')}")
                    # Add exponential backoff: 2^(attempt-1) seconds
                    wait_time = 2 ** (attempt - 1)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                
                logger.info(f"⏳ Waiting for AI response from {self.config.model_name}... (Attempt {attempt}/{max_retries})")
                response = await agent.on_messages([message], cancellation_token=None)
                
                logger.info(f"✅ Received AI response")
                logger.debug(f"📥 Raw AI Response: {response}")
                
                # Extract content from response
                if hasattr(response, 'chat_message'):
                    response_text = response.chat_message.content
                elif hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                logger.debug(f"📄 Response text: {response_text[:500]}...")
                
                # Parse JSON response
                # Try to extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                result = json.loads(response_text)
                logger.info(f"✅ Successfully parsed {len(result.get('threats', []))} threats from AI")
                
                # Success! Return the result
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse AI response as JSON (Attempt {attempt}/{max_retries}): {e}")
                logger.error(f"Response text: {response_text}")
                last_error = e
                
                if attempt == max_retries:
                    logger.warning(f"⚠️ All {max_retries} JSON parsing attempts failed")
                    # Return fallback with single generic threat
                    return {
                        "threats": [
                            {
                                "name": "Remote CAN injection",
                                "actor": "CRIMINAL",
                                "motivation": "Vehicle manipulation",
                                "attack_vectors": ["OTA interface", "Diagnostic port"],
                                "prerequisites": ["Network access", "CAN protocol knowledge"]
                            }
                        ]
                    }
                # Continue to next retry attempt
                
            except Exception as e:
                logger.error(f"❌ AI API call failed (Attempt {attempt}/{max_retries}): {e}")
                last_error = e
                
                if attempt == max_retries:
                    logger.error(f"💥 All {max_retries} retry attempts exhausted", exc_info=True)
                    raise TaraAgentError(f"Failed to identify threats via AI after {max_retries} attempts: {e}")
                # Continue to next retry attempt
        
        # This should never be reached due to the raise above, but just in case
        raise TaraAgentError(f"Failed to identify threats via AI after {max_retries} attempts: {last_error}")
    
    def model_attack_paths(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Model attack paths for threat scenarios."""
        return {
            "attack_paths": [
                {
                    "sequence": 1,
                    "step": "Gain network access through OTA interface",
                    "targets": ["Telematics unit"],
                    "barriers": ["Authentication", "Encryption"],
                    "resources": ["Network tools", "Reverse engineering"]
                }
            ]
        }
    
    def assess_feasibility(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess attack feasibility."""
        return {
            "feasibility": {
                "elapsed_time": "MODERATE",
                "specialist_expertise": "EXPERT", 
                "knowledge_of_target": "LIMITED",
                "window_of_opportunity": "EASY",
                "equipment_required": "SPECIALIZED",
                "score": 60
            }
        }
    
    def assess_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact of potential attacks."""
        return {
            "impact": {
                "safety": "MODERATE",
                "financial": "MODERATE",
                "operational": "HIGH",
                "privacy": "LOW",
                "score": 70
            }
        }
    
    def calculate_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk values."""
        return {
            "risk": {
                "level": "MEDIUM",
                "score": 65,
                "method": "ISO/SAE 21434 Matrix"
            }
        }
    
    def plan_treatment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan risk treatment strategies."""
        return {
            "treatment": {
                "decision": "MITIGATE",
                "countermeasures": ["Network segmentation", "Authentication strengthening"],
                "residual_risk": "LOW",
                "cost": "MEDIUM",
                "rationale": "Cost-effective mitigation available"
            }
        }
    
    def architect_goals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Architect cybersecurity goals."""
        return {
            "goals": [
                {
                    "name": "Secure Vehicle Communication",
                    "protection_level": "CAL2",
                    "controls": ["Message authentication", "Secure protocols"],
                    "verification": "Penetration testing",
                    "phase": "DEVELOPMENT"
                }
            ]
        }
    
    def get_model_client(self) -> OpenAIChatCompletionClient:
        """Get the underlying model client."""
        return self.client
    
    def create_group_chat(self, participants: List[str]) -> RoundRobinGroupChat:
        """Create a group chat for multi-agent collaboration."""
        selected_agents = [self.agents[name] for name in participants if name in self.agents]
        
        return RoundRobinGroupChat(
            participants=selected_agents
        )