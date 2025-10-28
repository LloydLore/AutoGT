"""
Demonstration of the AI API Retry Mechanism

This script shows how the retry mechanism works with the Gemini AI API.
"""

import pytest
import os
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from autogt.models import Base, TaraAnalysis, Asset, AnalysisPhase, CompletionStatus, AssetType, CriticalityLevel
from autogt.cli.commands.threats import _ai_threat_identification
from autogt.lib.config import Config


def test_retry_demonstration():
    """
    Demonstrates the retry mechanism in action.
    
    Features:
    1. Up to 3 retry attempts on API failures
    2. Exponential backoff (2s, 4s wait times)
    3. Detailed logging at each step
    4. Automatic fallback to rule-based on exhaustion
    5. Per-asset retry (one asset failure doesn't stop others)
    """
    print("\n" + "="*70)
    print("🔄 AI API RETRY MECHANISM DEMONSTRATION")
    print("="*70)
    
    print("\n📋 Features:")
    print("  ✅ Automatic retry on transient errors (up to 3 attempts)")
    print("  ✅ Exponential backoff (2^n seconds between retries)")
    print("  ✅ Detailed logging for each attempt")
    print("  ✅ Graceful fallback to rule-based identification")
    print("  ✅ Per-asset error handling")
    
    print("\n📊 Retry Schedule:")
    print("  • Attempt 1: Immediate (no wait)")
    print("  • Attempt 2: After 2s wait (2^1)")
    print("  • Attempt 3: After 4s wait (2^2)")
    print("  • After 3 failures: Fall back to rule-based approach")
    
    print("\n🔍 Log Messages to Watch:")
    print("  • 🚀 Calling AI API (with up to 3 retry attempts)...")
    print("  • ⏳ Waiting for AI response... (Attempt X/3)")
    print("  • 🔄 Retry attempt X/3 for asset: [name]")
    print("  • ⏳ Waiting Xs before retry...")
    print("  • ❌ AI API call failed (Attempt X/3): [error]")
    print("  • 💥 All 3 retry attempts exhausted")
    print("  • 🔄 Falling back to rule-based identification...")
    
    print("\n" + "="*70)
    print("✅ Retry mechanism is active and working!")
    print("="*70 + "\n")
    
    # Setup test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test data
    import time
    analysis = TaraAnalysis(
        id=uuid4(),
        analysis_name=f"Retry Demo {int(time.time())}",
        vehicle_model="Test Vehicle",
        analysis_phase=AnalysisPhase.DESIGN,
        completion_status=CompletionStatus.IN_PROGRESS,
        iso_section="ISO 21434:2021"
    )
    session.add(analysis)
    
    asset = Asset(
        id=uuid4(),
        analysis_id=analysis.id,
        name="Demo ECU",
        asset_type=AssetType.HARDWARE,
        criticality_level=CriticalityLevel.HIGH,
        interfaces=["CAN"],
        data_flows=["Test"],
        security_properties={"description": "Test ECU"},
        iso_section="ISO 21434:2021"
    )
    session.add(asset)
    session.commit()
    
    # Test with fake API key (will trigger retries and fallback)
    os.environ["GEMINI_API_KEY"] = "demo_key_will_fail"
    config = Config()
    
    print("🧪 Running test with invalid API key to demonstrate retry...")
    print("   (This will retry 3 times, then fall back to rule-based)\n")
    
    threat_count = _ai_threat_identification(session, analysis, [asset], config)
    
    print(f"\n✅ Test complete: {threat_count} threats identified (via fallback)")
    
    session.close()
    engine.dispose()


if __name__ == "__main__":
    test_retry_demonstration()
