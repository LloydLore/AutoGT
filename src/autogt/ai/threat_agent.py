"""Threat analysis agent with automotive patterns per research.md lines 24-33.

Specialized AutoGen agent for STRIDE threat identification and attack path
modeling for vehicle systems with automotive-specific threat patterns.
"""

from typing import Dict, Any, List, Tuple, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

from .base_agent import TaraBaseAgent, TaraAgentError
from ..models.enums import ThreatCategory, AttackVector, AttackComplexity, ReviewStatus
from ..models.threat_scenario import ThreatScenario
from ..models.asset import Asset


class ThreatAnalysisAgent(TaraBaseAgent):
    """AutoGen agent specialized for automotive threat scenario identification.
    
    Implements STRIDE-based threat modeling with vehicle-specific attack patterns,
    MITRE ATT&CK mapping, and attack path analysis per ISO/SAE 21434.
    """
    
    def __init__(self):
        system_message = """You are a specialized automotive cybersecurity analyst expert in threat scenario identification per ISO/SAE 21434 and STRIDE methodology.

CORE RESPONSIBILITY:
Analyze vehicle assets to identify credible cybersecurity threats using STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) with automotive-specific attack patterns.

STRIDE ANALYSIS FOR AUTOMOTIVE:
- SPOOFING: Identity spoofing of ECUs, sensors, communication endpoints, user interfaces
- TAMPERING: Modification of firmware, configuration data, communication messages, physical components
- REPUDIATION: Denial of actions in diagnostics, logging, audit trails, vehicle events
- INFORMATION_DISCLOSURE: Exposure of keys, personal data, vehicle data, diagnostic information
- DENIAL_OF_SERVICE: Disruption of critical functions, network flooding, resource exhaustion
- ELEVATION_OF_PRIVILEGE: Gaining unauthorized access to restricted ECU functions, root privileges

AUTOMOTIVE THREAT LANDSCAPE:
- Remote attacks via wireless interfaces (cellular, WiFi, Bluetooth, V2X)
- Network-based attacks on CAN/LIN buses and Ethernet backbones
- Physical attacks via OBD-II port, direct ECU access, hardware tampering
- Supply chain attacks through compromised components or update mechanisms
- Insider threats from development, manufacturing, or service personnel

ATTACK VECTOR ANALYSIS:
- NETWORK: Remote attacks via wireless/cellular connections
- ADJACENT: Attacks requiring proximity (WiFi, Bluetooth range)
- LOCAL: Attacks requiring physical vehicle access (OBD-II, direct ECU)
- PHYSICAL: Attacks requiring hardware access/modification

ATTACK COMPLEXITY ASSESSMENT:
- LOW: Simple attacks with standard tools and basic skills
- HIGH: Complex attacks requiring specialized knowledge, tools, or coordination

OUTPUT REQUIREMENTS:
- STRIDE-classified threat scenarios for each asset
- Attack vector and complexity assessment per CVSS methodology
- Attack path modeling with step-by-step progression
- MITRE ATT&CK tactics and techniques mapping
- Automotive industry context and real-world examples
- Confidence scoring and uncertainty flagging"""
        
        super().__init__(
            name="ThreatAnalysisAgent",
            system_message=system_message,
            model="gemini-2.0-flash",
            context_buffer_size=15  # Larger buffer for complex threat analysis
        )
        
        # Automotive threat patterns database
        self.threat_patterns = self._load_automotive_threat_patterns()
        
        # Create tools for threat analysis
        self.tools = [
            self._create_stride_analysis_tool(),
            self._create_attack_path_modeling_tool(),
            self._create_threat_intelligence_tool(),
            self._create_mitre_mapping_tool()
        ]
    
    def _load_automotive_threat_patterns(self) -> Dict[str, Any]:
        """Load automotive-specific threat patterns and attack techniques."""
        return {
            "remote_attacks": {
                "cellular_exploitation": {
                    "description": "Exploitation of cellular modem vulnerabilities",
                    "attack_vectors": ["NETWORK"],
                    "target_assets": ["Telematics Control Unit", "OTA Update System"],
                    "stride_categories": ["SPOOFING", "TAMPERING", "ELEVATION_OF_PRIVILEGE"],
                    "mitre_tactics": ["T1190", "T1055", "T1068"]
                },
                "wifi_attacks": {
                    "description": "WiFi network attacks on infotainment systems",
                    "attack_vectors": ["ADJACENT"],
                    "target_assets": ["Infotainment System", "WiFi Module"],
                    "stride_categories": ["SPOOFING", "INFORMATION_DISCLOSURE"],
                    "mitre_tactics": ["T1200", "T1557", "T1040"]
                }
            },
            "network_attacks": {
                "can_bus_injection": {
                    "description": "Malicious CAN message injection attacks",
                    "attack_vectors": ["LOCAL"],
                    "target_assets": ["CAN Bus Network", "ECU Gateway"],
                    "stride_categories": ["TAMPERING", "DENIAL_OF_SERVICE"],
                    "mitre_tactics": ["T1200", "T1499"]
                },
                "ethernet_exploitation": {
                    "description": "Exploitation of Ethernet backbone vulnerabilities",
                    "attack_vectors": ["ADJACENT", "LOCAL"],
                    "target_assets": ["Ethernet Backbone", "ECU Gateway"],
                    "stride_categories": ["SPOOFING", "TAMPERING", "INFORMATION_DISCLOSURE"],
                    "mitre_tactics": ["T1557", "T1040", "T1498"]
                }
            },
            "physical_attacks": {
                "obd_exploitation": {
                    "description": "OBD-II port exploitation for system access",
                    "attack_vectors": ["PHYSICAL"],
                    "target_assets": ["Diagnostics Port", "CAN Bus Network"],
                    "stride_categories": ["ELEVATION_OF_PRIVILEGE", "TAMPERING"],
                    "mitre_tactics": ["T1200", "T1055"]
                },
                "ecu_tampering": {
                    "description": "Physical ECU modification and firmware tampering",
                    "attack_vectors": ["PHYSICAL"],
                    "target_assets": ["Engine Control Module", "Body Control Module"],
                    "stride_categories": ["TAMPERING", "ELEVATION_OF_PRIVILEGE"],
                    "mitre_tactics": ["T1542", "T1601"]
                }
            }
        }
    
    def _create_stride_analysis_tool(self) -> FunctionTool:
        """Create tool for STRIDE-based threat identification."""
        
        async def analyze_stride_threats(
            asset_name: str,
            asset_type: str,
            asset_interfaces: List[str],
            system_context: str = ""
        ) -> Dict[str, Any]:
            """Analyze asset for STRIDE threats with automotive context.
            
            Args:
                asset_name: Name of the asset to analyze
                asset_type: Type of asset (HARDWARE, SOFTWARE, etc.)
                asset_interfaces: List of asset interfaces/connections
                system_context: Additional system architecture context
                
            Returns:
                Dictionary with STRIDE threat analysis results
            """
            stride_threats = {
                "SPOOFING": [],
                "TAMPERING": [],
                "REPUDIATION": [],
                "INFORMATION_DISCLOSURE": [],
                "DENIAL_OF_SERVICE": [],
                "ELEVATION_OF_PRIVILEGE": []
            }
            
            # Analyze each STRIDE category for the asset
            for category in stride_threats.keys():
                threats = self._identify_stride_threats(
                    category, asset_name, asset_type, asset_interfaces, system_context
                )
                stride_threats[category] = threats
            
            # Calculate threat scenario confidence and complexity
            threat_scenarios = []
            for category, threats in stride_threats.items():
                for threat in threats:
                    scenario = {
                        "name": threat["name"],
                        "description": threat["description"],
                        "stride_category": category,
                        "attack_vector": threat["attack_vector"],
                        "attack_complexity": threat["attack_complexity"],
                        "confidence_score": threat["confidence"],
                        "automotive_relevance": threat["automotive_context"]
                    }
                    threat_scenarios.append(scenario)
            
            return {
                "asset_name": asset_name,
                "stride_analysis": stride_threats,
                "threat_scenarios": threat_scenarios,
                "total_threats": len(threat_scenarios),
                "high_confidence_threats": len([t for t in threat_scenarios if t["confidence_score"] > 0.8])
            }
        
        return FunctionTool(analyze_stride_threats, description="Analyze asset for STRIDE threats")
    
    def _create_attack_path_modeling_tool(self) -> FunctionTool:
        """Create tool for modeling attack paths and sequences."""
        
        async def model_attack_path(
            threat_scenario: Dict[str, Any],
            target_asset: str,
            system_topology: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Model detailed attack path for threat scenario.
            
            Args:
                threat_scenario: Threat scenario to analyze
                target_asset: Target asset name
                system_topology: System network topology information
                
            Returns:
                Detailed attack path with steps and prerequisites
            """
            attack_path = {
                "threat_name": threat_scenario["name"],
                "target_asset": target_asset,
                "attack_steps": [],
                "prerequisites": [],
                "entry_points": [],
                "success_conditions": [],
                "detection_opportunities": []
            }
            
            # Generate attack path based on threat category and vector
            stride_category = threat_scenario.get("stride_category")
            attack_vector = threat_scenario.get("attack_vector")
            
            if attack_vector == "NETWORK":
                attack_path = self._model_network_attack_path(threat_scenario, target_asset)
            elif attack_vector == "ADJACENT":
                attack_path = self._model_adjacent_attack_path(threat_scenario, target_asset)
            elif attack_vector == "LOCAL":
                attack_path = self._model_local_attack_path(threat_scenario, target_asset)
            elif attack_vector == "PHYSICAL":
                attack_path = self._model_physical_attack_path(threat_scenario, target_asset)
            
            # Add automotive-specific context
            attack_path["automotive_context"] = self._add_automotive_attack_context(
                stride_category, attack_vector, target_asset
            )
            
            return attack_path
        
        return FunctionTool(model_attack_path, description="Model detailed attack paths")
    
    def _create_threat_intelligence_tool(self) -> FunctionTool:
        """Create tool for integrating automotive threat intelligence."""
        
        async def lookup_threat_intelligence(
            threat_type: str,
            asset_category: str
        ) -> Dict[str, Any]:
            """Lookup relevant threat intelligence for automotive context.
            
            Args:
                threat_type: Type of threat (e.g., "remote_code_execution")
                asset_category: Category of target asset
                
            Returns:
                Threat intelligence data including CVEs, real-world examples
            """
            # Simulate threat intelligence lookup
            intelligence = {
                "cve_references": self._lookup_automotive_cves(threat_type, asset_category),
                "real_world_incidents": self._lookup_real_incidents(threat_type),
                "attack_campaigns": self._lookup_attack_campaigns(asset_category),
                "mitigation_strategies": self._lookup_mitigations(threat_type),
                "industry_alerts": self._lookup_industry_alerts(threat_type, asset_category)
            }
            
            return intelligence
        
        return FunctionTool(lookup_threat_intelligence, description="Lookup automotive threat intelligence")
    
    def _create_mitre_mapping_tool(self) -> FunctionTool:
        """Create tool for MITRE ATT&CK mapping."""
        
        async def map_to_mitre_attack(
            threat_scenario: Dict[str, Any],
            attack_path: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Map threat scenario to MITRE ATT&CK framework.
            
            Args:
                threat_scenario: Threat scenario to map
                attack_path: Attack path details
                
            Returns:
                MITRE ATT&CK mapping with tactics and techniques
            """
            mitre_mapping = {
                "tactics": [],
                "techniques": [],
                "sub_techniques": [],
                "automotive_relevance": {}
            }
            
            # Map based on STRIDE category and attack vector
            stride_category = threat_scenario.get("stride_category")
            attack_vector = threat_scenario.get("attack_vector")
            
            # Add tactics based on STRIDE category
            if stride_category == "SPOOFING":
                mitre_mapping["tactics"].extend(["Defense Evasion", "Credential Access"])
                mitre_mapping["techniques"].extend(["T1557", "T1200"])
            elif stride_category == "TAMPERING":
                mitre_mapping["tactics"].extend(["Defense Evasion", "Impact"])
                mitre_mapping["techniques"].extend(["T1601", "T1542"])
            elif stride_category == "ELEVATION_OF_PRIVILEGE":
                mitre_mapping["tactics"].extend(["Privilege Escalation", "Defense Evasion"])
                mitre_mapping["techniques"].extend(["T1068", "T1055"])
            
            # Add automotive-specific context
            mitre_mapping["automotive_relevance"] = {
                "vehicle_systems_impact": True,
                "safety_implications": stride_category in ["TAMPERING", "DENIAL_OF_SERVICE"],
                "regulatory_concern": True
            }
            
            return mitre_mapping
        
        return FunctionTool(map_to_mitre_attack, description="Map threats to MITRE ATT&CK")
    
    async def analyze_threats_for_asset(self, asset: Asset, 
                                      system_context: str = "") -> List[ThreatScenario]:
        """Main entry point for threat analysis workflow.
        
        Args:
            asset: Asset model instance to analyze for threats
            system_context: Additional system architecture context
            
        Returns:
            List of identified ThreatScenario instances with attack paths
        """
        try:
            # Create assistant agent with tools
            agent = self.create_assistant_agent(self.tools)
            
            # Execute threat analysis
            analysis_prompt = f"""
            Perform comprehensive STRIDE threat analysis for the following automotive asset:
            
            ASSET DETAILS:
            Name: {asset.name}
            Type: {asset.asset_type.value}
            Criticality: {asset.criticality_level.value}
            Interfaces: {asset.interfaces or []}
            Data Flows: {asset.data_flows or []}
            
            SYSTEM CONTEXT:
            {system_context}
            
            ANALYSIS TASKS:
            1. Use analyze_stride_threats to identify all STRIDE threats for this asset
            2. For each high-confidence threat, use model_attack_path to create detailed attack sequences
            3. Use lookup_threat_intelligence to enrich with automotive CVEs and incidents
            4. Use map_to_mitre_attack to map threats to MITRE ATT&CK framework
            5. Focus on automotive-specific attack vectors and real-world feasibility
            6. Consider safety implications for vehicle operation
            
            Provide structured output suitable for ThreatScenario database storage.
            """
            
            # Execute analysis via agent conversation
            messages = [{"role": "user", "content": analysis_prompt}]
            response = await agent.run_stream(messages)
            
            # Process agent response and create ThreatScenario instances
            threat_scenarios = await self._process_threat_analysis_response(
                response, asset.id, asset.analysis_id
            )
            
            return threat_scenarios
            
        except Exception as e:
            raise TaraAgentError(f"Threat analysis failed for asset {asset.name}: {str(e)}")
    
    # Helper methods for threat analysis
    def _identify_stride_threats(self, category: str, asset_name: str, 
                               asset_type: str, interfaces: List[str], 
                               context: str) -> List[Dict[str, Any]]:
        """Identify specific threats for STRIDE category."""
        threats = []
        
        # Look up relevant threat patterns
        for pattern_category, patterns in self.threat_patterns.items():
            for pattern_name, pattern in patterns.items():
                if category in pattern["stride_categories"]:
                    threat = {
                        "name": f"{pattern['description']} against {asset_name}",
                        "description": pattern["description"],
                        "attack_vector": pattern["attack_vectors"][0],  # Primary vector
                        "attack_complexity": "LOW",  # Default, would be calculated
                        "confidence": 0.8,  # Would be calculated based on asset context
                        "automotive_context": True
                    }
                    threats.append(threat)
        
        return threats
    
    def _model_network_attack_path(self, threat: Dict, target: str) -> Dict[str, Any]:
        """Model network-based attack path."""
        return {
            "threat_name": threat["name"],
            "target_asset": target,
            "attack_steps": [
                {"step": 1, "action": "Network reconnaissance", "tools": ["nmap", "wireshark"]},
                {"step": 2, "action": "Identify vulnerable service", "tools": ["nessus", "custom_scanner"]},
                {"step": 3, "action": "Exploit vulnerability", "tools": ["metasploit", "custom_exploit"]},
                {"step": 4, "action": "Establish persistence", "tools": ["backdoor", "rootkit"]}
            ],
            "prerequisites": ["Network access to vehicle", "Knowledge of target protocols"],
            "entry_points": ["Cellular modem", "WiFi interface", "Ethernet port"]
        }
    
    def _model_adjacent_attack_path(self, threat: Dict, target: str) -> Dict[str, Any]:
        """Model adjacent network attack path."""
        return {
            "threat_name": threat["name"],
            "target_asset": target,
            "attack_steps": [
                {"step": 1, "action": "Physical proximity to vehicle", "tools": ["portable_equipment"]},
                {"step": 2, "action": "Wireless network discovery", "tools": ["aircrack-ng", "bluetooth_scanner"]},
                {"step": 3, "action": "Authentication bypass", "tools": ["custom_tools"]},
                {"step": 4, "action": "System exploitation", "tools": ["exploit_framework"]}
            ],
            "prerequisites": ["Physical access to vehicle vicinity", "Specialized RF equipment"],
            "entry_points": ["WiFi access point", "Bluetooth interface", "V2X communication"]
        }
    
    def _model_local_attack_path(self, threat: Dict, target: str) -> Dict[str, Any]:
        """Model local access attack path."""
        return {
            "threat_name": threat["name"],
            "target_asset": target,
            "attack_steps": [
                {"step": 1, "action": "Physical vehicle access", "tools": ["vehicle_key", "lock_picks"]},
                {"step": 2, "action": "Connect to diagnostic port", "tools": ["OBD_scanner", "CAN_interface"]},
                {"step": 3, "action": "Network enumeration", "tools": ["CANoe", "custom_tools"]},
                {"step": 4, "action": "Message injection/modification", "tools": ["CAN_injector"]}
            ],
            "prerequisites": ["Physical vehicle access", "Diagnostic equipment"],
            "entry_points": ["OBD-II port", "Service connector", "Direct ECU access"]
        }
    
    def _model_physical_attack_path(self, threat: Dict, target: str) -> Dict[str, Any]:
        """Model physical tampering attack path."""
        return {
            "threat_name": threat["name"], 
            "target_asset": target,
            "attack_steps": [
                {"step": 1, "action": "Vehicle disassembly", "tools": ["mechanical_tools"]},
                {"step": 2, "action": "ECU extraction", "tools": ["specialized_tools"]},
                {"step": 3, "action": "Hardware analysis", "tools": ["logic_analyzer", "oscilloscope"]},
                {"step": 4, "action": "Firmware modification", "tools": ["programmer", "debugger"]}
            ],
            "prerequisites": ["Extended vehicle access", "Hardware analysis expertise"],
            "entry_points": ["ECU housing", "Wiring harness", "Component interfaces"]
        }
    
    def _add_automotive_attack_context(self, stride_category: str, 
                                     attack_vector: str, target_asset: str) -> Dict[str, Any]:
        """Add automotive-specific context to attack analysis."""
        return {
            "safety_impact": stride_category in ["TAMPERING", "DENIAL_OF_SERVICE"],
            "regulatory_implications": ["ISO_21434", "UN_ECE_WP29"],
            "industry_precedent": True,
            "detection_difficulty": "MEDIUM"
        }
    
    def _lookup_automotive_cves(self, threat_type: str, asset_category: str) -> List[str]:
        """Lookup relevant automotive CVEs."""
        # Would implement actual CVE database lookup
        return ["CVE-2023-1234", "CVE-2022-5678"]
    
    def _lookup_real_incidents(self, threat_type: str) -> List[Dict[str, Any]]:
        """Lookup real-world automotive incidents."""
        return [{"incident": "Jeep Cherokee hack", "year": "2015", "impact": "Remote control"}]
    
    def _lookup_attack_campaigns(self, asset_category: str) -> List[Dict[str, Any]]:
        """Lookup known attack campaigns."""
        return [{"campaign": "Automotive APT", "targets": ["OEMs"], "techniques": ["supply_chain"]}]
    
    def _lookup_mitigations(self, threat_type: str) -> List[str]:
        """Lookup mitigation strategies."""
        return ["Network segmentation", "Code signing", "Intrusion detection"]
    
    def _lookup_industry_alerts(self, threat_type: str, asset_category: str) -> List[Dict[str, Any]]:
        """Lookup industry security alerts."""
        return [{"alert": "NHTSA Advisory", "date": "2023-01-01", "description": "Vehicle security"}]
    
    async def _process_threat_analysis_response(self, response, asset_id: str, 
                                              analysis_id: str) -> List[ThreatScenario]:
        """Process agent response and create ThreatScenario instances."""
        threat_scenarios = []
        
        # Extract structured data from agent response
        # This would parse the actual agent output format
        threat_data = self._extract_threat_data_from_response(response)
        
        for threat_info in threat_data:
            try:
                scenario = ThreatScenario(
                    name=threat_info["name"],
                    description=threat_info["description"],
                    threat_category=ThreatCategory(threat_info["stride_category"]),
                    attack_vector=AttackVector(threat_info["attack_vector"]),
                    attack_complexity=AttackComplexity(threat_info["attack_complexity"]),
                    attack_path=threat_info.get("attack_path", []),
                    prerequisites=threat_info.get("prerequisites", []),
                    entry_points=threat_info.get("entry_points", []),
                    cve_references=threat_info.get("cve_references", []),
                    mitre_tactics=threat_info.get("mitre_tactics", []),
                    confidence_score=threat_info["confidence_score"],
                    review_status=ReviewStatus.UNDER_REVIEW if threat_info["confidence_score"] < 0.8 else ReviewStatus.IDENTIFIED,
                    detection_methods=threat_info.get("detection_methods", []),
                    asset_id=asset_id,
                    analysis_id=analysis_id,
                    iso_section="6.4.2"  # Threat scenario identification section
                )
                
                threat_scenarios.append(scenario)
                
            except Exception as e:
                print(f"Warning: Failed to create threat scenario {threat_info.get('name', 'unknown')}: {e}")
                continue
        
        return threat_scenarios
    
    def _extract_threat_data_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract structured threat data from agent response."""
        # Would parse actual agent response format
        return []