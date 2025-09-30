"""
Unit tests for ThreatScenario model per data-model.md threat specifications.

This test validates all ThreatScenario model functionality including:
- Threat identification and categorization
- Threat actor and motivation validation
- Attack vector specification and validation
- Threat-asset relationship management
- ISO/SAE 21434 threat classification compliance

Test Coverage:
- ThreatScenario creation and validation
- Threat actor type validation
- Attack vector specification
- Threat categorization per ISO/SAE 21434
- Relationship to assets and analyses
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from typing import List

from autogt.core.models.threat import (
    ThreatScenario, ThreatActor, ThreatCategory, AttackVector,
    ThreatMotivation, ThreatCapability
)
from autogt.core.models.asset import Asset, AssetType, CriticalityLevel
from autogt.core.models.analysis import Analysis


class TestThreatScenarioModel:
    """ThreatScenario model validation unit tests."""
    
    def test_threat_scenario_creation_with_valid_data(self):
        """Test ThreatScenario creation with all valid data."""
        analysis = Analysis(
            id=uuid4(),
            name="Test Analysis",
            vehicle_model="Test Vehicle",
            current_step=3,
            created_at=datetime.utcnow()
        )
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH
        )
        
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_name="Remote Code Execution via CAN Bus",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=["CAN message injection", "ECU firmware exploitation"],
            prerequisites=["Physical access to CAN bus", "Knowledge of CAN protocols"],
            description="Attacker exploits CAN bus vulnerabilities to execute arbitrary code",
            created_at=datetime.utcnow()
        )
        
        # Validate all fields are set correctly
        assert threat.threat_name == "Remote Code Execution via CAN Bus"
        assert threat.threat_category == ThreatCategory.REMOTE_EXECUTION
        assert threat.threat_actor == ThreatActor.CRIMINAL
        assert threat.motivation == ThreatMotivation.FINANCIAL_GAIN
        assert "CAN message injection" in threat.attack_vectors
        assert "Physical access to CAN bus" in threat.prerequisites
        assert isinstance(threat.id, UUID)
        assert isinstance(threat.analysis_id, UUID)
        assert isinstance(threat.asset_id, UUID)
        assert isinstance(threat.created_at, datetime)
    
    def test_threat_name_validation(self):
        """Test threat name validation rules."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid threat names
        valid_names = [
            "Remote Code Execution",
            "Denial of Service Attack",
            "Man-in-the-Middle Interception",
            "Supply Chain Compromise",
            "Physical Tampering",
            "Eavesdropping on Communications"
        ]
        
        for name in valid_names:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name=name,
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN
            )
            assert threat.threat_name == name
        
        # Invalid threat names
        invalid_names = [
            "",  # Empty string
            " ",  # Whitespace only
            "A" * 513,  # Too long (>512 chars)
            None  # None value
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises((ValueError, TypeError)):
                ThreatScenario(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    asset_id=asset_id,
                    threat_name=invalid_name,
                    threat_category=ThreatCategory.REMOTE_EXECUTION,
                    threat_actor=ThreatActor.CRIMINAL,
                    motivation=ThreatMotivation.FINANCIAL_GAIN
                )
    
    def test_threat_actor_validation(self):
        """Test ThreatActor enum validation per ISO/SAE 21434."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid threat actors per ISO/SAE 21434
        valid_actors = [
            ThreatActor.CRIMINAL,
            ThreatActor.NATION_STATE,
            ThreatActor.INSIDER,
            ThreatActor.HACKTIVIST,
            ThreatActor.TERRORIST,
            ThreatActor.RESEARCHER,
            ThreatActor.SCRIPT_KIDDIE
        ]
        
        for actor in valid_actors:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=actor,
                motivation=ThreatMotivation.FINANCIAL_GAIN
            )
            assert threat.threat_actor == actor
        
        # Invalid threat actors
        invalid_actors = ["INVALID", "criminal", None, 123]
        
        for invalid_actor in invalid_actors:
            with pytest.raises((ValueError, TypeError)):
                ThreatScenario(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    asset_id=asset_id,
                    threat_name="Test Threat",
                    threat_category=ThreatCategory.REMOTE_EXECUTION,
                    threat_actor=invalid_actor,
                    motivation=ThreatMotivation.FINANCIAL_GAIN
                )
    
    def test_threat_category_validation(self):
        """Test ThreatCategory enum validation per data-model.md."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid threat categories
        valid_categories = [
            ThreatCategory.REMOTE_EXECUTION,
            ThreatCategory.DENIAL_OF_SERVICE,
            ThreatCategory.INFORMATION_DISCLOSURE,
            ThreatCategory.ELEVATION_OF_PRIVILEGE,
            ThreatCategory.TAMPERING,
            ThreatCategory.SPOOFING,
            ThreatCategory.REPUDIATION
        ]
        
        for category in valid_categories:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=category,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN
            )
            assert threat.threat_category == category
        
        # Test STRIDE mapping
        stride_mapping = {
            ThreatCategory.SPOOFING: "S",
            ThreatCategory.TAMPERING: "T", 
            ThreatCategory.REPUDIATION: "R",
            ThreatCategory.INFORMATION_DISCLOSURE: "I",
            ThreatCategory.DENIAL_OF_SERVICE: "D",
            ThreatCategory.ELEVATION_OF_PRIVILEGE: "E"
        }
        
        for category, stride_letter in stride_mapping.items():
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="STRIDE Test",
                threat_category=category,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN
            )
            
            assert threat.get_stride_category() == stride_letter
    
    def test_threat_motivation_validation(self):
        """Test ThreatMotivation enum validation."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid motivations
        valid_motivations = [
            ThreatMotivation.FINANCIAL_GAIN,
            ThreatMotivation.ESPIONAGE,
            ThreatMotivation.SABOTAGE,
            ThreatMotivation.ACTIVISM,
            ThreatMotivation.REVENGE,
            ThreatMotivation.CURIOSITY,
            ThreatMotivation.REPUTATION
        ]
        
        for motivation in valid_motivations:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=motivation
            )
            assert threat.motivation == motivation
    
    def test_attack_vectors_validation(self):
        """Test attack vector specification and validation."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid attack vector configurations
        valid_attack_vectors = [
            ["Network intrusion"],
            ["Physical access", "Social engineering"],
            ["Malware installation", "Privilege escalation", "Data exfiltration"],
            []  # Empty list should be valid
        ]
        
        for vectors in valid_attack_vectors:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN,
                attack_vectors=vectors
            )
            assert threat.attack_vectors == vectors
        
        # Test attack vector categorization
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Multi-vector Attack",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=[
                "Network scanning",  # Remote
                "Physical device tampering",  # Physical  
                "Social engineering",  # Human
                "Malware installation"  # Software
            ]
        )
        
        # Test vector categorization
        assert threat.has_remote_attack_vectors()
        assert threat.has_physical_attack_vectors()
        assert threat.has_social_attack_vectors()
        assert threat.has_software_attack_vectors()
    
    def test_prerequisites_validation(self):
        """Test threat prerequisite specification."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Valid prerequisite configurations
        valid_prerequisites = [
            ["Network access"],
            ["Physical access", "Specialized tools"],
            ["Insider knowledge", "System credentials", "Technical expertise"],
            []  # No prerequisites
        ]
        
        for prereqs in valid_prerequisites:
            threat = ThreatScenario(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=ThreatActor.CRIMINAL,
                motivation=ThreatMotivation.FINANCIAL_GAIN,
                prerequisites=prereqs
            )
            assert threat.prerequisites == prereqs
        
        # Test prerequisite complexity assessment
        complex_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Complex Attack",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.NATION_STATE,
            motivation=ThreatMotivation.ESPIONAGE,
            prerequisites=[
                "Advanced persistent threat capabilities",
                "Zero-day exploits",
                "Nation-state resources",
                "Multi-year campaign planning"
            ]
        )
        
        # Complex threats should have high prerequisite requirements
        assert complex_threat.get_prerequisite_complexity() == "HIGH"
        
        simple_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Simple Attack",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.SCRIPT_KIDDIE,
            motivation=ThreatMotivation.CURIOSITY,
            prerequisites=["Basic technical knowledge"]
        )
        
        assert simple_threat.get_prerequisite_complexity() == "LOW"
    
    def test_threat_asset_relationship(self):
        """Test threat-asset relationship management."""
        analysis_id = uuid4()
        
        # Create assets
        ecu_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN", "Ethernet"]
        )
        
        infotainment_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Infotainment System",
            asset_type=AssetType.SOFTWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            interfaces=["Bluetooth", "WiFi"]
        )
        
        # Create threat targeting ECU
        ecu_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=ecu_asset.id,
            threat_name="CAN Bus Injection",
            threat_category=ThreatCategory.TAMPERING,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=["CAN frame injection"]
        )
        
        # Test asset relationship
        assert ecu_threat.asset_id == ecu_asset.id
        assert ecu_threat.targets_asset(ecu_asset.id)
        assert not ecu_threat.targets_asset(infotainment_asset.id)
        
        # Test threat applicability to asset types
        assert ecu_threat.is_applicable_to_hardware()
        
        infotainment_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=infotainment_asset.id,
            threat_name="Malware Installation",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=["USB malware", "WiFi exploitation"]
        )
        
        assert infotainment_threat.is_applicable_to_software()
    
    def test_threat_capability_requirements(self):
        """Test threat capability requirement assessment."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # High capability threat (Nation State)
        advanced_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Advanced Persistent Threat",
            threat_category=ThreatCategory.INFORMATION_DISCLOSURE,
            threat_actor=ThreatActor.NATION_STATE,
            motivation=ThreatMotivation.ESPIONAGE,
            attack_vectors=["Zero-day exploits", "Supply chain compromise"],
            prerequisites=["Nation-state resources", "Advanced technical capabilities"]
        )
        
        capabilities = advanced_threat.get_required_capabilities()
        
        assert ThreatCapability.ADVANCED_TECHNICAL in capabilities
        assert ThreatCapability.SIGNIFICANT_RESOURCES in capabilities
        assert ThreatCapability.LONG_TERM_PLANNING in capabilities
        
        # Low capability threat (Script Kiddie)
        simple_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Script-based Attack",
            threat_category=ThreatCategory.DENIAL_OF_SERVICE,
            threat_actor=ThreatActor.SCRIPT_KIDDIE,
            motivation=ThreatMotivation.CURIOSITY,
            attack_vectors=["Publicly available tools"],
            prerequisites=["Basic computer knowledge"]
        )
        
        capabilities = simple_threat.get_required_capabilities()
        
        assert ThreatCapability.BASIC_TECHNICAL in capabilities
        assert ThreatCapability.MINIMAL_RESOURCES in capabilities
    
    def test_threat_severity_assessment(self):
        """Test threat severity assessment based on various factors."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # High severity threat
        high_severity_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Critical System Compromise",
            threat_category=ThreatCategory.ELEVATION_OF_PRIVILEGE,
            threat_actor=ThreatActor.NATION_STATE,
            motivation=ThreatMotivation.SABOTAGE,
            attack_vectors=["Supply chain compromise", "Firmware modification"],
            prerequisites=["Advanced capabilities"],
            impact_description="Complete vehicle control compromise"
        )
        
        assert high_severity_threat.calculate_base_severity() >= 0.8
        
        # Low severity threat
        low_severity_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Information Disclosure",
            threat_category=ThreatCategory.INFORMATION_DISCLOSURE,
            threat_actor=ThreatActor.SCRIPT_KIDDIE,
            motivation=ThreatMotivation.CURIOSITY,
            attack_vectors=["Network sniffing"],
            prerequisites=["Basic networking knowledge"],
            impact_description="Minor data exposure"
        )
        
        assert low_severity_threat.calculate_base_severity() <= 0.4
    
    def test_threat_serialization(self):
        """Test threat model serialization and deserialization."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        original_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Remote Code Execution",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=["Buffer overflow", "Code injection"],
            prerequisites=["Network access", "Vulnerability knowledge"],
            description="Attacker executes arbitrary code remotely",
            created_at=datetime.utcnow()
        )
        
        # Test JSON serialization
        threat_dict = original_threat.to_dict()
        
        # Validate serialized structure
        assert threat_dict['id'] == str(original_threat.id)
        assert threat_dict['analysis_id'] == str(original_threat.analysis_id)
        assert threat_dict['asset_id'] == str(original_threat.asset_id)
        assert threat_dict['threat_name'] == original_threat.threat_name
        assert threat_dict['threat_category'] == original_threat.threat_category.value
        assert threat_dict['threat_actor'] == original_threat.threat_actor.value
        assert threat_dict['motivation'] == original_threat.motivation.value
        assert threat_dict['attack_vectors'] == original_threat.attack_vectors
        assert threat_dict['prerequisites'] == original_threat.prerequisites
        
        # Test deserialization
        reconstructed_threat = ThreatScenario.from_dict(threat_dict)
        
        assert reconstructed_threat.id == original_threat.id
        assert reconstructed_threat.analysis_id == original_threat.analysis_id
        assert reconstructed_threat.asset_id == original_threat.asset_id
        assert reconstructed_threat.threat_name == original_threat.threat_name
        assert reconstructed_threat.threat_category == original_threat.threat_category
        assert reconstructed_threat.threat_actor == original_threat.threat_actor
        assert reconstructed_threat.motivation == original_threat.motivation
        assert reconstructed_threat.attack_vectors == original_threat.attack_vectors
        assert reconstructed_threat.prerequisites == original_threat.prerequisites
    
    def test_automotive_specific_threats(self):
        """Test automotive-specific threat scenarios."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # CAN Bus specific threat
        can_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="CAN Bus Message Injection",
            threat_category=ThreatCategory.TAMPERING,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=["CAN frame crafting", "Bus access via OBD port"],
            prerequisites=["Physical vehicle access", "CAN protocol knowledge"],
            automotive_specific=True,
            iso21434_category="Network Attack"
        )
        
        assert can_threat.is_automotive_specific()
        assert can_threat.get_iso21434_category() == "Network Attack"
        assert can_threat.affects_vehicle_safety()
        
        # V2X communication threat
        v2x_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="V2X Message Spoofing",
            threat_category=ThreatCategory.SPOOFING,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.SABOTAGE,
            attack_vectors=["False V2X beacon transmission", "Message replay attack"],
            prerequisites=["V2X communication equipment", "Protocol knowledge"],
            automotive_specific=True,
            iso21434_category="Communication Attack"
        )
        
        assert v2x_threat.is_automotive_specific()
        assert v2x_threat.affects_traffic_infrastructure()
    
    def test_threat_validation_edge_cases(self):
        """Test threat model edge cases and boundary conditions."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Test maximum field lengths
        max_name = "A" * 512  # Maximum threat name length
        
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name=max_name,
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN
        )
        
        assert len(threat.threat_name) == 512
        
        # Test very long attack vector list
        many_vectors = [f"Attack vector {i}" for i in range(50)]
        
        multi_vector_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Multi-vector Threat",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN,
            attack_vectors=many_vectors
        )
        
        assert len(multi_vector_threat.attack_vectors) == 50
        
        # Test Unicode characters
        unicode_threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_name="Unicode Threat™ 测试威胁",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN
        )
        
        assert "™" in unicode_threat.threat_name
        assert "测试威胁" in unicode_threat.threat_name