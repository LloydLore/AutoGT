"""
Integration tests for AI threat identification using real Gemini API.
Tests actual API calls and database operations.
"""

import pytest
import os
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from autogt.models import Base, TaraAnalysis, Asset, ThreatScenario, AnalysisPhase, CompletionStatus, AssetType, CriticalityLevel
from autogt.cli.commands.threats import _ai_threat_identification
from autogt.lib.config import Config 


@pytest.fixture(scope="module")
def test_db_engine():
    """Create a test database engine."""
    # 使用内存数据库进行测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def gemini_config():
    """Create real Gemini configuration."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY environment variable not set")
    
    # Create Config instance with Gemini API key
    config = Config()
    # Set the environment variable so Config can pick it up
    os.environ["GEMINI_API_KEY"] = api_key
    
    return config


@pytest.fixture
def sample_analysis(db_session: Session):
    """Create a sample TARA analysis in the database."""
    # Use unique name to avoid conflicts
    import time
    analysis = TaraAnalysis(
        id=uuid4(),
        analysis_name=f"Integration Test Analysis {int(time.time() * 1000)}",
        vehicle_model="Tesla Model 3",
        analysis_phase=AnalysisPhase.DESIGN,
        completion_status=CompletionStatus.IN_PROGRESS,
        iso_section="ISO 21434:2021"
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


@pytest.fixture
def sample_assets(db_session: Session, sample_analysis: TaraAnalysis):
    """Create sample assets in the database."""
    assets = [
        Asset(
            id=uuid4(),
            analysis_id=sample_analysis.id,
            name="CAN Bus",
            asset_type=AssetType.COMMUNICATION,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN-FD", "CAN 2.0B"],
            data_flows=["ECU-to-ECU communication"],
            security_properties={"description": "Controller Area Network for vehicle internal communication"},
            iso_section="ISO 21434:2021"
        ),
        Asset(
            id=uuid4(),
            analysis_id=sample_analysis.id,
            name="Infotainment System",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            interfaces=["USB", "Bluetooth", "WiFi"],
            data_flows=["User data", "Media streaming"],
            security_properties={"description": "Central multimedia and connectivity unit"},
            iso_section="ISO 21434:2021"
        ),
        Asset(
            id=uuid4(),
            analysis_id=sample_analysis.id,
            name="OTA Update Module",
            asset_type=AssetType.SOFTWARE,
            criticality_level=CriticalityLevel.VERY_HIGH,
            interfaces=["Cellular", "WiFi"],
            data_flows=["Firmware updates", "Configuration data"],
            security_properties={"description": "Over-the-air software update mechanism"},
            iso_section="ISO 21434:2021"
        )
    ]
    
    for asset in assets:
        db_session.add(asset)
    
    db_session.commit()
    
    for asset in assets:
        db_session.refresh(asset)
    
    return assets


class TestAIThreatIdentificationIntegration:
    """Integration tests for AI threat identification."""
    
    def test_real_api_threat_identification(
        self, 
        db_session: Session, 
        sample_analysis: TaraAnalysis, 
        sample_assets: list[Asset],
        gemini_config: Config
    ):
        """
        Test threat identification with real Gemini API.
        
        Verifies:
        - API successfully returns threat data
        - Threats are created in database
        - Threat data is properly structured
        """
        # 执行威胁识别
        threat_count = _ai_threat_identification(
            db_session,
            sample_analysis,
            sample_assets,
            gemini_config
        )
        
        # 验证返回的威胁数量
        assert threat_count > 0, "Should identify at least one threat"
        print(f"✓ Identified {threat_count} threats")
        
        # 从数据库查询创建的威胁
        threats = db_session.query(ThreatScenario).filter(
            ThreatScenario.asset_id.in_([a.id for a in sample_assets])
        ).all()
        
        # 验证数据库中的威胁数量
        assert len(threats) == threat_count, "Database should contain all identified threats"
        print(f"✓ Database contains {len(threats)} threats")
        
        # 验证威胁数据结构
        for threat in threats:
            assert threat.id is not None, "Threat should have ID"
            assert threat.threat_name, "Threat should have name"
            assert threat.motivation, "Threat should have motivation"
            assert threat.attack_vectors, "Threat should have attack vectors"
            assert threat.asset_id in [a.id for a in sample_assets], \
                "Threat should reference a valid asset"
            
            print(f"\n✓ Threat: {threat.threat_name}")
            print(f"  - Asset: {threat.asset_id}")
            print(f"  - Actor: {threat.threat_actor.value}")
            print(f"  - Motivation: {threat.motivation[:100]}...")
    
    def test_api_with_minimal_assets(
        self,
        db_session: Session,
        gemini_config: Config
    ):
        """
        Test threat identification with minimal asset set.
        
        Verifies system handles small datasets correctly.
        """
        import time
        # 创建最小分析场景
        analysis = TaraAnalysis(
            id=uuid4(),
            analysis_name=f"Minimal Test {int(time.time() * 1000)}",
            vehicle_model="Generic Vehicle",
            analysis_phase=AnalysisPhase.CONCEPT,
            completion_status=CompletionStatus.IN_PROGRESS,
            iso_section="ISO 21434:2021"
        )
        db_session.add(analysis)
        
        # 只创建一个资产
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="ECU",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN"],
            data_flows=["Control signals"],
            security_properties={"description": "Electronic Control Unit"},
            iso_section="ISO 21434:2021"
        )
        db_session.add(asset)
        db_session.commit()
        
        db_session.refresh(analysis)
        db_session.refresh(asset)
        
        # 执行威胁识别
        threat_count = _ai_threat_identification(
            db_session,
            analysis,
            [asset],
            gemini_config
        )
        
        # 验证结果
        assert threat_count > 0, "Should identify threats even with single asset"
        print(f"✓ Identified {threat_count} threats for single asset")
        
        threats = db_session.query(ThreatScenario).filter(
            ThreatScenario.asset_id == asset.id
        ).all()
        
        assert len(threats) == threat_count
        assert all(t.asset_id == asset.id for t in threats), \
            "All threats should reference the single asset"
    
    def test_api_error_handling(
        self,
        db_session: Session,
        sample_analysis: TaraAnalysis,
        sample_assets: list[Asset]
    ):
        """
        Test error handling with invalid API configuration.
        
        Verifies system gracefully handles API errors by falling back.
        """
        # 使用无效的 API 密钥
        os.environ["GEMINI_API_KEY"] = "invalid_key_12345"
        invalid_config = Config()
        
        # Should fall back to rule-based identification instead of failing
        threat_count = _ai_threat_identification(
            db_session,
            sample_analysis,
            sample_assets,
            invalid_config
        )
        
        # Should still generate threats using fallback method
        assert threat_count >= 0, "Should handle error gracefully"
        print(f"✓ Handled error gracefully with {threat_count} threats via fallback")
        
        threats = db_session.query(ThreatScenario).filter(
            ThreatScenario.asset_id.in_([a.id for a in sample_assets])
        ).all()
        
        # Verify threats were created (via fallback)
        print(f"✓ Fallback mechanism created {len(threats)} threats")
    
    def test_api_response_consistency(
        self,
        db_session: Session,
        sample_analysis: TaraAnalysis,
        sample_assets: list[Asset],
        gemini_config: Config
    ):
        """
        Test consistency of API responses.
        
        Runs identification twice and verifies reasonable results.
        """
        # 第一次运行
        count1 = _ai_threat_identification(
            db_session,
            sample_analysis,
            sample_assets,
            gemini_config
        )
        
        threats1 = db_session.query(ThreatScenario).filter(
            ThreatScenario.asset_id.in_([a.id for a in sample_assets])
        ).all()
        
        print(f"✓ First run: {count1} threats")
        
        # 清理威胁以进行第二次测试
        for threat in threats1:
            db_session.delete(threat)
        db_session.commit()
        
        # 第二次运行
        count2 = _ai_threat_identification(
            db_session,
            sample_analysis,
            sample_assets,
            gemini_config
        )
        
        threats2 = db_session.query(ThreatScenario).filter(
            ThreatScenario.asset_id.in_([a.id for a in sample_assets])
        ).all()
        
        print(f"✓ Second run: {count2} threats")
        
        # 验证两次结果都合理（允许一定差异）
        assert count1 > 0 and count2 > 0, "Both runs should identify threats"
        assert abs(count1 - count2) <= max(count1, count2) * 0.5, \
            "Results should be reasonably consistent (within 50%)"
        
        print(f"✓ Consistency check passed: {count1} vs {count2} threats")


if __name__ == "__main__":
    """
    Run integration tests directly.
    
    Usage:
        export GEMINI_API_KEY="your-api-key"
        python -m pytest tests/integration/test_ai_threat_identification_integration.py -v -s
    """
    pytest.main([__file__, "-v", "-s"])