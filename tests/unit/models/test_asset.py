"""
Unit tests for Asset model validation per data-model.md validation rules.

This test validates all Asset model functionality including:
- Field validation and constraints
- Security property calculations
- Criticality level validation
- Interface relationship management
- Asset type specific validation rules

Test Coverage:
- Asset creation and validation
- Security property derivation
- Field constraint enforcement
- Type-specific validation rules
- Edge cases and error conditions
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from typing import List

from autogt.core.models.asset import Asset, AssetType, CriticalityLevel, SecurityProperty
from autogt.core.models.analysis import Analysis


class TestAssetModel:
    """Asset model validation unit tests."""
    
    def test_asset_creation_with_valid_data(self):
        """Test Asset creation with all valid data."""
        analysis = Analysis(
            id=uuid4(),
            name="Test Analysis",
            vehicle_model="Test Vehicle",
            current_step=1,
            created_at=datetime.utcnow()
        )
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN", "Ethernet"],
            description="Central communication hub",
            created_at=datetime.utcnow()
        )
        
        # Validate all fields are set correctly
        assert asset.name == "ECU Gateway"
        assert asset.asset_type == AssetType.HARDWARE
        assert asset.criticality_level == CriticalityLevel.HIGH
        assert "CAN" in asset.interfaces
        assert "Ethernet" in asset.interfaces
        assert asset.description == "Central communication hub"
        assert isinstance(asset.id, UUID)
        assert isinstance(asset.analysis_id, UUID)
        assert isinstance(asset.created_at, datetime)
    
    def test_asset_name_validation(self):
        """Test asset name validation rules per data-model.md."""
        analysis_id = uuid4()
        
        # Valid names
        valid_names = [
            "ECU Gateway",
            "Engine Control Module",
            "OBD-II Port",
            "Telematics Unit",
            "GPS Receiver",
            "WiFi Module"
        ]
        
        for name in valid_names:
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis_id,
                name=name,
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM
            )
            assert asset.name == name
        
        # Invalid names (should raise validation errors)
        invalid_names = [
            "",  # Empty string
            " ",  # Whitespace only
            "A" * 256,  # Too long (>255 chars)
            None  # None value
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises((ValueError, TypeError)):
                Asset(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    name=invalid_name,
                    asset_type=AssetType.HARDWARE,
                    criticality_level=CriticalityLevel.MEDIUM
                )
    
    def test_asset_type_validation(self):
        """Test AssetType enum validation."""
        analysis_id = uuid4()
        
        # Valid asset types
        valid_types = [AssetType.HARDWARE, AssetType.SOFTWARE]
        
        for asset_type in valid_types:
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis_id,
                name="Test Asset",
                asset_type=asset_type,
                criticality_level=CriticalityLevel.MEDIUM
            )
            assert asset.asset_type == asset_type
        
        # Invalid asset types
        invalid_types = ["INVALID", "hardware", "software", None, 123]
        
        for invalid_type in invalid_types:
            with pytest.raises((ValueError, TypeError)):
                Asset(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    name="Test Asset",
                    asset_type=invalid_type,
                    criticality_level=CriticalityLevel.MEDIUM
                )
    
    def test_criticality_level_validation(self):
        """Test CriticalityLevel enum validation per data-model.md."""
        analysis_id = uuid4()
        
        # Valid criticality levels
        valid_levels = [
            CriticalityLevel.LOW,
            CriticalityLevel.MEDIUM,
            CriticalityLevel.HIGH,
            CriticalityLevel.VERY_HIGH
        ]
        
        for level in valid_levels:
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis_id,
                name="Test Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=level
            )
            assert asset.criticality_level == level
        
        # Invalid criticality levels
        invalid_levels = ["INVALID", "low", "HIGH", None, 1]
        
        for invalid_level in invalid_levels:
            with pytest.raises((ValueError, TypeError)):
                Asset(
                    id=uuid4(),
                    analysis_id=analysis_id,
                    name="Test Asset",
                    asset_type=AssetType.HARDWARE,
                    criticality_level=invalid_level
                )
    
    def test_interfaces_validation(self):
        """Test interface list validation."""
        analysis_id = uuid4()
        
        # Valid interface configurations
        valid_interfaces = [
            ["CAN"],
            ["CAN", "Ethernet"],
            ["Bluetooth", "WiFi", "USB"],
            ["Cellular", "GPS"],
            []  # Empty list should be valid
        ]
        
        for interfaces in valid_interfaces:
            asset = Asset(
                id=uuid4(),
                analysis_id=analysis_id,
                name="Test Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM,
                interfaces=interfaces
            )
            assert asset.interfaces == interfaces
        
        # Test interface normalization
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Test Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            interfaces=["can", "ETHERNET"]  # Mixed case
        )
        
        # Should normalize to standard format
        normalized_interfaces = [iface.upper() for iface in asset.interfaces]
        assert "CAN" in normalized_interfaces
        assert "ETHERNET" in normalized_interfaces
    
    def test_security_properties_calculation(self):
        """Test security property derivation per data-model.md rules."""
        analysis_id = uuid4()
        
        # Test high criticality asset
        high_crit_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Engine Control Module",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.VERY_HIGH,
            interfaces=["CAN"]
        )
        
        # Calculate security properties
        security_props = high_crit_asset.calculate_security_properties()
        
        # High criticality should result in high security requirements
        assert security_props.confidentiality in [SecurityProperty.HIGH, SecurityProperty.VERY_HIGH]
        assert security_props.integrity in [SecurityProperty.HIGH, SecurityProperty.VERY_HIGH]
        assert security_props.availability in [SecurityProperty.HIGH, SecurityProperty.VERY_HIGH]
        
        # Test low criticality asset
        low_crit_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Diagnostic Port",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.LOW,
            interfaces=["OBD"]
        )
        
        security_props = low_crit_asset.calculate_security_properties()
        
        # Low criticality should result in lower security requirements
        assert security_props.confidentiality in [SecurityProperty.LOW, SecurityProperty.MEDIUM]
        assert security_props.integrity in [SecurityProperty.LOW, SecurityProperty.MEDIUM]
        assert security_props.availability in [SecurityProperty.LOW, SecurityProperty.MEDIUM]
    
    def test_hardware_specific_validation(self):
        """Test hardware-specific validation rules."""
        analysis_id = uuid4()
        
        # Hardware assets should support physical interfaces
        hardware_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN", "Ethernet", "USB"]
        )
        
        # Validate hardware-specific properties
        assert hardware_asset.supports_physical_interfaces()
        assert hardware_asset.requires_physical_security()
        
        # Test hardware interface validation
        valid_hw_interfaces = ["CAN", "Ethernet", "USB", "GPIO", "SPI", "I2C"]
        
        for interface in valid_hw_interfaces:
            assert hardware_asset.is_valid_interface(interface)
        
        # Software interfaces should not be valid for hardware
        invalid_hw_interfaces = ["REST_API", "GraphQL", "WebSocket"]
        
        for interface in invalid_hw_interfaces:
            assert not hardware_asset.is_valid_interface(interface)
    
    def test_software_specific_validation(self):
        """Test software-specific validation rules."""
        analysis_id = uuid4()
        
        # Software assets should support logical interfaces
        software_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Infotainment System",
            asset_type=AssetType.SOFTWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            interfaces=["Bluetooth", "WiFi", "USB"]
        )
        
        # Validate software-specific properties
        assert software_asset.supports_logical_interfaces()
        assert software_asset.requires_code_security()
        
        # Test software interface validation
        valid_sw_interfaces = ["Bluetooth", "WiFi", "USB", "REST_API", "TCP_IP"]
        
        for interface in valid_sw_interfaces:
            assert software_asset.is_valid_interface(interface)
    
    def test_asset_relationship_management(self):
        """Test asset relationship functionality."""
        analysis_id = uuid4()
        
        parent_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Vehicle Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN", "Ethernet"]
        )
        
        child_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Gateway ECU",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN"],
            parent_asset_id=parent_asset.id
        )
        
        # Test parent-child relationship
        assert child_asset.parent_asset_id == parent_asset.id
        assert child_asset.has_parent()
        assert not parent_asset.has_parent()
        
        # Test asset hierarchy validation
        assert parent_asset.can_have_children()
        assert child_asset.is_child_of(parent_asset.id)
    
    def test_asset_validation_constraints(self):
        """Test asset model validation constraints per data-model.md."""
        analysis_id = uuid4()
        
        # Test required field validation
        with pytest.raises(TypeError):
            Asset(
                # Missing required id
                analysis_id=analysis_id,
                name="Test Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM
            )
        
        with pytest.raises(TypeError):
            Asset(
                id=uuid4(),
                # Missing required analysis_id
                name="Test Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.MEDIUM
            )
        
        # Test name uniqueness within analysis (if enforced by model)
        asset1 = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Duplicate Name",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM
        )
        
        # Should be able to create asset with same name in different analysis
        asset2 = Asset(
            id=uuid4(),
            analysis_id=uuid4(),  # Different analysis
            name="Duplicate Name",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM
        )
        
        assert asset1.name == asset2.name
        assert asset1.analysis_id != asset2.analysis_id
    
    def test_asset_serialization(self):
        """Test asset model serialization and deserialization."""
        analysis_id = uuid4()
        
        original_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Test Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH,
            interfaces=["CAN", "Ethernet"],
            description="Test description",
            created_at=datetime.utcnow()
        )
        
        # Test JSON serialization
        asset_dict = original_asset.to_dict()
        
        # Validate serialized structure
        assert asset_dict['id'] == str(original_asset.id)
        assert asset_dict['analysis_id'] == str(original_asset.analysis_id)
        assert asset_dict['name'] == original_asset.name
        assert asset_dict['asset_type'] == original_asset.asset_type.value
        assert asset_dict['criticality_level'] == original_asset.criticality_level.value
        assert asset_dict['interfaces'] == original_asset.interfaces
        assert asset_dict['description'] == original_asset.description
        
        # Test deserialization
        reconstructed_asset = Asset.from_dict(asset_dict)
        
        assert reconstructed_asset.id == original_asset.id
        assert reconstructed_asset.analysis_id == original_asset.analysis_id
        assert reconstructed_asset.name == original_asset.name
        assert reconstructed_asset.asset_type == original_asset.asset_type
        assert reconstructed_asset.criticality_level == original_asset.criticality_level
        assert reconstructed_asset.interfaces == original_asset.interfaces
        assert reconstructed_asset.description == original_asset.description
    
    def test_asset_edge_cases(self):
        """Test asset model edge cases and boundary conditions."""
        analysis_id = uuid4()
        
        # Test maximum name length
        max_name = "A" * 255  # Maximum allowed length
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name=max_name,
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM
        )
        
        assert len(asset.name) == 255
        
        # Test Unicode characters in name
        unicode_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="ECU Gateway™ 测试",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM
        )
        
        assert "™" in unicode_asset.name
        assert "测试" in unicode_asset.name
        
        # Test very long interface list
        many_interfaces = [f"Interface_{i}" for i in range(20)]
        
        multi_interface_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="Multi Interface Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            interfaces=many_interfaces
        )
        
        assert len(multi_interface_asset.interfaces) == 20
        
        # Test empty description
        no_description_asset = Asset(
            id=uuid4(),
            analysis_id=analysis_id,
            name="No Description Asset",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.MEDIUM,
            description=""
        )
        
        assert no_description_asset.description == ""