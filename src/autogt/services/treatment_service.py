"""Treatment planning service for cybersecurity risk mitigation per FR-016.

Provides comprehensive treatment planning capabilities including countermeasure
identification, implementation planning, cost-benefit analysis, and treatment validation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.treatment import TreatmentPlan, TreatmentStatus
from ..models.risk import RiskAssessment, RiskLevel
from ..models.threat import ThreatScenario
from ..models.asset import Asset
from ..ai.orchestrator import TaraOrchestrator
from ..core.exceptions import ValidationError, AnalysisError


logger = logging.getLogger(__name__)


class TreatmentStrategy(Enum):
    """Treatment strategies for risk mitigation."""
    AVOID = "AVOID"      # Eliminate the risk source
    MITIGATE = "MITIGATE"  # Reduce likelihood or impact
    TRANSFER = "TRANSFER"   # Share or transfer the risk
    ACCEPT = "ACCEPT"      # Accept residual risk


class CountermeasureType(Enum):
    """Types of cybersecurity countermeasures."""
    TECHNICAL = "TECHNICAL"           # Technical controls
    PROCEDURAL = "PROCEDURAL"        # Process/procedure controls
    ORGANIZATIONAL = "ORGANIZATIONAL" # Policy/governance controls
    PHYSICAL = "PHYSICAL"            # Physical security controls


@dataclass
class CountermeasureRecommendation:
    """Cybersecurity countermeasure recommendation."""
    name: str
    description: str
    type: str
    effectiveness: float
    implementation_cost: str
    maintenance_effort: str
    standards_compliance: List[str]
    implementation_timeline: str


@dataclass
class TreatmentPlanResult:
    """Result of treatment planning operation."""
    plan_id: str
    risk_id: str
    strategy: str
    countermeasures: List[CountermeasureRecommendation]
    expected_effectiveness: float
    cost_estimate: Dict[str, Any]
    implementation_timeline: str
    validation_criteria: List[str]


@dataclass
class TreatmentAnalysis:
    """Result of comprehensive treatment analysis."""
    total_plans: int
    strategy_distribution: Dict[str, int]
    cost_summary: Dict[str, Any]
    implementation_roadmap: List[Dict[str, Any]]
    effectiveness_metrics: Dict[str, float]


class TreatmentPlanningService:
    """Service for cybersecurity risk treatment planning."""
    
    def __init__(self, db_session: Session):
        """Initialize treatment planning service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.ai_orchestrator = TaraOrchestrator()
        
        # Cybersecurity countermeasure library
        self.countermeasure_library = {
            'SPOOFING': [
                {
                    'name': 'Multi-factor Authentication',
                    'description': 'Implement strong authentication mechanisms',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.85,
                    'cost': 'MEDIUM',
                    'standards': ['ISO 27001', 'NIST CSF'],
                    'timeline': '3-6 months'
                },
                {
                    'name': 'Digital Certificates',
                    'description': 'Use PKI-based identity verification',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.90,
                    'cost': 'HIGH',
                    'standards': ['ISO/SAE 21434', 'AUTOSAR'],
                    'timeline': '6-12 months'
                }
            ],
            'TAMPERING': [
                {
                    'name': 'Code Signing',
                    'description': 'Cryptographic signatures for software integrity',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.88,
                    'cost': 'MEDIUM',
                    'standards': ['ISO/SAE 21434', 'UNECE WP.29'],
                    'timeline': '2-4 months'
                },
                {
                    'name': 'Hardware Security Module',
                    'description': 'Tamper-resistant hardware for key storage',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.95,
                    'cost': 'HIGH',
                    'standards': ['FIPS 140-2', 'Common Criteria'],
                    'timeline': '6-18 months'
                }
            ],
            'INFORMATION_DISCLOSURE': [
                {
                    'name': 'End-to-End Encryption',
                    'description': 'Encrypt sensitive data in transit and at rest',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.92,
                    'cost': 'MEDIUM',
                    'standards': ['AES-256', 'TLS 1.3'],
                    'timeline': '2-6 months'
                },
                {
                    'name': 'Access Control Lists',
                    'description': 'Granular permission management',
                    'type': CountermeasureType.PROCEDURAL,
                    'effectiveness': 0.75,
                    'cost': 'LOW',
                    'standards': ['ISO 27001', 'NIST 800-53'],
                    'timeline': '1-3 months'
                }
            ],
            'DENIAL_OF_SERVICE': [
                {
                    'name': 'Rate Limiting',
                    'description': 'Limit request frequency to prevent overload',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.70,
                    'cost': 'LOW',
                    'standards': ['OWASP', 'NIST CSF'],
                    'timeline': '1-2 months'
                },
                {
                    'name': 'System Redundancy',
                    'description': 'Redundant systems for fault tolerance',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.85,
                    'cost': 'HIGH',
                    'standards': ['ISO 26262', 'IEC 61508'],
                    'timeline': '12-24 months'
                }
            ],
            'ELEVATION_OF_PRIVILEGE': [
                {
                    'name': 'Principle of Least Privilege',
                    'description': 'Minimize user and process privileges',
                    'type': CountermeasureType.PROCEDURAL,
                    'effectiveness': 0.80,
                    'cost': 'LOW',
                    'standards': ['ISO 27001', 'NIST 800-53'],
                    'timeline': '2-4 months'
                },
                {
                    'name': 'Sandboxing',
                    'description': 'Isolate processes in restricted environments',
                    'type': CountermeasureType.TECHNICAL,
                    'effectiveness': 0.85,
                    'cost': 'MEDIUM',
                    'standards': ['AUTOSAR', 'POSIX'],
                    'timeline': '4-8 months'
                }
            ]
        }
        
        # Treatment strategy selection criteria
        self.strategy_criteria = {
            TreatmentStrategy.AVOID: {
                'risk_levels': ['VERY_HIGH'],
                'conditions': ['critical_asset', 'safety_impact'],
                'cost_tolerance': 'HIGH'
            },
            TreatmentStrategy.MITIGATE: {
                'risk_levels': ['HIGH', 'VERY_HIGH', 'MEDIUM'],
                'conditions': ['technical_feasible', 'cost_effective'],
                'cost_tolerance': 'MEDIUM'
            },
            TreatmentStrategy.TRANSFER: {
                'risk_levels': ['MEDIUM', 'HIGH'],
                'conditions': ['external_dependency', 'insurance_available'],
                'cost_tolerance': 'LOW'
            },
            TreatmentStrategy.ACCEPT: {
                'risk_levels': ['LOW', 'VERY_LOW'],
                'conditions': ['low_impact', 'mitigation_not_feasible'],
                'cost_tolerance': 'VERY_LOW'
            }
        }
        
        # Cost estimation factors
        self.cost_factors = {
            'development': {'LOW': 10000, 'MEDIUM': 50000, 'HIGH': 200000},
            'implementation': {'LOW': 5000, 'MEDIUM': 25000, 'HIGH': 100000},
            'maintenance_annual': {'LOW': 2000, 'MEDIUM': 10000, 'HIGH': 50000},
            'training': {'LOW': 1000, 'MEDIUM': 5000, 'HIGH': 20000}
        }
    
    async def create_treatment_plans(self, analysis_id: str) -> TreatmentAnalysis:
        """Create comprehensive treatment plans for all risks in analysis.
        
        Args:
            analysis_id: ID of analysis to create treatment plans for
            
        Returns:
            Comprehensive treatment analysis results
        """
        try:
            logger.info(f"Creating treatment plans for analysis {analysis_id}")
            
            # Get high and medium priority risks
            risks = self.db_session.query(RiskAssessment).filter(
                and_(
                    RiskAssessment.analysis_id == analysis_id,
                    RiskAssessment.risk_level.in_(['MEDIUM', 'HIGH', 'VERY_HIGH'])
                )
            ).all()
            
            if not risks:
                logger.warning(f"No medium/high risks found for treatment planning in {analysis_id}")
                return TreatmentAnalysis(
                    total_plans=0,
                    strategy_distribution={},
                    cost_summary={'total_cost': 0},
                    implementation_roadmap=[],
                    effectiveness_metrics={}
                )
            
            # Create treatment plan for each risk
            treatment_plans = []
            strategy_distribution = {}
            total_cost = 0
            
            for risk in risks:
                try:
                    plan_result = await self._create_single_treatment_plan(risk)
                    treatment_plans.append(plan_result)
                    
                    # Track strategy distribution
                    strategy = plan_result.strategy
                    strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
                    
                    # Accumulate costs
                    if plan_result.cost_estimate:
                        total_cost += plan_result.cost_estimate.get('total_cost', 0)
                    
                    # Create database record
                    treatment_plan = TreatmentPlan(
                        analysis_id=analysis_id,
                        risk_assessment_id=risk.id,
                        treatment_strategy=plan_result.strategy,
                        description=f"Treatment plan for {risk.id}",
                        implementation_timeline=plan_result.implementation_timeline,
                        status=TreatmentStatus.PLANNED,
                        created_at=datetime.now(),
                        metadata={
                            'countermeasures': [cm.__dict__ for cm in plan_result.countermeasures],
                            'expected_effectiveness': plan_result.expected_effectiveness,
                            'cost_estimate': plan_result.cost_estimate,
                            'validation_criteria': plan_result.validation_criteria
                        }
                    )
                    
                    self.db_session.add(treatment_plan)
                    
                except Exception as e:
                    logger.warning(f"Failed to create treatment plan for risk {risk.id}: {str(e)}")
                    continue
            
            self.db_session.commit()
            
            # Generate implementation roadmap
            roadmap = self._generate_implementation_roadmap(treatment_plans)
            
            # Calculate effectiveness metrics
            effectiveness_metrics = self._calculate_effectiveness_metrics(treatment_plans)
            
            # Generate cost summary
            cost_summary = self._generate_cost_summary(treatment_plans, total_cost)
            
            return TreatmentAnalysis(
                total_plans=len(treatment_plans),
                strategy_distribution=strategy_distribution,
                cost_summary=cost_summary,
                implementation_roadmap=roadmap,
                effectiveness_metrics=effectiveness_metrics
            )
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create treatment plans for analysis {analysis_id}: {str(e)}")
            raise AnalysisError(f"Treatment planning failed: {str(e)}")
    
    async def update_treatment_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing treatment plan.
        
        Args:
            plan_id: ID of treatment plan to update
            updates: Dictionary of updates to apply
            
        Returns:
            Success status
        """
        plan = self.db_session.query(TreatmentPlan).filter_by(id=plan_id).first()
        if not plan:
            raise ValidationError(f"Treatment plan not found: {plan_id}")
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(plan, field):
                setattr(plan, field, value)
        
        plan.updated_at = datetime.now()
        self.db_session.commit()
        
        return True
    
    def validate_treatment_effectiveness(self, analysis_id: str) -> Dict[str, Any]:
        """Validate effectiveness of implemented treatment plans.
        
        Args:
            analysis_id: ID of analysis to validate
            
        Returns:
            Validation results and metrics
        """
        plans = self.db_session.query(TreatmentPlan).filter_by(analysis_id=analysis_id).all()
        
        validation_results = {
            'total_plans': len(plans),
            'implemented_plans': 0,
            'effectiveness_score': 0.0,
            'validation_details': []
        }
        
        if not plans:
            return validation_results
        
        total_effectiveness = 0
        implemented_count = 0
        
        for plan in plans:
            if plan.status == TreatmentStatus.IMPLEMENTED:
                implemented_count += 1
                
                # Get expected effectiveness from metadata
                expected_effectiveness = 0.0
                if plan.metadata and 'expected_effectiveness' in plan.metadata:
                    expected_effectiveness = plan.metadata['expected_effectiveness']
                    total_effectiveness += expected_effectiveness
                
                validation_results['validation_details'].append({
                    'plan_id': plan.id,
                    'strategy': plan.treatment_strategy,
                    'expected_effectiveness': expected_effectiveness,
                    'status': plan.status.value
                })
        
        validation_results['implemented_plans'] = implemented_count
        
        if implemented_count > 0:
            validation_results['effectiveness_score'] = total_effectiveness / implemented_count
        
        return validation_results
    
    def get_treatment_roadmap(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get implementation roadmap for treatment plans.
        
        Args:
            analysis_id: ID of analysis
            
        Returns:
            Ordered list of treatment implementation milestones
        """
        plans = self.db_session.query(TreatmentPlan).filter_by(analysis_id=analysis_id).all()
        
        roadmap_items = []
        for plan in plans:
            # Extract timeline from metadata
            timeline = "3-6 months"  # Default
            if plan.implementation_timeline:
                timeline = plan.implementation_timeline
            
            roadmap_items.append({
                'plan_id': plan.id,
                'strategy': plan.treatment_strategy,
                'timeline': timeline,
                'priority': self._get_plan_priority(plan),
                'cost_estimate': plan.metadata.get('cost_estimate', {}).get('total_cost', 0) if plan.metadata else 0,
                'status': plan.status.value
            })
        
        # Sort by priority and timeline
        roadmap_items.sort(key=lambda x: (x['priority'], x['timeline']))
        
        return roadmap_items
    
    async def _create_single_treatment_plan(self, risk: RiskAssessment) -> TreatmentPlanResult:
        """Create treatment plan for a single risk assessment."""
        # Get associated threat scenario
        threat = self.db_session.query(ThreatScenario).filter_by(id=risk.threat_scenario_id).first()
        if not threat:
            raise AnalysisError(f"Threat not found for risk {risk.id}")
        
        # Determine treatment strategy
        strategy = self._select_treatment_strategy(risk, threat)
        
        # Get countermeasure recommendations
        countermeasures = self._recommend_countermeasures(threat, strategy)
        
        # Get AI enhancement for countermeasures
        ai_enhanced = await self._enhance_countermeasures_with_ai(
            threat, countermeasures, strategy
        )
        
        # Calculate expected effectiveness
        effectiveness = self._calculate_treatment_effectiveness(countermeasures)
        
        # Estimate costs
        cost_estimate = self._estimate_treatment_costs(countermeasures, strategy)
        
        # Determine implementation timeline
        timeline = self._calculate_implementation_timeline(countermeasures, strategy)
        
        # Generate validation criteria
        validation_criteria = self._generate_validation_criteria(threat, countermeasures, strategy)
        
        return TreatmentPlanResult(
            plan_id=f"plan_{risk.id}",
            risk_id=risk.id,
            strategy=strategy.value,
            countermeasures=countermeasures,
            expected_effectiveness=effectiveness,
            cost_estimate=cost_estimate,
            implementation_timeline=timeline,
            validation_criteria=validation_criteria
        )
    
    def _select_treatment_strategy(self, risk: RiskAssessment, 
                                 threat: ThreatScenario) -> TreatmentStrategy:
        """Select appropriate treatment strategy based on risk characteristics."""
        risk_level = risk.risk_level or 'MEDIUM'
        
        # High/very high risks typically require mitigation or avoidance
        if risk_level in ['VERY_HIGH']:
            # Check if avoidance is possible (e.g., remove functionality)
            if threat.category in ['EXPERIMENTAL', 'OPTIONAL']:
                return TreatmentStrategy.AVOID
            else:
                return TreatmentStrategy.MITIGATE
        
        elif risk_level == 'HIGH':
            return TreatmentStrategy.MITIGATE
        
        elif risk_level == 'MEDIUM':
            # Medium risks can be mitigated or transferred
            if threat.stride_category in ['INFORMATION_DISCLOSURE', 'REPUDIATION']:
                return TreatmentStrategy.TRANSFER  # Insurance/liability
            else:
                return TreatmentStrategy.MITIGATE
        
        else:  # LOW, VERY_LOW
            return TreatmentStrategy.ACCEPT
    
    def _recommend_countermeasures(self, threat: ThreatScenario, 
                                 strategy: TreatmentStrategy) -> List[CountermeasureRecommendation]:
        """Recommend countermeasures based on threat and strategy."""
        countermeasures = []
        
        if strategy == TreatmentStrategy.ACCEPT:
            # No countermeasures for accepted risks
            return countermeasures
        
        # Get countermeasures from library based on STRIDE category
        stride_category = threat.stride_category or 'TAMPERING'
        available_countermeasures = self.countermeasure_library.get(stride_category, [])
        
        # Select appropriate countermeasures based on strategy
        for cm_data in available_countermeasures:
            if strategy == TreatmentStrategy.AVOID:
                # For avoidance, recommend high-effectiveness measures
                if cm_data['effectiveness'] >= 0.85:
                    countermeasures.append(self._create_countermeasure_recommendation(cm_data))
            
            elif strategy == TreatmentStrategy.MITIGATE:
                # For mitigation, recommend based on cost-effectiveness
                if cm_data['effectiveness'] >= 0.70:
                    countermeasures.append(self._create_countermeasure_recommendation(cm_data))
            
            elif strategy == TreatmentStrategy.TRANSFER:
                # For transfer, recommend organizational measures
                if cm_data['type'] in [CountermeasureType.PROCEDURAL, CountermeasureType.ORGANIZATIONAL]:
                    countermeasures.append(self._create_countermeasure_recommendation(cm_data))
        
        # Limit to top 3 countermeasures
        return countermeasures[:3]
    
    def _create_countermeasure_recommendation(self, cm_data: Dict[str, Any]) -> CountermeasureRecommendation:
        """Create countermeasure recommendation from library data."""
        return CountermeasureRecommendation(
            name=cm_data['name'],
            description=cm_data['description'],
            type=cm_data['type'].value,
            effectiveness=cm_data['effectiveness'],
            implementation_cost=cm_data['cost'],
            maintenance_effort=cm_data['cost'],  # Simplified
            standards_compliance=cm_data['standards'],
            implementation_timeline=cm_data['timeline']
        )
    
    async def _enhance_countermeasures_with_ai(self, threat: ThreatScenario,
                                             countermeasures: List[CountermeasureRecommendation],
                                             strategy: TreatmentStrategy) -> List[CountermeasureRecommendation]:
        """Enhance countermeasures using AI recommendations."""
        try:
            threat_data = {
                'name': threat.name,
                'category': threat.category,
                'stride_category': threat.stride_category,
                'description': threat.description
            }
            
            ai_recommendations = await self.ai_orchestrator.recommend_countermeasures(
                threat_data, strategy.value
            )
            
            # Merge AI recommendations with existing countermeasures
            # Implementation would enhance existing recommendations or add new ones
            return countermeasures
            
        except Exception as e:
            logger.warning(f"AI countermeasure enhancement failed: {str(e)}")
            return countermeasures
    
    def _calculate_treatment_effectiveness(self, countermeasures: List[CountermeasureRecommendation]) -> float:
        """Calculate overall treatment effectiveness."""
        if not countermeasures:
            return 0.0
        
        # Combined effectiveness using probability formula: 1 - (1-p1)(1-p2)...(1-pn)
        combined_failure_probability = 1.0
        for cm in countermeasures:
            failure_probability = 1.0 - cm.effectiveness
            combined_failure_probability *= failure_probability
        
        combined_effectiveness = 1.0 - combined_failure_probability
        return min(0.95, combined_effectiveness)  # Cap at 95%
    
    def _estimate_treatment_costs(self, countermeasures: List[CountermeasureRecommendation],
                                strategy: TreatmentStrategy) -> Dict[str, Any]:
        """Estimate implementation costs for treatment plan."""
        total_cost = 0
        cost_breakdown = {
            'development': 0,
            'implementation': 0,
            'maintenance_annual': 0,
            'training': 0
        }
        
        for cm in countermeasures:
            cost_level = cm.implementation_cost
            
            # Add costs from each category
            for category in cost_breakdown.keys():
                category_cost = self.cost_factors[category].get(cost_level, 0)
                cost_breakdown[category] += category_cost
                total_cost += category_cost
        
        # Strategy-based multipliers
        strategy_multipliers = {
            TreatmentStrategy.AVOID: 1.5,    # Higher cost for complete avoidance
            TreatmentStrategy.MITIGATE: 1.0, # Base cost
            TreatmentStrategy.TRANSFER: 0.3, # Lower technical cost, higher insurance
            TreatmentStrategy.ACCEPT: 0.1    # Minimal monitoring cost
        }
        
        multiplier = strategy_multipliers.get(strategy, 1.0)
        total_cost *= multiplier
        
        return {
            'total_cost': int(total_cost),
            'breakdown': cost_breakdown,
            'strategy_multiplier': multiplier,
            'currency': 'USD'
        }
    
    def _calculate_implementation_timeline(self, countermeasures: List[CountermeasureRecommendation],
                                        strategy: TreatmentStrategy) -> str:
        """Calculate implementation timeline for treatment plan."""
        if not countermeasures:
            return "Immediate"
        
        # Parse timeline ranges and find maximum
        max_months = 0
        for cm in countermeasures:
            timeline = cm.implementation_timeline
            
            # Extract maximum months from timeline string (e.g., "3-6 months" -> 6)
            import re
            months = re.findall(r'(\d+)', timeline)
            if months:
                cm_max = max(int(m) for m in months)
                max_months = max(max_months, cm_max)
        
        # Strategy adjustments
        if strategy == TreatmentStrategy.AVOID:
            max_months = int(max_months * 1.2)  # 20% longer for complete solutions
        elif strategy == TreatmentStrategy.ACCEPT:
            max_months = 1  # Minimal setup time
        
        # Format timeline
        if max_months <= 1:
            return "1 month"
        elif max_months <= 6:
            return f"{max_months} months"
        elif max_months <= 12:
            return f"{max_months} months"
        else:
            years = max_months / 12
            return f"{years:.1f} years"
    
    def _generate_validation_criteria(self, threat: ThreatScenario,
                                    countermeasures: List[CountermeasureRecommendation],
                                    strategy: TreatmentStrategy) -> List[str]:
        """Generate validation criteria for treatment effectiveness."""
        criteria = []
        
        # Strategy-specific criteria
        if strategy == TreatmentStrategy.AVOID:
            criteria.append("Verify threat vector is completely eliminated")
            criteria.append("Confirm functionality removal does not impact safety")
        
        elif strategy == TreatmentStrategy.MITIGATE:
            criteria.append("Measure residual risk reduction")
            criteria.append("Validate countermeasure effectiveness through testing")
        
        elif strategy == TreatmentStrategy.TRANSFER:
            criteria.append("Confirm liability transfer agreements are in place")
            criteria.append("Verify insurance coverage adequacy")
        
        elif strategy == TreatmentStrategy.ACCEPT:
            criteria.append("Document risk acceptance rationale")
            criteria.append("Establish monitoring for risk level changes")
        
        # Countermeasure-specific criteria
        for cm in countermeasures:
            if 'Authentication' in cm.name:
                criteria.append("Test authentication bypass attempts")
            elif 'Encryption' in cm.name:
                criteria.append("Verify encryption strength and key management")
            elif 'Access Control' in cm.name:
                criteria.append("Validate permission enforcement")
        
        # STRIDE-specific validation
        stride_validations = {
            'SPOOFING': "Test identity verification mechanisms",
            'TAMPERING': "Verify integrity protection effectiveness",
            'REPUDIATION': "Validate audit trail completeness",
            'INFORMATION_DISCLOSURE': "Test data protection measures",
            'DENIAL_OF_SERVICE': "Validate system availability under load",
            'ELEVATION_OF_PRIVILEGE': "Test privilege escalation prevention"
        }
        
        if threat.stride_category in stride_validations:
            criteria.append(stride_validations[threat.stride_category])
        
        return criteria[:5]  # Limit to top 5 criteria
    
    def _generate_implementation_roadmap(self, treatment_plans: List[TreatmentPlanResult]) -> List[Dict[str, Any]]:
        """Generate implementation roadmap from treatment plans."""
        roadmap = []
        
        # Group by timeline and priority
        timeline_groups = {}
        for plan in treatment_plans:
            timeline = plan.implementation_timeline
            if timeline not in timeline_groups:
                timeline_groups[timeline] = []
            timeline_groups[timeline].append(plan)
        
        # Create roadmap milestones
        phase = 1
        for timeline in sorted(timeline_groups.keys()):
            plans = timeline_groups[timeline]
            
            milestone = {
                'phase': phase,
                'timeline': timeline,
                'plans_count': len(plans),
                'total_cost': sum(p.cost_estimate.get('total_cost', 0) for p in plans),
                'expected_effectiveness': sum(p.expected_effectiveness for p in plans) / len(plans),
                'strategies': list(set(p.strategy for p in plans))
            }
            
            roadmap.append(milestone)
            phase += 1
        
        return roadmap
    
    def _calculate_effectiveness_metrics(self, treatment_plans: List[TreatmentPlanResult]) -> Dict[str, float]:
        """Calculate effectiveness metrics across all treatment plans."""
        if not treatment_plans:
            return {}
        
        total_effectiveness = sum(p.expected_effectiveness for p in treatment_plans)
        avg_effectiveness = total_effectiveness / len(treatment_plans)
        
        # Calculate effectiveness by strategy
        strategy_effectiveness = {}
        for plan in treatment_plans:
            strategy = plan.strategy
            if strategy not in strategy_effectiveness:
                strategy_effectiveness[strategy] = []
            strategy_effectiveness[strategy].append(plan.expected_effectiveness)
        
        # Average effectiveness per strategy
        for strategy in strategy_effectiveness:
            values = strategy_effectiveness[strategy]
            strategy_effectiveness[strategy] = sum(values) / len(values)
        
        return {
            'overall_effectiveness': round(avg_effectiveness, 3),
            'strategy_effectiveness': strategy_effectiveness,
            'high_effectiveness_count': sum(1 for p in treatment_plans if p.expected_effectiveness >= 0.8)
        }
    
    def _generate_cost_summary(self, treatment_plans: List[TreatmentPlanResult], 
                             total_cost: float) -> Dict[str, Any]:
        """Generate comprehensive cost summary."""
        if not treatment_plans:
            return {'total_cost': 0}
        
        # Cost by strategy
        strategy_costs = {}
        for plan in treatment_plans:
            strategy = plan.strategy
            plan_cost = plan.cost_estimate.get('total_cost', 0)
            strategy_costs[strategy] = strategy_costs.get(strategy, 0) + plan_cost
        
        # Cost effectiveness ratio
        total_effectiveness = sum(p.expected_effectiveness for p in treatment_plans)
        cost_effectiveness_ratio = total_cost / total_effectiveness if total_effectiveness > 0 else 0
        
        return {
            'total_cost': int(total_cost),
            'strategy_costs': strategy_costs,
            'average_cost_per_plan': int(total_cost / len(treatment_plans)),
            'cost_effectiveness_ratio': round(cost_effectiveness_ratio, 2),
            'currency': 'USD'
        }
    
    def _get_plan_priority(self, plan: TreatmentPlan) -> int:
        """Get priority level for treatment plan (1=highest, 5=lowest)."""
        strategy_priorities = {
            'AVOID': 1,     # Highest priority
            'MITIGATE': 2,  # High priority
            'TRANSFER': 3,  # Medium priority
            'ACCEPT': 4     # Lower priority
        }
        
        return strategy_priorities.get(plan.treatment_strategy, 3)