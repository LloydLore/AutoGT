"""Threats command group for AutoGT CLI.

Reference: contracts/cli.md threats identify command
Handles threat scenario identification for TARA analyses.
"""

import click
import logging
import json
from typing import List, Dict, Any
from uuid import UUID

from ...lib.exceptions import AutoGTError
from ...services.database import DatabaseService
from ...services.autogen_agent import AutoGenTaraAgent
from ...models.analysis import TaraAnalysis
from ...models.asset import Asset
from ...models.threat import ThreatScenario, ThreatActor
from ...lib.config import Config


logger = logging.getLogger('autogt.cli.threats')


@click.group()
def threats():
    """Manage threat scenarios for TARA analyses."""
    pass


@threats.command()
@click.argument('analysis_id', required=True)
@click.option('--ai-mode', is_flag=True, help='Use AI-powered threat identification')
@click.pass_context
def identify(ctx: click.Context, analysis_id: str, ai_mode: bool) -> None:
    """Identify threat scenarios for analysis assets.
    
    Uses AI-powered analysis to identify potential threat scenarios
    for all assets in the specified analysis.
    
    Example:
        autogt threats identify abc12345
        autogt threats identify abc12345 --ai-mode
    """
    try:
        click.echo(f"🔍 Identifying threats for analysis: {analysis_id}")
        
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
            
            # Get all assets for this analysis
            assets = session.query(Asset).filter(
                Asset.analysis_id == resolved_id
            ).all()
            
            if not assets:
                raise AutoGTError(f"No assets found for analysis {analysis_id}. Run 'autogt assets define' first.")
            
            click.echo(f"🎯 Target analysis: {analysis.analysis_name}")
            click.echo(f"📊 Found {len(assets)} assets to analyze")
            
            threats_added = 0
            
            if ai_mode:
                # AI-powered threat identification
                click.echo("\n🤖 Using AI-powered threat identification...")
                threats_added = _ai_threat_identification(session, analysis, assets, config)
            else:
                # Rule-based threat identification
                click.echo("\n📋 Using rule-based threat identification...")
                threats_added = _rule_based_threat_identification(session, analysis, assets)
            
            # Commit all changes
            session.commit()
            
            # Summary
            click.echo(f"\n🎉 Threat identification completed!")
            click.echo(f"📊 Threats identified: {threats_added}")
            click.echo(f"📈 Assets analyzed: {len(assets)}")
            
            if threats_added > 0:
                click.echo(f"\n💡 Next steps:")
                click.echo(f"   • Run: autogt risks calculate {analysis_id}")
                click.echo(f"   • Run: autogt export {analysis_id}")
                
    except Exception as e:
        logger.error(f"Threat identification failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to identify threats: {e}")


def _resolve_analysis_id(session, analysis_id: str) -> UUID:
    """Resolve partial analysis ID to full UUID."""
    # Remove dashes and normalize
    normalized_id = analysis_id.replace('-', '')
    
    if len(normalized_id) < 32:  # Partial ID
        # Convert to UUID format for LIKE query
        from sqlalchemy import text
        result = session.execute(
            text("SELECT id FROM tara_analyses WHERE REPLACE(CAST(id as TEXT), '-', '') LIKE :partial_id || '%'"),
            {"partial_id": normalized_id}
        ).first()
        
        if not result:
            raise AutoGTError(f"No analysis found matching ID: {analysis_id}")
        
        return result[0]
    else:
        # Try to construct full UUID
        try:
            return UUID(analysis_id)
        except ValueError:
            # Try with dashes if needed
            if len(normalized_id) == 32:
                formatted_uuid = f"{normalized_id[:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:]}"
                return UUID(formatted_uuid)
            else:
                raise AutoGTError(f"Invalid analysis ID format: {analysis_id}")


def _ai_threat_identification(session, analysis: TaraAnalysis, assets: List[Asset], config: Config) -> int:
    """AI-powered threat identification using AutoGen agents with retry mechanism."""
    import asyncio
    
    try:
        # Initialize AI agent
        logger.info("Initializing AI agent for threat identification")
        gemini_config = config.get_gemini_config()
        ai_agent = AutoGenTaraAgent(gemini_config)
        
        click.echo("   🤖 AutoGen agents initialized")
        logger.info(f"✅ Using model: {gemini_config.model_name}")
        logger.info(f"📡 API endpoint: {gemini_config.base_url}")
        
        threats_added = 0
        
        for asset in assets:
            click.echo(f"   🔍 Analyzing asset: {asset.name}")
            logger.info(f"🎯 Starting threat analysis for asset: {asset.name} (Type: {asset.asset_type.value})")
            
            # Prepare context for AI analysis
            context = {
                "analysis_name": analysis.analysis_name,
                "vehicle_model": analysis.vehicle_model,
                "asset_name": asset.name,
                "asset_type": asset.asset_type.value,
                "criticality": asset.criticality_level.value,
                "interfaces": asset.interfaces,
                "data_flows": asset.data_flows,
                "description": asset.security_properties.get("description", "")
            }
            
            logger.debug(f"📋 Analysis context: {context}")
            
            # Use AI agent for threat identification (async call with retry)
            logger.info("🚀 Calling AI API (with up to 3 retry attempts)...")
            click.echo(f"      ⏳ Sending request to {gemini_config.model_name}...")
            
            try:
                threat_results = asyncio.run(ai_agent.identify_threats(context, max_retries=3))
                
                logger.info(f"✅ AI API returned {len(threat_results.get('threats', []))} threats")
                
                # Process AI results
                if "threats" in threat_results:
                    for threat_data in threat_results["threats"]:
                        logger.debug(f"💾 Saving threat: {threat_data['name']}")
                        threat_scenario = _create_threat_scenario(
                            asset, threat_data, "AI_GENERATED"
                        )
                        session.add(threat_scenario)
                        threats_added += 1
                        click.echo(f"      ✅ AI threat: {threat_data['name']}")
                else:
                    logger.warning(f"⚠️ No threats returned for asset {asset.name}")
                    
            except Exception as e:
                # This exception means all retries failed
                logger.error(f"❌ All retry attempts failed for asset {asset.name}: {e}")
                click.echo(f"      ⚠️ AI analysis failed after 3 retries for {asset.name}")
                click.echo(f"      🔄 Falling back to rule-based identification...")
                
                # Fall back to rule-based for this specific asset
                fallback_threats = _rule_based_threat_identification_for_asset(session, analysis, asset)
                threats_added += fallback_threats
            
        logger.info(f"🎉 Threat identification complete: {threats_added} threats added")
        return threats_added
        
    except Exception as e:
        logger.error(f"❌ AI initialization or processing failed: {e}", exc_info=True)
        click.echo(f"   ⚠️ AI mode failed completely, falling back to rule-based approach...")
        return _rule_based_threat_identification(session, analysis, assets)


def _rule_based_threat_identification_for_asset(session, analysis: TaraAnalysis, asset: Asset) -> int:
    """Rule-based threat identification for a single asset (used as fallback)."""
    return _rule_based_threat_identification(session, analysis, [asset])


def _rule_based_threat_identification(session, analysis: TaraAnalysis, assets: List[Asset]) -> int:
    """Rule-based threat identification using automotive cybersecurity patterns."""
    threats_added = 0
    
    # Define automotive threat patterns
    threat_patterns = {
        "HARDWARE": [
            {
                "name": "Physical Tampering",
                "actor": "CRIMINAL",
                "motivation": "Unauthorized access to vehicle systems",
                "attack_vectors": ["Physical access", "Diagnostic port"],
                "prerequisites": ["Vehicle access", "Basic tools"]
            },
            {
                "name": "Firmware Modification",
                "actor": "INSIDER", 
                "motivation": "System manipulation or data extraction",
                "attack_vectors": ["JTAG interface", "Boot sequence"],
                "prerequisites": ["Physical access", "Specialized tools", "Technical knowledge"]
            }
        ],
        "SOFTWARE": [
            {
                "name": "Code Injection",
                "actor": "CRIMINAL",
                "motivation": "Remote control or data theft",
                "attack_vectors": ["Network interface", "Input validation flaws"],
                "prerequisites": ["Network access", "Vulnerability knowledge"]
            },
            {
                "name": "Malware Installation",
                "actor": "NATION_STATE",
                "motivation": "Persistent access and surveillance",
                "attack_vectors": ["OTA updates", "USB interface", "Bluetooth"],
                "prerequisites": ["Communication channel", "Execution rights"]
            }
        ],
        "COMMUNICATION": [
            {
                "name": "Man-in-the-Middle Attack",
                "actor": "CRIMINAL",
                "motivation": "Data interception and manipulation",
                "attack_vectors": ["Wireless communication", "Network protocols"],
                "prerequisites": ["Proximity to target", "Radio equipment"]
            },
            {
                "name": "Protocol Exploitation",
                "actor": "SCRIPT_KIDDIE",
                "motivation": "System disruption or unauthorized access",
                "attack_vectors": ["CAN bus", "Ethernet", "Bluetooth"],
                "prerequisites": ["Protocol knowledge", "Access to network"]
            }
        ]
    }
    
    # Special threats for high-criticality assets
    critical_threats = [
        {
            "name": "Advanced Persistent Threat",
            "actor": "NATION_STATE",
            "motivation": "Long-term surveillance and control",
            "attack_vectors": ["Supply chain", "Zero-day exploits", "Social engineering"],
            "prerequisites": ["Significant resources", "Advanced capabilities"]
        },
        {
            "name": "Safety-Critical System Attack",
            "actor": "CRIMINAL",
            "motivation": "Extortion or causing harm",
            "attack_vectors": ["Remote access", "Physical manipulation"],
            "prerequisites": ["System knowledge", "Attack tools"]
        }
    ]
    
    for asset in assets:
        click.echo(f"   📋 Analyzing asset: {asset.name} ({asset.asset_type.value})")
        
        # Apply type-specific threats
        asset_type = asset.asset_type.value
        if asset_type in threat_patterns:
            for threat_data in threat_patterns[asset_type]:
                threat_scenario = _create_threat_scenario(
                    asset, threat_data, "RULE_BASED"
                )
                session.add(threat_scenario)
                threats_added += 1
                click.echo(f"      ✅ Rule-based threat: {threat_data['name']}")
        
        # Apply critical threats for high-criticality assets
        if asset.criticality_level.value in ["HIGH", "VERY_HIGH"]:
            for threat_data in critical_threats:
                threat_scenario = _create_threat_scenario(
                    asset, threat_data, "CRITICALITY_BASED"
                )
                session.add(threat_scenario)
                threats_added += 1
                click.echo(f"      ✅ Critical threat: {threat_data['name']}")
    
    return threats_added


def _create_threat_scenario(asset: Asset, threat_data: Dict[str, Any], source: str) -> ThreatScenario:
    """Create a ThreatScenario object from threat data."""
    # Map actor string to enum
    actor_mapping = {
        "SCRIPT_KIDDIE": ThreatActor.SCRIPT_KIDDIE,
        "CRIMINAL": ThreatActor.CRIMINAL,
        "NATION_STATE": ThreatActor.NATION_STATE,
        "INSIDER": ThreatActor.INSIDER,
        "EXTERNAL_ATTACKER": ThreatActor.CRIMINAL  # Fallback mapping
    }
    
    actor = actor_mapping.get(threat_data["actor"], ThreatActor.CRIMINAL)
    
    return ThreatScenario(
        asset_id=asset.id,
        threat_name=threat_data["name"],
        threat_actor=actor,
        motivation=threat_data["motivation"],
        attack_vectors=threat_data.get("attack_vectors", []),
        prerequisites=threat_data.get("prerequisites", []),
        iso_section=f"21434-15.7-{source}"
    )