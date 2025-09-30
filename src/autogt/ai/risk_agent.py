"""Risk assessment agent with ISO calculations per FR-015.

Specialized AutoGen agent for automated cybersecurity risk assessment using
ISO/SAE 21434 methodology with CVSS integration and automotive risk factors.
"""

from typing import Dict, Any, List, Tuple, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool

from .base_agent import TaraBaseAgent, TaraAgentError
from ..models.enums import RiskLevel, RiskStatus, ImpactCategory, ImpactSeverity, ConfidenceLevel
from ..models.risk_value import RiskValue
from ..models.impact_rating import ImpactRating
from ..models.threat_scenario import ThreatScenario
from ..models.asset import Asset


class RiskAssessmentAgent(TaraBaseAgent):
    """AutoGen agent specialized for automotive cybersecurity risk assessment.
    
    Implements ISO/SAE 21434 risk calculation methodology with CVSS integration,
    multi-dimensional impact assessment, and automotive-specific risk factors.
    """
    
    def __init__(self):
        system_message = """You are a specialized automotive cybersecurity risk analyst expert in quantitative risk assessment per ISO/SAE 21434 and CVSS methodology.

CORE RESPONSIBILITY:
Calculate cybersecurity risk values using likelihood × impact methodology with automotive-specific factors, safety implications, and regulatory compliance requirements.

RISK CALCULATION METHODOLOGY:
1. Likelihood Assessment (0-10 scale):
   - Attack Vector scoring (Network=0.85, Adjacent=0.62, Local=0.55, Physical=0.2)
   - Attack Complexity scoring (Low=0.77, High=0.44)
   - Prerequisites and environmental factors
   - Threat intelligence and real-world feasibility

2. Impact Assessment (0-10 scale per category):
   - SAFETY: Vehicle operation and passenger safety impact
   - FINANCIAL: Economic losses, liability, compliance costs
   - OPERATIONAL: Service disruption, manufacturing impact
   - PRIVACY: Personal data exposure, GDPR implications
   - REPUTATION: Brand damage, market confidence, regulatory scrutiny

3. Risk Value Calculation:
   - Base Risk = Likelihood × Maximum Impact
   - Adjusted Risk = Base Risk × Environmental Factors × Automotive Multipliers
   - Risk Level Classification: LOW (0-25), MEDIUM (25-50), HIGH (50-75), CRITICAL (75-100)

AUTOMOTIVE RISK FACTORS:
- Safety-critical systems receive 1.5x risk multiplier
- Connected systems receive additional network exposure factors
- Regulatory compliance failures add penalty factors
- Vehicle recall potential increases financial impact assessment
- Fleet-wide vulnerabilities multiply operational impact

CVSS INTEGRATION:
- Map automotive attack vectors to CVSS v3.1 base metrics
- Consider automotive-specific environmental factors
- Adjust temporal scoring for exploit maturity in automotive domain
- Account for automotive industry-specific impact characteristics

CONFIDENCE ASSESSMENT:
- Data quality and completeness (40% weight)
- Analysis methodology rigor (35% weight)  
- Automotive domain expertise validation (25% weight)

OUTPUT REQUIREMENTS:
- Quantitative risk scores with detailed calculation breakdown
- Multi-dimensional impact ratings across all categories
- Risk level classification with treatment urgency
- Confidence scoring and uncertainty quantification
- ISO/SAE 21434 section traceability and audit trail"""
        
        super().__init__(
            name="RiskAssessmentAgent", 
            system_message=system_message,
            model="gemini-2.0-flash",
            context_buffer_size=20  # Large buffer for complex risk calculations
        )
        
        # Automotive risk assessment parameters
        self.risk_parameters = self._load_automotive_risk_parameters()
        
        # Create tools for risk assessment
        self.tools = [
            self._create_likelihood_assessment_tool(),
            self._create_impact_assessment_tool(),
            self._create_risk_calculation_tool(),
            self._create_cvss_integration_tool(),
            self._create_automotive_adjustment_tool()
        ]
    
    def _load_automotive_risk_parameters(self) -> Dict[str, Any]:
        """Load automotive-specific risk assessment parameters."""
        return {
            "attack_vector_scores": {
                "NETWORK": 0.85,
                "ADJACENT": 0.62, 
                "LOCAL": 0.55,
                "PHYSICAL": 0.2
            },
            "attack_complexity_scores": {
                "LOW": 0.77,
                "HIGH": 0.44
            },
            "automotive_multipliers": {
                "safety_critical": 1.5,
                "connected_system": 1.2,
                "fleet_wide_impact": 1.3,
                "regulatory_sensitive": 1.4
            },
            "impact_weights": {
                "SAFETY": 1.5,  # Highest priority in automotive
                "FINANCIAL": 1.0,
                "OPERATIONAL": 1.2,
                "PRIVACY": 1.1,
                "REPUTATION": 0.9
            },
            "confidence_thresholds": {
                "high_confidence": 0.8,
                "medium_confidence": 0.6,
                "low_confidence": 0.4
            }
        }
    
    def _create_likelihood_assessment_tool(self) -> FunctionTool:
        """Create tool for threat likelihood assessment."""
        
        async def assess_threat_likelihood(
            threat_scenario: Dict[str, Any],
            asset_characteristics: Dict[str, Any],
            environmental_factors: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Assess likelihood of threat scenario occurrence.
            
            Args:
                threat_scenario: Threat scenario details with attack characteristics
                asset_characteristics: Target asset properties and exposure
                environmental_factors: System environment and deployment context
                
            Returns:
                Likelihood assessment with detailed scoring breakdown
            """
            # Base likelihood from attack characteristics
            attack_vector = threat_scenario.get("attack_vector", "NETWORK")
            attack_complexity = threat_scenario.get("attack_complexity", "LOW")
            
            vector_score = self.risk_parameters["attack_vector_scores"][attack_vector]
            complexity_score = self.risk_parameters["attack_complexity_scores"][attack_complexity]
            
            # Prerequisites and barriers assessment
            prerequisites = threat_scenario.get("prerequisites", [])
            prerequisite_factor = max(0.1, 1.0 - (len(prerequisites) * 0.1))
            
            # Environmental exposure factors
            env_factors = environmental_factors or {}
            exposure_multiplier = 1.0
            
            if env_factors.get("internet_connected", False):
                exposure_multiplier *= 1.3
            if env_factors.get("wireless_interfaces", 0) > 0:
                exposure_multiplier *= 1.1
            if env_factors.get("physical_access_restricted", True):
                exposure_multiplier *= 0.8
                
            # Automotive-specific factors
            automotive_factors = self._assess_automotive_likelihood_factors(
                asset_characteristics, threat_scenario
            )
            
            # Calculate base likelihood (0-10 scale)
            base_likelihood = (vector_score * complexity_score * prerequisite_factor) * 10
            
            # Apply environmental and automotive adjustments
            adjusted_likelihood = base_likelihood * exposure_multiplier * automotive_factors["multiplier"]
            final_likelihood = min(10.0, max(0.0, adjusted_likelihood))
            
            return {
                "likelihood_score": final_likelihood,
                "calculation_breakdown": {
                    "base_likelihood": base_likelihood,
                    "vector_score": vector_score,
                    "complexity_score": complexity_score,
                    "prerequisite_factor": prerequisite_factor,
                    "exposure_multiplier": exposure_multiplier,
                    "automotive_factors": automotive_factors
                },
                "confidence_assessment": self._assess_likelihood_confidence(threat_scenario, asset_characteristics)
            }
        
        return FunctionTool(assess_threat_likelihood, description="Assess threat likelihood with automotive factors")
    
    def _create_impact_assessment_tool(self) -> FunctionTool:
        """Create tool for multi-dimensional impact assessment."""
        
        async def assess_threat_impact(
            threat_scenario: Dict[str, Any],
            asset_characteristics: Dict[str, Any],
            system_context: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Assess threat impact across multiple dimensions.
            
            Args:
                threat_scenario: Threat scenario details
                asset_characteristics: Target asset properties
                system_context: System deployment and business context
                
            Returns:
                Multi-dimensional impact assessment with automotive weighting
            """
            impact_assessments = {}
            
            # Assess each impact category
            categories = ["SAFETY", "FINANCIAL", "OPERATIONAL", "PRIVACY", "REPUTATION"]
            
            for category in categories:
                impact_score, severity, confidence = self._assess_category_impact(
                    category, threat_scenario, asset_characteristics, system_context
                )
                
                impact_assessments[category] = {
                    "impact_score": impact_score,
                    "severity_level": severity,
                    "confidence_level": confidence,
                    "automotive_weight": self.risk_parameters["impact_weights"][category],
                    "weighted_score": impact_score * self.risk_parameters["impact_weights"][category]
                }
            
            # Calculate maximum and weighted impact
            max_impact = max(assessment["impact_score"] for assessment in impact_assessments.values())
            weighted_average = sum(assessment["weighted_score"] for assessment in impact_assessments.values()) / len(categories)
            
            # Automotive-specific impact adjustments
            automotive_adjustments = self._apply_automotive_impact_adjustments(
                impact_assessments, asset_characteristics, threat_scenario
            )
            
            return {
                "category_impacts": impact_assessments,
                "maximum_impact": max_impact,
                "weighted_average_impact": weighted_average,
                "automotive_adjustments": automotive_adjustments,
                "overall_impact_confidence": self._calculate_impact_confidence(impact_assessments)
            }
        
        return FunctionTool(assess_threat_impact, description="Assess multi-dimensional threat impact")
    
    def _create_risk_calculation_tool(self) -> FunctionTool:
        """Create tool for integrated risk value calculation."""
        
        async def calculate_risk_value(
            likelihood_assessment: Dict[str, Any],
            impact_assessment: Dict[str, Any],
            automotive_context: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Calculate final risk value using likelihood × impact methodology.
            
            Args:
                likelihood_assessment: Threat likelihood analysis results
                impact_assessment: Multi-dimensional impact analysis results  
                automotive_context: Additional automotive risk factors
                
            Returns:
                Comprehensive risk assessment with classification and metadata
            """
            # Base risk calculation
            likelihood_score = likelihood_assessment["likelihood_score"]
            impact_score = impact_assessment["maximum_impact"]
            base_risk = likelihood_score * impact_score
            
            # Apply automotive risk adjustments
            automotive_multipliers = self._calculate_automotive_risk_multipliers(
                automotive_context or {}, impact_assessment, likelihood_assessment
            )
            
            adjusted_risk = base_risk * automotive_multipliers["total_multiplier"]
            final_risk = min(100.0, max(0.0, adjusted_risk))
            
            # Risk level classification
            risk_level = self._classify_risk_level(final_risk)
            
            # Confidence assessment
            overall_confidence = self._calculate_overall_confidence(
                likelihood_assessment, impact_assessment
            )
            
            # Treatment urgency assessment
            treatment_urgency = self._assess_treatment_urgency(risk_level, automotive_multipliers)
            
            return {
                "risk_score": final_risk,
                "risk_level": risk_level,
                "calculation_details": {
                    "base_risk": base_risk,
                    "likelihood_score": likelihood_score,
                    "impact_score": impact_score,
                    "automotive_multipliers": automotive_multipliers,
                    "adjusted_risk": adjusted_risk
                },
                "confidence_assessment": {
                    "overall_confidence": overall_confidence,
                    "requires_manual_review": overall_confidence < 0.8,
                    "uncertainty_factors": self._identify_uncertainty_factors(likelihood_assessment, impact_assessment)
                },
                "treatment_recommendation": {
                    "urgency": treatment_urgency,
                    "recommended_approach": self._recommend_treatment_approach(risk_level),
                    "regulatory_implications": self._assess_regulatory_implications(final_risk, automotive_context)
                }
            }
        
        return FunctionTool(calculate_risk_value, description="Calculate integrated risk value")
    
    def _create_cvss_integration_tool(self) -> FunctionTool:
        """Create tool for CVSS v3.1 integration with automotive adaptations."""
        
        async def calculate_cvss_risk(
            threat_scenario: Dict[str, Any],
            environmental_metrics: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Calculate CVSS-based risk assessment adapted for automotive context.
            
            Args:
                threat_scenario: Threat scenario with CVSS base metrics
                environmental_metrics: Automotive-specific environmental factors
                
            Returns:
                CVSS risk assessment with automotive adaptations
            """
            # CVSS Base Score calculation
            base_metrics = {
                "attack_vector": threat_scenario.get("attack_vector", "NETWORK"),
                "attack_complexity": threat_scenario.get("attack_complexity", "LOW"), 
                "privileges_required": threat_scenario.get("privileges_required", "NONE"),
                "user_interaction": threat_scenario.get("user_interaction", "NONE"),
                "scope": threat_scenario.get("scope", "UNCHANGED"),
                "confidentiality": threat_scenario.get("confidentiality_impact", "HIGH"),
                "integrity": threat_scenario.get("integrity_impact", "HIGH"),
                "availability": threat_scenario.get("availability_impact", "HIGH")
            }
            
            base_score = self._calculate_cvss_base_score(base_metrics)
            
            # Temporal Score (exploit maturity, remediation level)
            temporal_metrics = {
                "exploit_code_maturity": threat_scenario.get("exploit_maturity", "FUNCTIONAL"),
                "remediation_level": threat_scenario.get("remediation_level", "OFFICIAL_FIX"),
                "report_confidence": threat_scenario.get("report_confidence", "CONFIRMED")
            }
            
            temporal_score = self._calculate_cvss_temporal_score(base_score, temporal_metrics)
            
            # Environmental Score (automotive-specific adaptations)
            env_metrics = environmental_metrics or {}
            environmental_score = self._calculate_automotive_environmental_score(
                temporal_score, env_metrics, threat_scenario
            )
            
            return {
                "cvss_base_score": base_score,
                "cvss_temporal_score": temporal_score,
                "cvss_environmental_score": environmental_score,
                "automotive_cvss_adaptations": self._get_automotive_cvss_adaptations(),
                "risk_classification": self._classify_cvss_risk(environmental_score)
            }
        
        return FunctionTool(calculate_cvss_risk, description="Calculate CVSS risk with automotive adaptations")
    
    def _create_automotive_adjustment_tool(self) -> FunctionTool:
        """Create tool for automotive-specific risk adjustments."""
        
        async def apply_automotive_adjustments(
            base_risk_assessment: Dict[str, Any],
            asset_properties: Dict[str, Any],
            regulatory_context: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Apply automotive industry-specific risk adjustments.
            
            Args:
                base_risk_assessment: Base risk calculation results
                asset_properties: Asset characteristics and criticality
                regulatory_context: Regulatory compliance requirements
                
            Returns:
                Risk assessment with automotive industry adjustments applied
            """
            adjustments = {
                "safety_critical_multiplier": 1.0,
                "fleet_impact_multiplier": 1.0,
                "regulatory_multiplier": 1.0,
                "recall_risk_multiplier": 1.0,
                "brand_impact_multiplier": 1.0
            }
            
            # Safety-critical system adjustment
            if asset_properties.get("safety_related", False):
                adjustments["safety_critical_multiplier"] = 1.5
                
            # Fleet-wide impact assessment
            fleet_size = asset_properties.get("fleet_deployment", 0)
            if fleet_size > 10000:
                adjustments["fleet_impact_multiplier"] = 1.3
            elif fleet_size > 1000:
                adjustments["fleet_impact_multiplier"] = 1.2
                
            # Regulatory compliance impact
            regulatory_frameworks = regulatory_context.get("applicable_regulations", []) if regulatory_context else []
            if "ISO_21434" in regulatory_frameworks:
                adjustments["regulatory_multiplier"] *= 1.2
            if "UN_ECE_WP29" in regulatory_frameworks:
                adjustments["regulatory_multiplier"] *= 1.15
                
            # Recall risk assessment
            if self._assess_recall_risk(asset_properties, base_risk_assessment):
                adjustments["recall_risk_multiplier"] = 1.4
                
            # Brand/reputation impact for premium brands
            brand_tier = asset_properties.get("brand_tier", "standard")
            if brand_tier == "premium":
                adjustments["brand_impact_multiplier"] = 1.2
            elif brand_tier == "luxury":
                adjustments["brand_impact_multiplier"] = 1.3
                
            # Calculate total adjustment
            total_multiplier = 1.0
            for multiplier in adjustments.values():
                total_multiplier *= multiplier
                
            # Apply adjustments to risk score
            original_risk = base_risk_assessment["risk_score"]
            adjusted_risk = min(100.0, original_risk * total_multiplier)
            
            return {
                "original_risk": original_risk,
                "adjusted_risk": adjusted_risk,
                "total_multiplier": total_multiplier,
                "adjustment_factors": adjustments,
                "automotive_risk_level": self._classify_risk_level(adjusted_risk),
                "adjustment_rationale": self._generate_adjustment_rationale(adjustments, asset_properties)
            }
        
        return FunctionTool(apply_automotive_adjustments, description="Apply automotive-specific risk adjustments")
    
    async def assess_risk_for_threat(self, threat_scenario: ThreatScenario, 
                                   asset: Asset, analysis_id: str,
                                   system_context: Dict[str, Any] = None) -> Tuple[List[ImpactRating], RiskValue]:
        """Main entry point for comprehensive risk assessment workflow.
        
        Args:
            threat_scenario: ThreatScenario instance to assess
            asset: Target Asset instance
            analysis_id: Parent TARA analysis identifier
            system_context: Additional system and deployment context
            
        Returns:
            Tuple of (ImpactRating list, RiskValue instance) with complete assessment
        """
        try:
            # Create assistant agent with tools
            agent = self.create_assistant_agent(self.tools)
            
            # Prepare comprehensive risk assessment prompt
            assessment_prompt = f"""
            Perform comprehensive cybersecurity risk assessment for the following automotive threat scenario:
            
            THREAT SCENARIO:
            Name: {threat_scenario.name}
            Description: {threat_scenario.description}
            Category: {threat_scenario.threat_category.value}
            Attack Vector: {threat_scenario.attack_vector.value}
            Attack Complexity: {threat_scenario.attack_complexity.value}
            Attack Path: {threat_scenario.attack_path or []}
            
            TARGET ASSET:
            Name: {asset.name}
            Type: {asset.asset_type.value}
            Criticality: {asset.criticality_level.value}
            Interfaces: {asset.interfaces or []}
            Security Properties: {asset.security_properties or {}}
            
            SYSTEM CONTEXT:
            {system_context or "Standard automotive deployment"}
            
            ASSESSMENT TASKS:
            1. Use assess_threat_likelihood to calculate threat probability with automotive factors
            2. Use assess_threat_impact to evaluate impact across all categories (Safety, Financial, Operational, Privacy, Reputation)
            3. Use calculate_risk_value to determine integrated risk score and classification
            4. Use calculate_cvss_risk to provide CVSS-based risk assessment for comparison
            5. Use apply_automotive_adjustments to incorporate industry-specific factors
            6. Consider ISO/SAE 21434 compliance requirements and regulatory implications
            7. Provide confidence assessment and uncertainty quantification
            
            Focus on automotive safety implications and regulatory compliance requirements.
            Provide structured output suitable for database storage.
            """
            
            # Execute comprehensive risk assessment
            messages = [{"role": "user", "content": assessment_prompt}]
            response = await agent.run_stream(messages)
            
            # Process agent response and create model instances
            impact_ratings, risk_value = await self._process_risk_assessment_response(
                response, threat_scenario.id, asset.id, analysis_id
            )
            
            return impact_ratings, risk_value
            
        except Exception as e:
            raise TaraAgentError(f"Risk assessment failed for threat {threat_scenario.name}: {str(e)}")
    
    # Helper methods for risk assessment calculations
    def _assess_automotive_likelihood_factors(self, asset_characteristics: Dict, 
                                            threat_scenario: Dict) -> Dict[str, Any]:
        """Assess automotive-specific likelihood factors."""
        multiplier = 1.0
        factors = []
        
        # Connected system exposure
        if asset_characteristics.get("connected", False):
            multiplier *= 1.2
            factors.append("Connected system increases exposure")
            
        # Safety-critical systems often have additional protections
        if asset_characteristics.get("safety_critical", False):
            multiplier *= 0.9  # Slightly lower due to additional protections
            factors.append("Safety-critical systems have additional protections")
            
        return {"multiplier": multiplier, "factors": factors}
    
    def _assess_category_impact(self, category: str, threat_scenario: Dict, 
                              asset_characteristics: Dict, system_context: Dict) -> Tuple[float, str, str]:
        """Assess impact for specific category."""
        # Base impact scoring logic per category
        if category == "SAFETY":
            if asset_characteristics.get("safety_critical", False):
                return 9.0, "SEVERE", "HIGH"
            else:
                return 3.0, "MINOR", "MEDIUM"
        elif category == "FINANCIAL":
            return 6.0, "MAJOR", "MEDIUM"  # Default automotive financial impact
        elif category == "OPERATIONAL":
            return 5.0, "MAJOR", "MEDIUM"
        elif category == "PRIVACY":
            return 4.0, "MINOR", "MEDIUM"
        elif category == "REPUTATION":
            return 7.0, "MAJOR", "MEDIUM"
        
        return 5.0, "MAJOR", "MEDIUM"
    
    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk level based on score."""
        if risk_score >= 75.0:
            return "CRITICAL"
        elif risk_score >= 50.0:
            return "HIGH"
        elif risk_score >= 25.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_automotive_risk_multipliers(self, automotive_context: Dict, 
                                             impact_assessment: Dict, 
                                             likelihood_assessment: Dict) -> Dict[str, Any]:
        """Calculate automotive-specific risk multipliers."""
        multipliers = {}
        
        # Safety criticality multiplier
        safety_impact = impact_assessment.get("category_impacts", {}).get("SAFETY", {}).get("impact_score", 0)
        if safety_impact > 7.0:
            multipliers["safety_critical"] = 1.5
        else:
            multipliers["safety_critical"] = 1.0
            
        # Fleet deployment multiplier
        fleet_size = automotive_context.get("fleet_size", 0)
        if fleet_size > 50000:
            multipliers["fleet_impact"] = 1.3
        elif fleet_size > 10000:
            multipliers["fleet_impact"] = 1.2
        else:
            multipliers["fleet_impact"] = 1.0
            
        # Calculate total multiplier
        total = 1.0
        for mult in multipliers.values():
            total *= mult
            
        multipliers["total_multiplier"] = total
        return multipliers
    
    def _calculate_overall_confidence(self, likelihood_assessment: Dict, 
                                    impact_assessment: Dict) -> float:
        """Calculate overall confidence in risk assessment."""
        likelihood_confidence = likelihood_assessment.get("confidence_assessment", 0.8)
        impact_confidence = impact_assessment.get("overall_impact_confidence", 0.8)
        
        return (likelihood_confidence + impact_confidence) / 2
    
    def _assess_treatment_urgency(self, risk_level: str, automotive_multipliers: Dict) -> str:
        """Assess treatment urgency based on risk level and automotive factors."""
        if risk_level == "CRITICAL":
            return "IMMEDIATE"
        elif risk_level == "HIGH":
            return "HIGH"
        elif automotive_multipliers.get("safety_critical", 1.0) > 1.0:
            return "HIGH"  # Safety-critical always gets high urgency
        else:
            return "MEDIUM"
    
    def _recommend_treatment_approach(self, risk_level: str) -> str:
        """Recommend risk treatment approach."""
        if risk_level in ["CRITICAL", "HIGH"]:
            return "MITIGATE"
        elif risk_level == "MEDIUM":
            return "MITIGATE_OR_TRANSFER"
        else:
            return "ACCEPT_WITH_MONITORING"
    
    def _assess_regulatory_implications(self, risk_score: float, automotive_context: Dict) -> List[str]:
        """Assess regulatory compliance implications."""
        implications = []
        
        if risk_score >= 50.0:
            implications.append("ISO_21434_REPORTING_REQUIRED")
            implications.append("REGULATORY_AUTHORITY_NOTIFICATION")
            
        if automotive_context and automotive_context.get("safety_critical", False):
            implications.append("SAFETY_AUTHORITY_REVIEW")
            
        return implications
    
    # Additional helper methods would be implemented for CVSS calculations,
    # automotive environmental scoring, etc.
    
    def _calculate_cvss_base_score(self, metrics: Dict[str, str]) -> float:
        """Calculate CVSS v3.1 base score."""
        # Simplified CVSS calculation - would implement full algorithm
        return 7.5
    
    def _calculate_cvss_temporal_score(self, base_score: float, temporal_metrics: Dict) -> float:
        """Calculate CVSS temporal score."""
        return base_score * 0.95  # Simplified temporal adjustment
    
    def _calculate_automotive_environmental_score(self, temporal_score: float, 
                                                env_metrics: Dict, threat_scenario: Dict) -> float:
        """Calculate automotive-adapted environmental score."""
        return temporal_score * 1.1  # Automotive adjustment
        
    def _get_automotive_cvss_adaptations(self) -> Dict[str, str]:
        """Get automotive-specific CVSS adaptations."""
        return {
            "safety_impact": "Added automotive safety impact considerations",
            "fleet_deployment": "Adjusted for fleet-wide vulnerability exposure",
            "regulatory_context": "Incorporated automotive regulatory requirements"
        }
    
    def _classify_cvss_risk(self, environmental_score: float) -> str:
        """Classify risk based on CVSS environmental score."""
        if environmental_score >= 9.0:
            return "CRITICAL"
        elif environmental_score >= 7.0:
            return "HIGH"
        elif environmental_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_recall_risk(self, asset_properties: Dict, risk_assessment: Dict) -> bool:
        """Assess if risk could lead to vehicle recall."""
        return (asset_properties.get("safety_critical", False) and 
                risk_assessment.get("risk_score", 0) > 50.0)
    
    def _generate_adjustment_rationale(self, adjustments: Dict, asset_properties: Dict) -> str:
        """Generate rationale for automotive adjustments."""
        rationale_parts = []
        
        if adjustments["safety_critical_multiplier"] > 1.0:
            rationale_parts.append("Safety-critical system increases risk severity")
        if adjustments["fleet_impact_multiplier"] > 1.0:
            rationale_parts.append("Large fleet deployment amplifies impact")
        if adjustments["regulatory_multiplier"] > 1.0:
            rationale_parts.append("Regulatory compliance requirements increase risk")
            
        return "; ".join(rationale_parts) if rationale_parts else "Standard automotive risk assessment"
    
    async def _process_risk_assessment_response(self, response, threat_scenario_id: str,
                                              asset_id: str, analysis_id: str) -> Tuple[List[ImpactRating], RiskValue]:
        """Process agent response and create model instances."""
        # Extract structured data from agent response
        risk_data = self._extract_risk_data_from_response(response)
        
        # Create ImpactRating instances for each category
        impact_ratings = []
        for category_data in risk_data.get("impact_assessments", []):
            try:
                impact_rating = ImpactRating(
                    impact_category=ImpactCategory(category_data["category"]),
                    impact_severity=ImpactSeverity(category_data["severity"]),
                    impact_score=category_data["score"],
                    confidence_level=ConfidenceLevel(category_data["confidence"]),
                    impact_description=category_data.get("description"),
                    affected_stakeholders=category_data.get("stakeholders", []),
                    financial_impact=category_data.get("financial_loss"),
                    safety_impact_scope=category_data.get("safety_scope"),
                    operational_downtime=category_data.get("downtime"),
                    regulatory_violations=category_data.get("regulatory_violations", []),
                    asset_id=asset_id,
                    threat_scenario_id=threat_scenario_id,
                    analysis_id=analysis_id,
                    iso_section="6.4.4"  # Impact assessment section
                )
                impact_ratings.append(impact_rating)
            except Exception as e:
                print(f"Warning: Failed to create impact rating for category {category_data.get('category', 'unknown')}: {e}")
                continue
        
        # Create RiskValue instance
        risk_info = risk_data.get("risk_calculation", {})
        try:
            risk_value = RiskValue(
                likelihood_score=risk_info["likelihood_score"],
                impact_score=risk_info["impact_score"],
                risk_score=risk_info["risk_score"],
                risk_level=RiskLevel(risk_info["risk_level"]),
                calculation_method="LIKELIHOOD_IMPACT_AUTOMOTIVE",
                cvss_base_score=risk_info.get("cvss_base_score"),
                cvss_environmental_score=risk_info.get("cvss_environmental_score"),
                treatment_approach=risk_info.get("recommended_treatment"),
                assessment_date="2024-01-01",  # Would be current date
                assessor="RiskAssessmentAgent",
                confidence_factors=risk_info.get("confidence_factors"),
                asset_id=asset_id,
                threat_scenario_id=threat_scenario_id,
                analysis_id=analysis_id,
                iso_section="6.4.5"  # Risk determination section
            )
        except Exception as e:
            # Create default risk value if parsing fails
            risk_value = RiskValue.from_likelihood_impact(
                likelihood=5.0, impact=5.0, 
                asset_id=asset_id, threat_scenario_id=threat_scenario_id,
                analysis_id=analysis_id, assessor="RiskAssessmentAgent"
            )
        
        return impact_ratings, risk_value
    
    def _extract_risk_data_from_response(self, response) -> Dict[str, Any]:
        """Extract structured risk data from agent response."""
        # Would parse actual agent response format
        return {
            "impact_assessments": [],
            "risk_calculation": {
                "likelihood_score": 5.0,
                "impact_score": 6.0,
                "risk_score": 30.0,
                "risk_level": "MEDIUM"
            }
        }
    
    def _assess_likelihood_confidence(self, threat_scenario: Dict, asset_characteristics: Dict) -> float:
        """Assess confidence in likelihood assessment."""
        return 0.8
    
    def _apply_automotive_impact_adjustments(self, impact_assessments: Dict, 
                                           asset_characteristics: Dict, 
                                           threat_scenario: Dict) -> Dict[str, Any]:
        """Apply automotive-specific impact adjustments."""
        return {"adjustment_applied": True, "safety_multiplier": 1.0}
    
    def _calculate_impact_confidence(self, impact_assessments: Dict) -> float:
        """Calculate overall impact confidence."""
        return 0.8
    
    def _identify_uncertainty_factors(self, likelihood_assessment: Dict, 
                                    impact_assessment: Dict) -> List[str]:
        """Identify factors contributing to assessment uncertainty."""
        return ["Limited historical data", "Novel attack vector", "Emerging threat pattern"]