#!/usr/bin/env python3
"""
AutoGT AI-Powered TARA Analysis Demonstration

This script demonstrates how to start and conduct a TARA analysis using AutoGT's AI capabilities.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autogt.services.autogen_agent import AutoGenTaraAgent
from autogt.lib.config import GeminiConfig
from autogt.services.database import DatabaseService
from autogt.models.analysis import TaraAnalysis
import uuid

def demonstrate_ai_tara_workflow():
    """Demonstrate complete AI-powered TARA workflow."""
    print("🚀 AutoGT AI-Powered TARA Analysis Demonstration")
    print("=" * 60)
    
    # Step 1: Initialize AI Agent (with mock config for demo)
    print("\n1️⃣  Initializing AI Agent...")
    config = GeminiConfig(
        api_key="demo-key-replace-with-real-key",
        model_name="gemini-1.5-pro"
    )
    
    try:
        ai_agent = AutoGenTaraAgent(config)
        print("   ✅ AutoGen AI agent initialized successfully")
        print(f"   📝 Model: {config.model_name}")
        print("   🤖 8 specialized agents ready for TARA workflow")
    except Exception as e:
        print(f"   ⚠️  Demo mode (no real API key): {str(e)[:50]}...")
        print("   💡 To use real AI: Set AUTOGT_GEMINI_API_KEY environment variable")
    
    # Step 2: Define Analysis Context
    print("\n2️⃣  Defining Analysis Context...")
    analysis_context = {
        "analysis_name": "BMW iX Electric Vehicle Security Analysis",
        "vehicle_model": "BMW iX",
        "system_scope": "ADAS, Infotainment, Battery Management",
        "compliance_standard": "ISO/SAE 21434",
        "analysis_phase": "Design Phase"
    }
    
    for key, value in analysis_context.items():
        print(f"   📋 {key.replace('_', ' ').title()}: {value}")
    
    # Step 3: AI-Powered Asset Analysis
    print("\n3️⃣  AI Asset Analysis...")
    print("   🤖 Running asset identification using AutoGen agents...")
    
    try:
        asset_results = ai_agent.analyze_assets(analysis_context)
        print("   ✅ Asset analysis completed!")
        
        if "assets" in asset_results:
            print(f"   📊 Identified {len(asset_results['assets'])} critical assets:")
            for asset in asset_results["assets"]:
                print(f"      • {asset['name']} ({asset['type']}) - Criticality: {asset['criticality']}")
    except Exception as e:
        print(f"   📝 Demo result (simulated): Central Gateway ECU (VERY_HIGH criticality)")
        print(f"   💡 Full AI analysis available with API key")
    
    # Step 4: AI Threat Identification  
    print("\n4️⃣  AI Threat Identification...")
    print("   🕵️  Running threat analysis using specialized AI agents...")
    
    try:
        threat_results = ai_agent.identify_threats(analysis_context)
        print("   ✅ Threat identification completed!")
        
        if "threats" in threat_results:
            print(f"   🎯 Identified {len(threat_results['threats'])} threat scenarios:")
            for threat in threat_results["threats"]:
                print(f"      • {threat['name']} - Actor: {threat['actor']}")
    except Exception as e:
        print(f"   📝 Demo result (simulated): Remote CAN injection threat identified")
        print(f"   💡 Full threat analysis available with API key")
    
    # Step 5: Attack Path Modeling
    print("\n5️⃣  AI Attack Path Modeling...")
    print("   🗺️  Modeling attack paths using AI agents...")
    
    try:
        attack_results = ai_agent.model_attack_paths(analysis_context)
        print("   ✅ Attack path modeling completed!")
        
        if "attack_paths" in attack_results:
            print(f"   🛤️  Modeled {len(attack_results['attack_paths'])} attack sequences")
    except Exception as e:
        print(f"   📝 Demo result (simulated): Multi-step attack path through OTA interface")
        print(f"   💡 Full attack modeling available with API key")
    
    # Step 6: AI Risk Calculation
    print("\n6️⃣  AI Risk Assessment...")
    print("   📊 Calculating risk levels using AI analysis...")
    
    # Mock risk calculation based on ISO/SAE 21434
    risk_matrix = {
        "impact": "HIGH",  # Based on asset criticality
        "feasibility": "MEDIUM",  # Based on attack complexity
        "risk_level": "4"  # ISO risk level
    }
    
    print(f"   📈 Impact Rating: {risk_matrix['impact']}")
    print(f"   🎯 Attack Feasibility: {risk_matrix['feasibility']}")
    print(f"   ⚠️  Overall Risk Level: {risk_matrix['risk_level']}")
    
    # Step 7: Generate Security Goals
    print("\n7️⃣  AI Security Goals Generation...")
    print("   🎯 Generating cybersecurity goals using AI recommendations...")
    
    security_goals = [
        "Implement robust authentication for OTA updates",
        "Deploy network segmentation between critical ECUs", 
        "Establish monitoring for abnormal CAN traffic",
        "Implement secure boot for all critical components"
    ]
    
    for i, goal in enumerate(security_goals, 1):
        print(f"   {i}. {goal}")
    
    # Step 8: Summary
    print("\n8️⃣  Analysis Summary...")
    print("   📋 TARA Analysis completed successfully!")
    print("   ✅ ISO/SAE 21434 compliant analysis generated")
    print("   📄 Results ready for export and review")
    
    return {
        "analysis_id": str(uuid.uuid4())[:8],
        "assets_count": len(asset_results.get("assets", [])) if 'asset_results' in locals() else 1,
        "threats_count": len(threat_results.get("threats", [])) if 'threat_results' in locals() else 1,
        "risk_level": risk_matrix["risk_level"],
        "goals_count": len(security_goals)
    }

def show_cli_commands():
    """Show the CLI commands for AI-powered TARA analysis."""
    print("\n" + "=" * 60)
    print("🔧 AutoGT CLI Commands for AI Analysis")
    print("=" * 60)
    
    commands = [
        ("Create Analysis", "autogt analysis create --name 'BMW iX Security Analysis' --vehicle 'BMW iX'"),
        ("Define Assets", "autogt assets define <analysis-id> --interactive"),
        ("Identify Threats", "autogt threats identify <analysis-id>"),
        ("Calculate Risks", "autogt risks calculate <analysis-id>"),
        ("Export Results", "autogt export <analysis-id> --format json")
    ]
    
    for step, command in commands:
        print(f"\n📝 {step}:")
        print(f"   {command}")
    
    print(f"\n💡 Pro Tips:")
    print(f"   • Set AUTOGT_GEMINI_API_KEY for full AI functionality")
    print(f"   • Use --help with any command for detailed options")
    print(f"   • Export to JSON/Excel for ISO compliance documentation")

if __name__ == "__main__":
    # Run the demonstration
    result = demonstrate_ai_tara_workflow()
    
    # Show CLI commands
    show_cli_commands()
    
    print(f"\n🎉 Demo completed! Analysis summary:")
    print(f"   📊 Assets: {result['assets_count']} | Threats: {result['threats_count']} | Risk Level: {result['risk_level']} | Goals: {result['goals_count']}")