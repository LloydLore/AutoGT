#!/usr/bin/env python3
"""
Simple AI workflow validation using file-based operations
"""
import json
import os

def validate_ai_workflow():
    """Validate the AI workflow results."""
    analysis_dir = "/home/lj/Documents/AutoGT/autogt-output/33ac746d-fe83-41fe-a991-2337eaff8136"
    
    print("🔍 AutoGT AI Workflow Validation")
    print("=" * 50)
    
    # Check all expected files exist
    expected_files = [
        "analysis.json", "assets.json", "threats.json", 
        "attack_paths.json", "feasibility.json", "risks.json",
        "treatments.json", "cybersecurity_goals.json", "final_report.json"
    ]
    
    print("📁 File Structure Validation:")
    for file in expected_files:
        file_path = os.path.join(analysis_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} (missing)")
    
    # Load and validate key metrics
    print("\n📊 AI Analysis Metrics:")
    
    # Assets analysis
    with open(os.path.join(analysis_dir, "assets.json"), 'r') as f:
        assets = json.load(f)
    
    asset_confidence = sum(a.get('ai_confidence_score', 0) for a in assets) / len(assets)
    print(f"   🤖 Assets Identified: {len(assets)} (avg confidence: {asset_confidence:.3f})")
    
    # Threats analysis  
    with open(os.path.join(analysis_dir, "threats.json"), 'r') as f:
        threats = json.load(f)
    
    threat_confidence = sum(t.get('ai_discovery_confidence', 0) for t in threats) / len(threats)
    print(f"   🎯 Threats Discovered: {len(threats)} (avg confidence: {threat_confidence:.3f})")
    
    # Risk analysis
    with open(os.path.join(analysis_dir, "risks.json"), 'r') as f:
        risks = json.load(f)
    
    avg_risk_score = sum(r.get('calculated_risk_score', 0) for r in risks) / len(risks)
    print(f"   ⚠️  Risks Calculated: {len(risks)} (avg score: {avg_risk_score:.1f})")
    
    # Final report summary
    with open(os.path.join(analysis_dir, "final_report.json"), 'r') as f:
        report = json.load(f)
    
    print(f"\n📋 Analysis Summary:")
    print(f"   📊 Analysis ID: {report['analysis_summary']['analysis_id']}")
    print(f"   🤖 AI Enhanced: {report['analysis_summary']['ai_enhanced']}")
    print(f"   ✅ Steps Completed: {len(report['analysis_summary']['workflow_steps'])}")
    
    print(f"\n🎯 Key AI Findings:")
    for finding in report['key_findings']:
        print(f"   • {finding}")
        
    print(f"\n💡 AI Recommendations:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    
    print(f"\n✅ AI workflow validation completed successfully!")
    print(f"📁 Complete results: {analysis_dir}")

if __name__ == "__main__":
    validate_ai_workflow()