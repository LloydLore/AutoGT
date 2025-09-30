"""Risks command group for AutoGT CLI.

Reference: contracts/cli.md risks calculate command
Handles risk value calculation for TARA analyses.
"""

import click
import logging
import math
from typing import List, Dict, Any
from uuid import UUID

from ...lib.exceptions import AutoGTError
from ...services.database import DatabaseService
from ...services.autogen_agent import AutoGenTaraAgent
from ...models.analysis import TaraAnalysis
from ...models.asset import Asset
from ...models.threat import ThreatScenario
from ...models.impact import ImpactRating, SafetyImpact, FinancialImpact, OperationalImpact, PrivacyImpact
from ...models.attack_feasibility import AttackFeasibility, ElapsedTime, SpecialistExpertise, KnowledgeOfTarget, WindowOfOpportunity, EquipmentRequired
from ...models.risk import RiskValue, RiskLevel
from ...models.attack_path import AttackPath
from ...lib.config import Config


logger = logging.getLogger('autogt.cli.risks')


@click.group()
def risks():
    """Manage risk calculations for TARA analyses.""" 
    pass


@risks.command()
@click.argument('analysis_id', required=True)
@click.option('--ai-mode', is_flag=True, help='Use AI-powered risk assessment')
@click.pass_context
def calculate(ctx: click.Context, analysis_id: str, ai_mode: bool) -> None:
    """Calculate risk values for analysis.
    
    Calculates risk values based on impact ratings and attack feasibility
    assessments for all threat scenarios in the analysis.
    
    Example:
        autogt risks calculate abc12345
        autogt risks calculate abc12345 --ai-mode
    """
    try:
        click.echo(f"⚖️ Calculating risks for analysis: {analysis_id}")
        
        # Get services
        config = ctx.obj.get('config_instance')
        if not config:
            config = Config()
        
        db_service = DatabaseService(database_url=config.get_database_url())
        
        # Resolve analysis ID and verify it exists
        with db_service.get_session() as session:
            resolved_id = _resolve_analysis_id(session, analysis_id)
            analysis = session.query(TaraAnalysis).filter(
                TaraAnalysis.id == resolved_id
            ).first()
            
            if not analysis:
                raise AutoGTError(f"Analysis {analysis_id} not found")
            
            # Get all threat scenarios for this analysis
            threat_scenarios = session.query(ThreatScenario).join(Asset).filter(
                Asset.analysis_id == resolved_id
            ).all()
            
            if not threat_scenarios:
                raise AutoGTError(f"No threat scenarios found for analysis {analysis_id}. Run 'autogt threats identify' first.")
            
            click.echo(f"🎯 Target analysis: {analysis.analysis_name}")
            click.echo(f"📊 Found {len(threat_scenarios)} threat scenarios to assess")
            
            risks_calculated = 0
            
            if ai_mode:
                # AI-powered risk assessment
                click.echo("\n🤖 Using AI-powered risk assessment...")
                risks_calculated = _ai_risk_assessment(session, analysis, threat_scenarios, config)
            else:
                # Rule-based risk assessment
                click.echo("\n📋 Using rule-based risk assessment...")
                risks_calculated = _rule_based_risk_assessment(session, analysis, threat_scenarios)
            
            # Commit all changes
            session.commit()
            
            # Summary
            click.echo(f"\n🎉 Risk calculation completed!")
            click.echo(f"⚖️ Risk assessments: {risks_calculated}")
            click.echo(f"📊 Threat scenarios processed: {len(threat_scenarios)}")
            
            # Risk summary
            _display_risk_summary(session, resolved_id)
            
            if risks_calculated > 0:
                click.echo(f"\n💡 Next steps:")
                click.echo(f"   • Run: autogt export {analysis_id} --format json")
                click.echo(f"   • Review high-risk scenarios for mitigation")
                
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to calculate risks: {e}")


def _resolve_analysis_id(session, analysis_id: str) -> UUID:
    """Resolve partial analysis ID to full UUID."""
    # Same implementation as in threats.py
    normalized_id = analysis_id.replace('-', '')
    
    if len(normalized_id) < 32:  # Partial ID
        from sqlalchemy import text
        result = session.execute(
            text("SELECT id FROM tara_analyses WHERE REPLACE(CAST(id as TEXT), '-', '') LIKE :partial_id || '%'"),
            {"partial_id": normalized_id}
        ).first()
        
        if not result:
            raise AutoGTError(f"No analysis found matching ID: {analysis_id}")
        
        return result[0]
    else:
        try:
            return UUID(analysis_id)
        except ValueError:
            if len(normalized_id) == 32:
                formatted_uuid = f"{normalized_id[:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:]}"
                return UUID(formatted_uuid)
            else:
                raise AutoGTError(f"Invalid analysis ID format: {analysis_id}")


def _ai_risk_assessment(session, analysis: TaraAnalysis, threat_scenarios: List[ThreatScenario], config: Config) -> int:
    """AI-powered risk assessment using AutoGen agents."""
    try:
        # Initialize AI agent
        gemini_config = config.get_gemini_config()
        ai_agent = AutoGenTaraAgent(gemini_config)
        
        click.echo("   🤖 AutoGen risk assessment agents initialized")
        
        risks_calculated = 0
        
        for threat_scenario in threat_scenarios:
            click.echo(f"   ⚖️ Assessing: {threat_scenario.threat_name}")
            
            # Prepare context for AI analysis
            context = {
                "analysis_name": analysis.analysis_name,
                "vehicle_model": analysis.vehicle_model,
                "asset_name": threat_scenario.asset.name,
                "asset_type": threat_scenario.asset.asset_type.value,
                "criticality": threat_scenario.asset.criticality_level.value,
                "threat_name": threat_scenario.threat_name,
                "threat_actor": threat_scenario.threat_actor.value,
                "motivation": threat_scenario.motivation,
                "attack_vectors": threat_scenario.attack_vectors,
                "prerequisites": threat_scenario.prerequisites
            }
            
            # Use AI for impact and feasibility assessment (mock implementation)
            impact_score, feasibility_score, risk_level = _calculate_ai_risk_scores(context)
            
            # Create impact rating
            impact_rating = _create_impact_rating(threat_scenario, impact_score)
            session.add(impact_rating)
            session.flush()  # Get the ID
            
            # Create feasibility assessment
            feasibility = _create_feasibility_assessment(session, threat_scenario, feasibility_score)
            session.add(feasibility)
            session.flush()  # Get the ID
            
            # Create risk value
            risk_value = _create_risk_value(
                threat_scenario, impact_rating, feasibility, risk_level, impact_score * feasibility_score
            )
            session.add(risk_value)
            
            risks_calculated += 1
            click.echo(f"      ✅ Risk level: {risk_level.value} (Score: {impact_score * feasibility_score:.2f})")
            
        return risks_calculated
        
    except Exception as e:
        click.echo(f"   ⚠️ AI mode failed, falling back to rule-based: {str(e)[:50]}...")
        return _rule_based_risk_assessment(session, analysis, threat_scenarios)


def _rule_based_risk_assessment(session, analysis: TaraAnalysis, threat_scenarios: List[ThreatScenario]) -> int:
    """Rule-based risk assessment using ISO/SAE 21434 methodology."""
    risks_calculated = 0
    
    for threat_scenario in threat_scenarios:
        click.echo(f"   📋 Assessing: {threat_scenario.threat_name}")
        
        # Calculate impact score based on asset criticality and threat type
        impact_score = _calculate_impact_score(threat_scenario)
        
        # Calculate feasibility score based on threat characteristics
        feasibility_score = _calculate_feasibility_score(threat_scenario)
        
        # Calculate combined risk level
        risk_level = _calculate_risk_level(impact_score, feasibility_score)
        
        # Create impact rating
        impact_rating = _create_impact_rating(threat_scenario, impact_score)
        session.add(impact_rating)
        session.flush()
        
        # Create feasibility assessment
        feasibility = _create_feasibility_assessment(session, threat_scenario, feasibility_score)
        session.add(feasibility)
        session.flush()
        
        # Create risk value
        risk_value = _create_risk_value(
            threat_scenario, impact_rating, feasibility, risk_level, impact_score * feasibility_score
        )
        session.add(risk_value)
        
        risks_calculated += 1
        click.echo(f"      ✅ Risk level: {risk_level.value} (Impact: {impact_score:.1f}, Feasibility: {feasibility_score:.1f})")
    
    return risks_calculated


def _calculate_ai_risk_scores(context: Dict[str, Any]) -> tuple:
    """Calculate AI-based risk scores (mock implementation for demo)."""
    # Mock AI-based scoring - in production, this would use actual AI agents
    criticality_weight = {
        "VERY_HIGH": 4.0,
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0
    }.get(context["criticality"], 2.0)
    
    actor_weight = {
        "NATION_STATE": 4.0,
        "CRIMINAL": 3.0,
        "INSIDER": 2.5,
        "SCRIPT_KIDDIE": 1.5
    }.get(context["threat_actor"], 2.0)
    
    # AI would analyze complexity based on attack vectors and prerequisites
    complexity = len(context.get("prerequisites", [])) * 0.5
    
    impact_score = min(4.0, criticality_weight * 0.8 + actor_weight * 0.2)
    feasibility_score = min(4.0, actor_weight * 0.7 - complexity * 0.3)
    
    risk_level = _calculate_risk_level(impact_score, feasibility_score)
    
    return impact_score, feasibility_score, risk_level


def _calculate_impact_score(threat_scenario: ThreatScenario) -> float:
    """Calculate impact score based on asset criticality and threat characteristics."""
    # Base score from asset criticality
    criticality_scores = {
        "VERY_HIGH": 4.0,
        "HIGH": 3.0, 
        "MEDIUM": 2.0,
        "LOW": 1.0
    }
    
    base_score = criticality_scores.get(threat_scenario.asset.criticality_level.value, 2.0)
    
    # Adjust based on threat actor capability
    actor_multiplier = {
        "NATION_STATE": 1.2,
        "CRIMINAL": 1.0,
        "INSIDER": 0.9,
        "SCRIPT_KIDDIE": 0.7
    }.get(threat_scenario.threat_actor.value, 1.0)
    
    return min(4.0, base_score * actor_multiplier)


def _calculate_feasibility_score(threat_scenario: ThreatScenario) -> float:
    """Calculate feasibility score based on attack complexity and prerequisites."""
    # Base feasibility from threat actor
    actor_scores = {
        "SCRIPT_KIDDIE": 1.0,
        "CRIMINAL": 2.0,
        "INSIDER": 3.0,
        "NATION_STATE": 4.0
    }
    
    base_score = actor_scores.get(threat_scenario.threat_actor.value, 2.0)
    
    # Reduce score based on complexity (more prerequisites = harder)
    complexity_penalty = len(threat_scenario.prerequisites) * 0.3
    attack_vector_penalty = max(0, len(threat_scenario.attack_vectors) - 1) * 0.2
    
    return max(1.0, base_score - complexity_penalty - attack_vector_penalty)


def _calculate_risk_level(impact_score: float, feasibility_score: float) -> RiskLevel:
    """Calculate risk level using ISO/SAE 21434 risk matrix."""
    # ISO/SAE 21434 risk matrix (simplified)
    risk_score = impact_score * feasibility_score
    
    if risk_score >= 12.0:
        return RiskLevel.VERY_HIGH
    elif risk_score >= 8.0:
        return RiskLevel.HIGH
    elif risk_score >= 4.0:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def _create_impact_rating(threat_scenario: ThreatScenario, impact_score: float) -> ImpactRating:
    """Create an ImpactRating object."""
    # Determine impact levels based on score (1-4 scale)
    if impact_score >= 3.5:
        safety_impact = SafetyImpact.HAZARDOUS
        financial_impact = FinancialImpact.SEVERE
        operational_impact = OperationalImpact.LOSS
        privacy_impact = PrivacyImpact.SEVERE
    elif impact_score >= 2.5:
        safety_impact = SafetyImpact.MAJOR
        financial_impact = FinancialImpact.MAJOR
        operational_impact = OperationalImpact.MAJOR
        privacy_impact = PrivacyImpact.MAJOR
    elif impact_score >= 1.5:
        safety_impact = SafetyImpact.MODERATE
        financial_impact = FinancialImpact.MODERATE
        operational_impact = OperationalImpact.DEGRADED
        privacy_impact = PrivacyImpact.MODERATE
    else:
        safety_impact = SafetyImpact.NONE
        financial_impact = FinancialImpact.NEGLIGIBLE
        operational_impact = OperationalImpact.NONE
        privacy_impact = PrivacyImpact.NONE
    
    impact_rating = ImpactRating(
        asset_id=threat_scenario.asset_id,
        safety_impact=safety_impact,
        financial_impact=financial_impact,
        operational_impact=operational_impact,
        privacy_impact=privacy_impact,
        impact_score=impact_score,
        iso_section="ISO/SAE 21434 Section 15.4.2"
    )
    
    # Calculate the impact score using the model's method
    impact_rating.impact_score = impact_rating.calculate_impact_score()
    
    return impact_rating


def _create_feasibility_assessment(session, threat_scenario: ThreatScenario, feasibility_score: float) -> AttackFeasibility:
    """Create an AttackFeasibility object with corresponding AttackPath."""
    # First create an AttackPath
    attack_path = AttackPath(
        threat_scenario_id=threat_scenario.id,
        step_sequence=1,  # Default single step
        attack_step=f"Attack step for {threat_scenario.threat_name}",
        intermediate_targets=threat_scenario.attack_vectors,
        technical_barriers=threat_scenario.prerequisites,
        required_resources={"complexity": "medium", "tools": "standard"}
    )
    session.add(attack_path)
    session.flush()  # Get the ID
    
    # Determine feasibility factors based on score (1-4 scale)
    if feasibility_score >= 3.5:
        elapsed_time = ElapsedTime.MINUTES
        specialist_expertise = SpecialistExpertise.NONE
        knowledge_of_target = KnowledgeOfTarget.PUBLIC
        window_of_opportunity = WindowOfOpportunity.UNLIMITED
        equipment_required = EquipmentRequired.STANDARD
    elif feasibility_score >= 2.5:
        elapsed_time = ElapsedTime.HOURS
        specialist_expertise = SpecialistExpertise.LIMITED
        knowledge_of_target = KnowledgeOfTarget.RESTRICTED
        window_of_opportunity = WindowOfOpportunity.MODERATE
        equipment_required = EquipmentRequired.SPECIALIZED
    elif feasibility_score >= 1.5:
        elapsed_time = ElapsedTime.DAYS
        specialist_expertise = SpecialistExpertise.PROFICIENT
        knowledge_of_target = KnowledgeOfTarget.SENSITIVE
        window_of_opportunity = WindowOfOpportunity.DIFFICULT
        equipment_required = EquipmentRequired.BESPOKE
    else:
        elapsed_time = ElapsedTime.WEEKS
        specialist_expertise = SpecialistExpertise.EXPERT
        knowledge_of_target = KnowledgeOfTarget.CRITICAL
        window_of_opportunity = WindowOfOpportunity.NONE
        equipment_required = EquipmentRequired.MULTIPLE_BESPOKE
    
    feasibility = AttackFeasibility(
        attack_path_id=attack_path.id,
        elapsed_time=elapsed_time,
        specialist_expertise=specialist_expertise,
        knowledge_of_target=knowledge_of_target,
        window_of_opportunity=window_of_opportunity,
        equipment_required=equipment_required,
        feasibility_score=feasibility_score
    )
    
    # Calculate the feasibility score using the model's method
    feasibility.feasibility_score = feasibility.calculate_feasibility_score()
    
    return feasibility


def _create_risk_value(threat_scenario: ThreatScenario, impact_rating, feasibility, risk_level: RiskLevel, risk_score: float) -> RiskValue:
    """Create a RiskValue object."""
    return RiskValue(
        asset_id=threat_scenario.asset_id,
        threat_scenario_id=threat_scenario.id,
        impact_rating_id=impact_rating.id,
        attack_feasibility_id=feasibility.id,
        risk_level=risk_level,
        risk_score=risk_score,
        calculation_method="ISO_SAE_21434"
    )


def _display_risk_summary(session, analysis_id: UUID) -> None:
    """Display risk summary statistics."""
    # Get risk distribution
    risk_counts = session.query(RiskValue).join(Asset).filter(
        Asset.analysis_id == analysis_id
    ).all()
    
    if not risk_counts:
        return
    
    # Count by risk level
    level_counts = {}
    total_score = 0
    for risk in risk_counts:
        level = risk.risk_level.value
        level_counts[level] = level_counts.get(level, 0) + 1
        total_score += risk.risk_score
    
    click.echo(f"\n📊 Risk Distribution:")
    for level in ["VERY_HIGH", "HIGH", "MEDIUM", "LOW"]:
        count = level_counts.get(level, 0)
        if count > 0:
            emoji = {
                "VERY_HIGH": "🔴",
                "HIGH": "🟠", 
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }[level]
            click.echo(f"   {emoji} {level}: {count} risks")
    
    avg_score = total_score / len(risk_counts) if risk_counts else 0
    click.echo(f"   📊 Average Risk Score: {avg_score:.2f}")