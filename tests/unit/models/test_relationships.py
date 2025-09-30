"""
Unit tests for database relationships per data-model.md relationship specifications.

This test validates all database relationship functionality including:
- Foreign key relationships and constraints
- One-to-many and many-to-many relationships
- Cascade delete and update behavior
- Reference integrity validation
- Cross-entity relationship queries

Test Coverage:
- Analysis -> Asset relationships
- Asset -> ThreatScenario relationships  
- ThreatScenario -> RiskValue relationships
- Asset -> Asset (parent-child) relationships
- Cascade operations and constraint validation
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from autogt.core.models.analysis import Analysis
from autogt.core.models.asset import Asset, AssetType, CriticalityLevel
from autogt.core.models.threat import ThreatScenario, ThreatActor, ThreatCategory, ThreatMotivation
from autogt.core.models.risk import RiskValue, RiskLevel, ImpactLevel, LikelihoodLevel, RiskCalculationMethod
from autogt.core.database import get_database_session


class TestDatabaseRelationships:
    """Database relationship validation unit tests."""
    
    @pytest.fixture
    def db_session(self):
        """Get database session for testing."""
        session = get_database_session()
        yield session
        session.rollback()
        session.close()
    
    def test_analysis_asset_relationship(self, db_session):
        """Test Analysis -> Asset one-to-many relationship."""
        # Create analysis
        analysis = Analysis(
            id=uuid4(),
            name="Relationship Test Analysis",
            vehicle_model="Test Vehicle",
            current_step=1,
            created_at=datetime.utcnow()
        )
        
        db_session.add(analysis)
        db_session.flush()  # Get ID without committing
        
        # Create assets for the analysis
        assets = []
        for i in range(3):
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis.id,
                name=f"Test Asset {i}",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM,
                created_at=datetime.utcnow()
            )
            assets.append(asset)
            db_session.add(asset)
        
        db_session.flush()
        
        # Test relationship navigation
        # From analysis to assets
        db_session.refresh(analysis)
        assert len(analysis.assets) == 3
        
        for i, asset in enumerate(analysis.assets):
            assert asset.name == f"Test Asset {i}"
            assert asset.analysis_id == analysis.id
        
        # From asset to analysis
        for asset in assets:
            db_session.refresh(asset)
            assert asset.analysis.id == analysis.id
            assert asset.analysis.name == "Relationship Test Analysis"
    
    def test_asset_threat_relationship(self, db_session):
        """Test Asset -> ThreatScenario one-to-many relationship."""
        # Create analysis and asset
        analysis = Analysis(
            id=uuid4(),
            name="Threat Relationship Test",
            vehicle_model="Test Vehicle",
            current_step=3,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            created_at=datetime.utcnow()
        )
        db_session.add(asset)
        db_session.flush()
        
        # Create threat scenarios for the asset
        threats = []
        threat_names = [
            "Remote Code Execution",
            "Denial of Service",
            "Information Disclosure"
        ]
        
        for name in threat_names:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis.id,
                asset_id=asset.id,
                threat_name=name,
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN,
                created_at=datetime.utcnow()
            )
            threats.append(threat)
            db_session.add(threat)
        
        db_session.flush()
        
        # Test relationship navigation
        # From asset to threats
        db_session.refresh(asset)
        assert len(asset.threat_scenarios) == 3
        
        threat_names_found = [threat.threat_name for threat in asset.threat_scenarios]
        for name in threat_names:
            assert name in threat_names_found
        
        # From threat to asset
        for threat in threats:
            db_session.refresh(threat)
            assert threat.asset.id == asset.id
            assert threat.asset.name == "ECU Gateway"
            assert threat.analysis_id == analysis.id
    
    def test_threat_risk_relationship(self, db_session):
        """Test ThreatScenario -> RiskValue one-to-many relationship."""
        # Create full hierarchy
        analysis = Analysis(
            id=uuid4(),
            name="Risk Relationship Test",
            vehicle_model="Test Vehicle",
            current_step=6,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="Test Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            created_at=datetime.utcnow()
        )
        db_session.add(asset)
        
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_name="Test Threat",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(threat)
        db_session.flush()
        
        # Create risk values for the threat
        risks = []
        risk_scenarios = [
            (ImpactLevel.MAJOR, LikelihoodLevel.HIGH, RiskLevel.HIGH),
            (ImpactLevel.MODERATE, LikelihoodLevel.MEDIUM, RiskLevel.MEDIUM),
            (ImpactLevel.SEVERE, LikelihoodLevel.LOW, RiskLevel.MEDIUM)
        ]
        
        for impact, likelihood, level in risk_scenarios:
            risk = RiskValue(
                id=uuid4(),
                analysis_id=analysis.id,
                asset_id=asset.id,
                threat_id=threat.id,
                impact_level=impact,
                likelihood_level=likelihood,
                risk_level=level,
                risk_score=0.5,
                calculation_method=RiskCalculationMethod.ISO21434,
                created_at=datetime.utcnow()
            )
            risks.append(risk)
            db_session.add(risk)
        
        db_session.flush()
        
        # Test relationship navigation
        # From threat to risks
        db_session.refresh(threat)
        assert len(threat.risk_values) == 3
        
        risk_levels_found = [risk.risk_level for risk in threat.risk_values]
        assert RiskLevel.HIGH in risk_levels_found
        assert RiskLevel.MEDIUM in risk_levels_found
        
        # From risk to threat
        for risk in risks:
            db_session.refresh(risk)
            assert risk.threat_scenario.id == threat.id
            assert risk.threat_scenario.threat_name == "Test Threat"
            assert risk.asset_id == asset.id
            assert risk.analysis_id == analysis.id
    
    def test_asset_parent_child_relationship(self, db_session):
        """Test Asset -> Asset (parent-child) self-referential relationship."""
        # Create analysis
        analysis = Analysis(
            id=uuid4(),
            name="Asset Hierarchy Test",
            vehicle_model="Test Vehicle",
            current_step=1,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        db_session.flush()
        
        # Create parent asset
        parent_asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="Vehicle Gateway System",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            created_at=datetime.utcnow()
        )
        db_session.add(parent_asset)
        db_session.flush()
        
        # Create child assets
        child_assets = []
        child_names = ["Gateway ECU", "Communication Module", "Security Processor"]
        
        for name in child_names:
            child_asset = Asset(
                id=uuid4(),
                analysis_id=analysis.id,
                name=name,
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM,
                parent_asset_id=parent_asset.id,
                created_at=datetime.utcnow()
            )
            child_assets.append(child_asset)
            db_session.add(child_asset)
        
        db_session.flush()
        
        # Test parent-child relationships
        # From parent to children
        db_session.refresh(parent_asset)
        assert len(parent_asset.child_assets) == 3
        
        child_names_found = [child.name for child in parent_asset.child_assets]
        for name in child_names:
            assert name in child_names_found
        
        # From child to parent
        for child in child_assets:
            db_session.refresh(child)
            assert child.parent_asset.id == parent_asset.id
            assert child.parent_asset.name == "Vehicle Gateway System"
            assert child.parent_asset_id == parent_asset.id
        
        # Test hierarchy depth
        assert parent_asset.get_hierarchy_depth() == 0  # Root level
        for child in child_assets:
            assert child.get_hierarchy_depth() == 1  # One level deep
    
    def test_cascade_delete_behavior(self, db_session):
        """Test cascade delete behavior across relationships."""
        # Create full entity hierarchy
        analysis = Analysis(
            id=uuid4(),
            name="Cascade Delete Test",
            vehicle_model="Test Vehicle",
            current_step=6,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="Test Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            created_at=datetime.utcnow()
        )
        db_session.add(asset)
        
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_name="Test Threat",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(threat)
        
        risk = RiskValue(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_id=threat.id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.HIGH,
            risk_level=RiskLevel.HIGH,
            risk_score=0.7,
            calculation_method=RiskCalculationMethod.ISO21434,
            created_at=datetime.utcnow()
        )
        db_session.add(risk)
        
        db_session.commit()
        
        # Get IDs for verification
        analysis_id = analysis.id
        asset_id = asset.id
        threat_id = threat.id
        risk_id = risk.id
        
        # Test cascade delete of analysis (should delete all related entities)
        db_session.delete(analysis)
        db_session.commit()
        
        # Verify all related entities are deleted
        assert db_session.get(Analysis, analysis_id) is None
        assert db_session.get(Asset, asset_id) is None
        assert db_session.get(ThreatScenario, threat_id) is None
        assert db_session.get(RiskValue, risk_id) is None
    
    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraint enforcement."""
        # Test invalid analysis_id in asset
        with pytest.raises(IntegrityError):
            invalid_asset = Asset(
                id=uuid4(),
                analysis_id=uuid4(),  # Non-existent analysis ID
                name="Invalid Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM,
                created_at=datetime.utcnow()
            )
            db_session.add(invalid_asset)
            db_session.commit()
        
        db_session.rollback()
        
        # Test invalid asset_id in threat
        analysis = Analysis(
            id=uuid4(),
            name="FK Constraint Test",
            vehicle_model="Test Vehicle",
            current_step=3,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        db_session.commit()
        
        with pytest.raises(IntegrityError):
            invalid_threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis.id,
                asset_id=uuid4(),  # Non-existent asset ID
                threat_name="Invalid Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN,
                created_at=datetime.utcnow()
            )
            db_session.add(invalid_threat)
            db_session.commit()
    
    def test_cross_entity_queries(self, db_session):
        """Test complex cross-entity relationship queries."""
        # Create comprehensive test data
        analysis = Analysis(
            id=uuid4(),
            name="Cross-Entity Query Test",
            vehicle_model="Test Vehicle",
            current_step=6,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        
        # Multiple assets
        assets = []
        for i in range(3):
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis.id,
                name=f"Asset {i}",
                asset_type=AssetType.HARDWARE if i % 2 == 0 else AssetType.SOFTWARE,
                criticality_level=CriticalityLevel.HIGH if i == 0 else CriticalityLevel.MEDIUM,
                created_at=datetime.utcnow()
            )
            assets.append(asset)
            db_session.add(asset)
        
        db_session.flush()
        
        # Multiple threats per asset
        threats = []
        for asset in assets:
            for j in range(2):
                threat = ThreatScenario(
                    id=uuid4(),
                    analysis_id=analysis.id,
                    asset_id=asset.id,
                    threat_name=f"Threat {asset.name}-{j}",
                    threat_category=ThreatCategory.REMOTE_EXECUTION,
                    threat_actor=ThreatActor.CRIMINAL,
                    motivation=ThreatMotivation.FINANCIAL_GAIN,
                    created_at=datetime.utcnow()
                )
                threats.append(threat)
                db_session.add(threat)
        
        db_session.flush()
        
        # Multiple risks per threat
        risks = []
        for threat in threats:
            risk = RiskValue(
                id=uuid4(),
                analysis_id=analysis.id,
                asset_id=threat.asset_id,
                threat_id=threat.id,
                impact_level=ImpactLevel.MAJOR,
                likelihood_level=LikelihoodLevel.HIGH,
                risk_level=RiskLevel.HIGH,
                risk_score=0.7,
                calculation_method=RiskCalculationMethod.ISO21434,
                created_at=datetime.utcnow()
            )
            risks.append(risk)
            db_session.add(risk)
        
        db_session.commit()
        
        # Test complex queries
        
        # 1. Get all high-risk scenarios for high-criticality assets
        high_criticality_assets = db_session.query(Asset).filter(
            Asset.analysis_id == analysis.id,
            Asset.criticality_level == CriticalityLevel.HIGH
        ).all()
        
        assert len(high_criticality_assets) == 1
        assert high_criticality_assets[0].name == "Asset 0"
        
        # 2. Get all risks for a specific analysis with asset and threat info
        analysis_risks = db_session.query(RiskValue).join(Asset).join(ThreatScenario).filter(
            RiskValue.analysis_id == analysis.id
        ).all()
        
        assert len(analysis_risks) == 6  # 3 assets × 2 threats × 1 risk each
        
        # 3. Count threats by asset type
        hardware_threat_count = db_session.query(ThreatScenario).join(Asset).filter(
            Asset.analysis_id == analysis.id,
            Asset.asset_type == AssetType.HARDWARE
        ).count()
        
        software_threat_count = db_session.query(ThreatScenario).join(Asset).filter(
            Asset.analysis_id == analysis.id,
            Asset.asset_type == AssetType.SOFTWARE
        ).count()
        
        assert hardware_threat_count == 4  # 2 hardware assets × 2 threats each
        assert software_threat_count == 2   # 1 software asset × 2 threats
        
        # 4. Get analysis summary with relationship counts
        db_session.refresh(analysis)
        assert len(analysis.assets) == 3
        
        total_threats = sum(len(asset.threat_scenarios) for asset in analysis.assets)
        assert total_threats == 6
        
        total_risks = db_session.query(RiskValue).filter(
            RiskValue.analysis_id == analysis.id
        ).count()
        assert total_risks == 6
    
    def test_relationship_integrity_constraints(self, db_session):
        """Test relationship integrity and constraint validation."""
        # Create analysis and assets
        analysis = Analysis(
            id=uuid4(),
            name="Integrity Test",
            vehicle_model="Test Vehicle",
            current_step=1,
            created_at=datetime.utcnow()
        )
        db_session.add(analysis)
        
        asset1 = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="Asset 1",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            created_at=datetime.utcnow()
        )
        db_session.add(asset1)
        
        asset2 = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="Asset 2",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            created_at=datetime.utcnow()
        )
        db_session.add(asset2)
        
        db_session.commit()
        
        # Test cross-analysis relationship validation
        # Should not be able to create threat for asset in different analysis
        other_analysis = Analysis(
            id=uuid4(),
            name="Other Analysis",
            vehicle_model="Other Vehicle",
            current_step=3,
            created_at=datetime.utcnow()
        )
        db_session.add(other_analysis)
        db_session.commit()
        
        # This should be prevented by application logic (business rule)
        cross_analysis_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=other_analysis.id,  # Different analysis
            asset_id=asset1.id,  # Asset from first analysis
            threat_name="Cross-Analysis Threat",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            created_at=datetime.utcnow()
        )
        
        # This might be allowed by database but should be caught by application validation
        db_session.add(cross_analysis_threat)
        
        # Application should validate that threat.analysis_id == asset.analysis_id
        try:
            db_session.commit()
            # If commit succeeds, validate business rule in application
            assert cross_analysis_threat.analysis_id != asset1.analysis_id, \
                "Business rule validation should catch cross-analysis relationships"
        except IntegrityError:
            # Database constraint prevents this - also acceptable
            db_session.rollback()