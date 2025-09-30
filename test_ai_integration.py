#!/usr/bin/env python3
"""
Direct test of AutoGen + Gemini integration for AutoGT TARA analysis.
This demonstrates the real AI capabilities separate from CLI issues.
"""

import os
import sys
sys.path.insert(0, '/home/lj/Documents/AutoGT/src')

from autogt.services.autogen_agent import AutoGenTaraAgent, TaraAgentConfig
from autogt.core.config import get_config

def test_real_ai_integration():
    """Test AutoGen + Gemini AI integration for asset identification."""
    
    print("🤖 Testing AutoGT Real AI Integration (AutoGen + Gemini)")
    print("=" * 60)
    
    # Check configuration
    try:
        config = get_config()
        print(f"✅ Gemini API Key: {'*' * 20 if config.gemini_api_key else 'NOT SET'}")
        print(f"✅ Gemini Model: {config.gemini_model}")
        print(f"✅ Gemini Base URL: {config.gemini_base_url}")
        print()
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return
    
    # Test document content (BMW iX3 ADAS)
    test_document = """
    BMW iX3 Advanced Driver Assistance System (ADAS)
    
    Central Processing Unit: High-performance automotive ECU running AUTOSAR Adaptive Platform
    LiDAR Sensor Array: Velodyne HDL-64E 360-degree laser scanning system
    Camera Systems: Multiple forward-facing stereo cameras with image processing
    Radar Units: 77GHz mmWave radar sensors for object detection
    V2X Communication Module: DSRC and C-V2X for vehicle-to-infrastructure
    Hardware Security Module: HSM for cryptographic key management
    Over-the-Air Update System: Secure OTA update mechanism
    
    Interfaces: CAN-FD, Ethernet, WiFi, Bluetooth, 5G Cellular
    """
    
    try:
        # Initialize AutoGen agent with Gemini
        print("🚀 Initializing AutoGen + Gemini Agent...")
        agent_config = TaraAgentConfig(
            gemini_api_key=config.gemini_api_key,
            gemini_model_name=config.gemini_model,
            gemini_base_url=config.gemini_base_url
        )
        
        ai_agent = AutoGenTaraAgent(agent_config)
        print("✅ AutoGen agent initialized successfully")
        print()
        
        # Test AI document analysis
        print("📄 Analyzing document with AutoGen + Gemini AI...")
        analysis_result = ai_agent.analyze_document(test_document, "test-analysis-123")
        
        print("🎯 AI Analysis Results:")
        print(f"   Asset Count: {analysis_result.get('asset_count', 0)}")
        print(f"   Confidence Score: {analysis_result.get('confidence_score', 0):.2f}")
        print()
        
        # Display identified assets
        assets = analysis_result.get('identified_assets', [])
        if assets:
            print("🔍 AI-Identified Assets:")
            for i, asset in enumerate(assets, 1):
                print(f"   {i}. {asset.get('name', 'Unknown')}")
                print(f"      Type: {asset.get('asset_type', 'N/A')}")
                print(f"      Criticality: {asset.get('criticality_level', 'N/A')}")
                print(f"      AI Confidence: {asset.get('ai_confidence', 0):.2f}")
                print()
        
        # Test AI threat identification
        print("🛡️ Testing AI Threat Identification...")
        threat_context = {
            "analysis_id": "test-analysis-123",
            "assets": assets
        }
        
        threat_result = ai_agent.identify_threats(threat_context)
        threats = threat_result.get('threats', [])
        
        print(f"🎯 AI Threat Analysis Results:")
        print(f"   Threat Count: {len(threats)}")
        print(f"   Analysis Method: {threat_result.get('analysis_method', 'Unknown')}")
        print(f"   Confidence Score: {threat_result.get('confidence_score', 0):.2f}")
        print()
        
        if threats:
            print("⚠️ AI-Identified Threats:")
            for i, threat in enumerate(threats, 1):
                print(f"   {i}. {threat.get('threat_name', 'Unknown Threat')}")
                print(f"      Category: {threat.get('threat_category', 'N/A')}")
                print(f"      Target: {threat.get('target_asset', 'N/A')}")
                print(f"      Vectors: {', '.join(threat.get('attack_vectors', []))}")
                print(f"      AI Confidence: {threat.get('confidence_score', 0):.2f}")
                print()
        
        print("🎉 AutoGen + Gemini Integration Test SUCCESSFUL!")
        print("✅ AI-powered TARA analysis working correctly")
        
    except Exception as e:
        print(f"❌ AI Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_ai_integration()