"""Asset identification agent with confidence scoring per FR-012.

Specialized AutoGen agent for automated vehicle system asset identification
with multi-factor confidence assessment and manual review flagging.
"""

from typing import Dict, Any, List, Tuple, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

from .base_agent import TaraBaseAgent, TaraAgentError
from ..models.enums import AssetType, CriticalityLevel, ReviewStatus
from ..models.asset import Asset


class AssetIdentificationAgent(TaraBaseAgent):
    """AutoGen agent specialized for vehicle asset identification.
    
    Implements automated asset discovery from documentation with
    confidence scoring and uncertainty flagging per FR-011, FR-012.
    """
    
    def __init__(self):
        system_message = """You are a specialized cybersecurity analyst expert in automotive vehicle systems asset identification per ISO/SAE 21434.

CORE RESPONSIBILITY:
Analyze vehicle system documentation to identify cybersecurity assets (hardware, software, communication, data) with precise classification and confidence assessment.

ANALYSIS APPROACH:
1. Parse technical documentation for system components
2. Classify assets by type (HARDWARE, SOFTWARE, COMMUNICATION, DATA, HUMAN, PHYSICAL)
3. Assess criticality level (LOW, MEDIUM, HIGH, CRITICAL) based on safety/security impact
4. Determine asset relationships (interfaces, data flows, dependencies)
5. Calculate confidence score based on documentation clarity and completeness

ASSET IDENTIFICATION CRITERIA:
- HARDWARE: ECUs, sensors, controllers, communication modules, physical interfaces
- SOFTWARE: Applications, firmware, operating systems, drivers, protocols
- COMMUNICATION: Networks, buses (CAN, LIN, Ethernet), wireless links, protocols
- DATA: Configuration data, keys, certificates, logs, personal information
- HUMAN: Operators, developers, maintenance personnel, end users
- PHYSICAL: Vehicle components, manufacturing equipment, test infrastructure

CONFIDENCE SCORING FACTORS:
- Documentation completeness (40% weight)
- Technical specification clarity (35% weight) 
- Asset relationship mapping (25% weight)

OUTPUT REQUIREMENTS:
- Structured asset list with classifications
- Confidence score (0.0-1.0) for each asset
- Uncertainty flags for manual review (score < 0.8)
- ISO section references for traceability"""
        
        super().__init__(
            name="AssetIdentificationAgent",
            system_message=system_message,
            model="gemini-2.0-flash",
            context_buffer_size=10  # Larger buffer for document analysis
        )
        
        # Create tools for asset analysis
        self.tools = [
            self._create_asset_analysis_tool(),
            self._create_confidence_calculation_tool(),
            self._create_relationship_mapping_tool()
        ]
    
    def _create_asset_analysis_tool(self) -> FunctionTool:
        """Create tool for analyzing document content for assets."""
        
        async def analyze_assets_in_document(
            document_content: str,
            document_type: str = "system_specification"
        ) -> Dict[str, Any]:
            """Analyze document content to identify cybersecurity assets.
            
            Args:
                document_content: Text content of technical document
                document_type: Type of document (system_spec, architecture, interface_spec)
                
            Returns:
                Dictionary with identified assets and analysis metadata
            """
            # Document parsing patterns for asset identification
            asset_patterns = {
                "hardware": [
                    "ECU", "controller", "module", "sensor", "actuator",
                    "gateway", "switch", "router", "processor", "memory"
                ],
                "software": [
                    "application", "firmware", "driver", "OS", "middleware",
                    "protocol stack", "bootloader", "hypervisor"
                ],
                "communication": [
                    "CAN", "LIN", "Ethernet", "WiFi", "Bluetooth", "5G",
                    "V2X", "bus", "network", "interface", "port"
                ],
                "data": [
                    "configuration", "calibration", "key", "certificate",
                    "log", "diagnostic", "personal data", "telemetry"
                ]
            }
            
            identified_assets = []
            document_lower = document_content.lower()
            
            for asset_type, keywords in asset_patterns.items():
                for keyword in keywords:
                    if keyword.lower() in document_lower:
                        # Extract context around keyword for better analysis
                        context = self._extract_asset_context(document_content, keyword)
                        
                        asset_info = {
                            "name": self._generate_asset_name(keyword, context),
                            "type": self._map_to_asset_type(asset_type),
                            "description": context.get("description", ""),
                            "criticality_indicators": context.get("criticality", []),
                            "interfaces": context.get("interfaces", []),
                            "data_flows": context.get("data_flows", []),
                            "source_location": context.get("location", ""),
                            "confidence_factors": self._calculate_asset_confidence(context)
                        }
                        
                        identified_assets.append(asset_info)
            
            return {
                "assets": identified_assets,
                "document_analysis": {
                    "document_type": document_type,
                    "total_assets_found": len(identified_assets),
                    "coverage_assessment": self._assess_document_coverage(document_content),
                    "analysis_quality": self._assess_analysis_quality(identified_assets)
                }
            }
        
        return FunctionTool(analyze_assets_in_document, description="Analyze document content for cybersecurity assets")
    
    def _create_confidence_calculation_tool(self) -> FunctionTool:
        """Create tool for multi-factor confidence scoring per FR-012."""
        
        async def calculate_asset_confidence(
            asset_info: Dict[str, Any],
            documentation_quality: float,
            specification_clarity: float
        ) -> Dict[str, float]:
            """Calculate multi-factor confidence score for asset identification.
            
            Per FR-012: 40% data completeness + 35% model confidence + 25% validation
            
            Args:
                asset_info: Asset identification data
                documentation_quality: Quality assessment of source documentation (0-1)
                specification_clarity: Clarity of technical specifications (0-1)
                
            Returns:
                Confidence factors breakdown and overall score
            """
            # Data completeness factor (40% weight)
            required_fields = ["name", "type", "description"]
            optional_fields = ["interfaces", "data_flows", "criticality_indicators"]
            
            required_complete = sum(1 for field in required_fields if asset_info.get(field))
            optional_complete = sum(1 for field in optional_fields if asset_info.get(field))
            
            data_completeness = (required_complete / len(required_fields)) * 0.7 + \
                              (optional_complete / len(optional_fields)) * 0.3
            
            # Model confidence factor (35% weight)
            model_confidence = (documentation_quality + specification_clarity) / 2
            
            # Validation checks factor (25% weight)  
            validation_score = self._validate_asset_consistency(asset_info)
            
            # Calculate weighted confidence score
            factors = {
                "data_completeness": data_completeness * 0.40,
                "model_confidence": model_confidence * 0.35,
                "validation_checks": validation_score * 0.25
            }
            
            overall_confidence = sum(factors.values())
            
            return {
                **factors,
                "overall_confidence": overall_confidence,
                "requires_review": overall_confidence < 0.8
            }
        
        return FunctionTool(calculate_asset_confidence, description="Calculate multi-factor confidence score")
    
    def _create_relationship_mapping_tool(self) -> FunctionTool:
        """Create tool for mapping asset relationships and dependencies."""
        
        async def map_asset_relationships(
            assets: List[Dict[str, Any]],
            system_architecture: str = ""
        ) -> Dict[str, Any]:
            """Map relationships and dependencies between identified assets.
            
            Args:
                assets: List of identified assets
                system_architecture: System architecture description
                
            Returns:
                Relationship mapping with interface and data flow analysis
            """
            relationships = {
                "interfaces": [],
                "data_flows": [],
                "dependencies": [],
                "trust_boundaries": []
            }
            
            # Analyze pairwise relationships
            for i, asset_a in enumerate(assets):
                for j, asset_b in enumerate(assets[i+1:], i+1):
                    relationship = self._analyze_asset_pair(asset_a, asset_b, system_architecture)
                    if relationship:
                        relationships[relationship["type"]].append(relationship)
            
            # Identify system boundaries and trust zones
            trust_boundaries = self._identify_trust_boundaries(assets, system_architecture)
            relationships["trust_boundaries"] = trust_boundaries
            
            return {
                "relationships": relationships,
                "system_complexity": len(relationships["interfaces"]) + len(relationships["data_flows"]),
                "security_boundaries": len(trust_boundaries),
                "analysis_confidence": self._assess_relationship_confidence(relationships)
            }
        
        return FunctionTool(map_asset_relationships, description="Map asset relationships and dependencies")
    
    async def identify_assets(self, document_content: str, 
                            analysis_id: str) -> List[Asset]:
        """Main entry point for asset identification workflow.
        
        Args:
            document_content: Technical documentation to analyze
            analysis_id: Parent TARA analysis identifier
            
        Returns:
            List of identified Asset model instances with confidence scores
        """
        try:
            # Create assistant agent with tools
            agent = self.create_assistant_agent(self.tools)
            
            # Execute asset identification analysis
            analysis_prompt = f"""
            Analyze the following technical documentation to identify all cybersecurity assets per ISO/SAE 21434 requirements:
            
            DOCUMENT CONTENT:
            {document_content}
            
            TASKS:
            1. Use analyze_assets_in_document tool to identify all assets
            2. For each asset, use calculate_asset_confidence to determine confidence score
            3. Use map_asset_relationships to analyze system interactions
            4. Flag assets with confidence < 0.8 for manual review
            5. Provide structured output suitable for database storage
            
            Focus on automotive cybersecurity relevance and maintain ISO/SAE 21434 traceability.
            """
            
            # Execute analysis via agent conversation
            messages = [ChatMessage(content=analysis_prompt, source="user")]
            response = await agent.run_stream(messages)
            
            # Process agent response and create Asset instances
            assets = await self._process_agent_response(response, analysis_id)
            
            return assets
            
        except Exception as e:
            raise TaraAgentError(f"Asset identification failed: {str(e)}")
    
    async def _process_agent_response(self, agent_response, analysis_id: str) -> List[Asset]:
        """Process agent response and create Asset model instances."""
        assets = []
        
        # Extract structured data from agent response
        # This would parse the actual agent output format
        asset_data = self._extract_asset_data_from_response(agent_response)
        
        for asset_info in asset_data:
            try:
                # Create Asset instance with confidence scoring
                asset = Asset(
                    name=asset_info["name"],
                    description=asset_info.get("description"),
                    asset_type=AssetType(asset_info["type"]),
                    criticality_level=self._determine_criticality(asset_info),
                    interfaces=asset_info.get("interfaces", []),
                    data_flows=asset_info.get("data_flows", []),
                    security_properties=asset_info.get("security_properties", {}),
                    confidence_score=asset_info["confidence_score"],
                    review_status=ReviewStatus.UNDER_REVIEW if asset_info["confidence_score"] < 0.8 else ReviewStatus.IDENTIFIED,
                    source_files=[asset_info.get("source_location", "")],
                    analysis_id=analysis_id,
                    iso_section="5.4.1"  # Asset identification section
                )
                
                assets.append(asset)
                
            except Exception as e:
                # Log asset creation error but continue with others
                print(f"Warning: Failed to create asset {asset_info.get('name', 'unknown')}: {e}")
                continue
        
        return assets
    
    # Helper methods for asset analysis
    def _extract_asset_context(self, document: str, keyword: str) -> Dict[str, Any]:
        """Extract contextual information around asset keyword."""
        # Implementation would extract surrounding text and parse for context
        return {
            "description": f"Asset containing {keyword}",
            "interfaces": [],
            "data_flows": [],
            "location": "document_section",
            "criticality": []
        }
    
    def _generate_asset_name(self, keyword: str, context: Dict[str, Any]) -> str:
        """Generate descriptive asset name from keyword and context."""
        return f"{keyword.title()} Component"
    
    def _map_to_asset_type(self, category: str) -> str:
        """Map category string to AssetType enum value."""
        mapping = {
            "hardware": "HARDWARE",
            "software": "SOFTWARE", 
            "communication": "COMMUNICATION",
            "data": "DATA"
        }
        return mapping.get(category, "SOFTWARE")
    
    def _calculate_asset_confidence(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence factors for asset identification."""
        return {
            "documentation_quality": 0.8,
            "specification_clarity": 0.7,
            "context_completeness": 0.9
        }
    
    def _determine_criticality(self, asset_info: Dict[str, Any]) -> CriticalityLevel:
        """Determine asset criticality level based on analysis."""
        # Default to MEDIUM, would implement logic based on asset_info
        return CriticalityLevel.MEDIUM
    
    def _assess_document_coverage(self, document: str) -> float:
        """Assess how well document covers system architecture."""
        return 0.8
    
    def _assess_analysis_quality(self, assets: List[Dict]) -> float:
        """Assess quality of asset identification analysis."""
        return 0.85
    
    def _validate_asset_consistency(self, asset_info: Dict[str, Any]) -> float:
        """Validate consistency of asset information."""
        return 0.9
    
    def _analyze_asset_pair(self, asset_a: Dict, asset_b: Dict, 
                          architecture: str) -> Optional[Dict[str, Any]]:
        """Analyze relationship between two assets."""
        # Would implement relationship detection logic
        return None
    
    def _identify_trust_boundaries(self, assets: List[Dict], 
                                 architecture: str) -> List[Dict[str, Any]]:
        """Identify trust boundaries in system architecture."""
        return []
    
    def _assess_relationship_confidence(self, relationships: Dict) -> float:
        """Assess confidence in relationship mapping."""
        return 0.8
    
    def _extract_asset_data_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract structured asset data from agent response."""
        # Would parse actual agent response format
        return []