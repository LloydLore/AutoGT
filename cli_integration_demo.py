#!/usr/bin/env python3
"""
AutoGT CLI Integration Demonstration

This shows how the AI workflow results can be integrated 
with AutoGT CLI commands for real-world usage.
"""

import os
import json
import subprocess
from datetime import datetime

def demonstrate_cli_integration():
    """Demonstrate CLI integration with AI workflow results."""
    
    print("🔄 AutoGT CLI Integration with AI Workflow")
    print("=" * 55)
    
    # Analysis data from AI workflow
    analysis_id = "33ac746d-fe83-41fe-a991-2337eaff8136" 
    analysis_dir = f"/home/lj/Documents/AutoGT/autogt-output/{analysis_id}"
    
    print(f"📊 AI Analysis: test-ai-workflow")
    print(f"🔍 Analysis ID: {analysis_id}")
    print(f"📁 Output Directory: {analysis_dir}")
    
    # Show CLI equivalents for AI workflow steps
    print(f"\n🤖 AI Workflow → CLI Command Mapping:")
    print(f"=" * 45)
    
    cli_mappings = [
        ("Step 1: Analysis Creation", "uv run autogt analysis create --name 'test-ai-workflow'"),
        ("Step 2: Asset Definition", "uv run autogt assets import assets.csv"),  
        ("Step 3: Impact Assessment", "uv run autogt analysis impacts assess <analysis-id>"),
        ("Step 4: Threat Discovery", "uv run autogt threats identify <analysis-id>"),
        ("Step 5: Attack Path Modeling", "uv run autogt analysis attack-paths <analysis-id>"),
        ("Step 6: Feasibility Analysis", "uv run autogt analysis feasibility <analysis-id>"),
        ("Step 7: Risk Calculation", "uv run autogt risks calculate <analysis-id>"),
        ("Step 8: Treatment Planning", "uv run autogt risks treat <analysis-id>"),
        ("Step 9: Goals Definition", "uv run autogt analysis goals <analysis-id>"),
        ("Final: Export Results", "uv run autogt export analysis <analysis-id>")
    ]
    
    for step, command in cli_mappings:
        print(f"   {step}")
        print(f"   💻 {command}")
        print()
    
    # Show data validation commands
    print(f"📋 Data Validation Commands:")
    print(f"=" * 30)
    
    validation_commands = [
        "uv run autogt analysis list",
        "uv run autogt assets list <analysis-id>",
        "uv run autogt threats list <analysis-id>", 
        "uv run autogt risks list <analysis-id>"
    ]
    
    for cmd in validation_commands:
        print(f"   💻 {cmd}")
    
    # Load and display AI results summary
    print(f"\n🤖 AI Analysis Results Summary:")
    print(f"=" * 35)
    
    # Load assets
    with open(f"{analysis_dir}/assets.json", 'r') as f:
        assets = json.load(f)
    
    print(f"📊 Assets Identified: {len(assets)}")
    for asset in assets:
        confidence = asset.get('ai_confidence_score', 0)
        status_icon = "🟢" if confidence >= 0.9 else "🟡" if confidence >= 0.8 else "🔴"
        print(f"   {status_icon} {asset['name']} ({asset['asset_type']}) - {confidence:.2f}")
    
    # Load threats  
    with open(f"{analysis_dir}/threats.json", 'r') as f:
        threats = json.load(f)
    
    print(f"\n🎯 Threats Discovered: {len(threats)}")
    for threat in threats:
        confidence = threat.get('ai_discovery_confidence', 0)
        status_icon = "🔴" if confidence >= 0.9 else "🟡" if confidence >= 0.8 else "🟢"
        print(f"   {status_icon} {threat['name']} - {confidence:.2f}")
    
    # Load risks
    with open(f"{analysis_dir}/risks.json", 'r') as f:
        risks = json.load(f)
    
    print(f"\n⚠️  Risk Assessment: {len(risks)} risks calculated")
    for risk in risks:
        level = risk['risk_level']
        score = risk['calculated_risk_score']
        level_icon = "🔴" if level == "VERY_HIGH" else "🟡" if level in ["HIGH", "MEDIUM"] else "🟢"
        print(f"   {level_icon} {risk['threat_name']} → {risk['asset_name']}: {level} ({score:.1f})")
    
    # Show export capabilities
    print(f"\n📤 Export & Integration Options:")
    print(f"=" * 35)
    
    export_options = [
        ("JSON Export", "Complete analysis data in structured JSON format"),
        ("CSV Export", "Assets, threats, and risks in CSV format for Excel"),
        ("PDF Report", "Executive summary with visualizations"),
        ("SARIF Export", "Security findings in industry standard format"),
        ("STIX/TAXII", "Threat intelligence sharing format")
    ]
    
    for format_type, description in export_options:
        print(f"   📊 {format_type}: {description}")
    
    print(f"\n✅ AutoGT CLI Integration Complete")
    print(f"🔗 Analysis results ready for:")
    print(f"   • Further CLI processing and refinement")
    print(f"   • Export to multiple formats")  
    print(f"   • Integration with existing security tools")
    print(f"   • Compliance reporting (ISO/SAE 21434, UN-R 155)")

def show_real_world_usage():
    """Show real-world usage scenarios."""
    print(f"\n🌍 Real-World Usage Scenarios:")
    print(f"=" * 35)
    
    scenarios = [
        {
            "title": "OEM Cybersecurity Assessment",
            "description": "Vehicle manufacturer conducting pre-production TARA",
            "workflow": [
                "1. Import vehicle specification documents", 
                "2. AI identifies all cybersecurity assets",
                "3. Threat hunting discovers attack scenarios", 
                "4. Risk assessment prioritizes treatments",
                "5. Export compliance report for regulators"
            ]
        },
        {
            "title": "Supplier Security Validation", 
            "description": "Tier-1 supplier validating component security",
            "workflow": [
                "1. Load component specifications and interfaces",
                "2. AI analyzes attack surfaces and entry points", 
                "3. Model attack paths through component ecosystem",
                "4. Calculate residual risks after controls",
                "5. Generate security requirements for sub-suppliers"
            ]
        },
        {
            "title": "Incident Response Planning",
            "description": "Security team preparing for cybersecurity incidents", 
            "workflow": [
                "1. Import current vehicle cybersecurity architecture",
                "2. AI discovers potential incident scenarios",
                "3. Model attack progression and lateral movement",
                "4. Prioritize response procedures by risk level", 
                "5. Export incident playbooks and detection rules"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 Scenario {i}: {scenario['title']}")
        print(f"   {scenario['description']}")
        print(f"   Workflow:")
        for step in scenario['workflow']:
            print(f"      {step}")

if __name__ == "__main__":
    demonstrate_cli_integration()
    show_real_world_usage()