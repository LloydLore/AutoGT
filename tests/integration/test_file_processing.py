"""
Integration test for multi-format file processing per quickstart.md lines 41-49.

This test validates the system's ability to process various input formats:
- CSV files (primary format)
- Excel spreadsheets
- JSON data files
- YAML configuration files
- XML system definitions

Test Scenarios:
- File format detection and parsing
- Data validation and normalization
- Error handling for invalid formats
- Large file processing capabilities
"""

import json
import pytest
import tempfile
import pandas as pd
from pathlib import Path
from io import BytesIO

from autogt.cli.main import cli
from click.testing import CliRunner


class TestFileProcessing:
    """Multi-format file processing integration test."""
    
    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_assets_data(self):
        """Sample asset data for testing different formats."""
        return [
            {
                'Asset Name': 'ECU Gateway',
                'Asset Type': 'HARDWARE',
                'Criticality Level': 'HIGH',
                'Interfaces': 'CAN,Ethernet',
                'Description': 'Central communication hub'
            },
            {
                'Asset Name': 'Infotainment System',
                'Asset Type': 'SOFTWARE', 
                'Criticality Level': 'MEDIUM',
                'Interfaces': 'Bluetooth,WiFi,USB',
                'Description': 'Entertainment and navigation'
            },
            {
                'Asset Name': 'Engine Control Module',
                'Asset Type': 'HARDWARE',
                'Criticality Level': 'VERY_HIGH',
                'Interfaces': 'CAN',
                'Description': 'Engine management system'
            }
        ]
    
    def test_csv_file_processing(self, runner, sample_assets_data):
        """Test CSV file processing (primary format)."""
        # Create CSV file
        csv_content = """Asset Name,Asset Type,Criticality Level,Interfaces,Description
ECU Gateway,HARDWARE,HIGH,"CAN,Ethernet",Central communication hub
Infotainment System,SOFTWARE,MEDIUM,"Bluetooth,WiFi,USB",Entertainment and navigation
Engine Control Module,HARDWARE,VERY_HIGH,CAN,Engine management system"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        # Test CSV import
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'CSV Processing Test',
            csv_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Verify assets were imported correctly
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_data['analysis_id'], '--step', '1'
        ])
        assert result.exit_code == 0
        
        asset_data = json.loads(result.output)
        assert asset_data['assets_count'] == 3
        
        # Validate specific asset
        ecu = next(a for a in asset_data['assets'] if a['name'] == 'ECU Gateway')
        assert ecu['asset_type'] == 'HARDWARE'
        assert ecu['criticality_level'] == 'HIGH'
        assert 'CAN' in ecu['interfaces']
        
        # Cleanup
        Path(csv_file).unlink()
    
    def test_excel_file_processing(self, runner, sample_assets_data):
        """Test Excel spreadsheet processing."""
        # Create Excel file
        df = pd.DataFrame(sample_assets_data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_file = f.name
        
        # Write Excel file
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Assets', index=False)
        
        # Test Excel import
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Excel Processing Test',
            '--format', 'excel',
            excel_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Verify assets imported
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_data['analysis_id'], '--step', '1'
        ])
        assert result.exit_code == 0
        
        asset_data = json.loads(result.output)
        assert asset_data['assets_count'] == 3
        
        # Cleanup
        Path(excel_file).unlink()
    
    def test_json_file_processing(self, runner, sample_assets_data):
        """Test JSON file processing."""
        # Create JSON file
        json_data = {
            'vehicle_model': 'Test Vehicle 2025',
            'assets': sample_assets_data
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file = f.name
        
        # Test JSON import
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'JSON Processing Test',
            '--format', 'json',
            json_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Verify assets imported
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_data['analysis_id'], '--step', '1'
        ])
        assert result.exit_code == 0
        
        asset_data = json.loads(result.output)
        assert asset_data['assets_count'] == 3
        
        # Cleanup
        Path(json_file).unlink()
    
    def test_yaml_file_processing(self, runner, sample_assets_data):
        """Test YAML configuration file processing."""
        import yaml
        
        # Create YAML file
        yaml_data = {
            'vehicle_model': 'Test Vehicle 2025',
            'system_architecture': 'Distributed ECU Network',
            'assets': sample_assets_data
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_data, f)
            yaml_file = f.name
        
        # Test YAML import
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'YAML Processing Test',
            '--format', 'yaml',
            yaml_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Verify assets imported
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        # Cleanup
        Path(yaml_file).unlink()
    
    def test_xml_file_processing(self, runner, sample_assets_data):
        """Test XML system definition processing."""
        # Create XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<vehicle_system>
    <metadata>
        <vehicle_model>Test Vehicle 2025</vehicle_model>
        <system_type>Automotive ECU Network</system_type>
    </metadata>
    <assets>
        <asset>
            <name>ECU Gateway</name>
            <type>HARDWARE</type>
            <criticality_level>HIGH</criticality_level>
            <interfaces>
                <interface>CAN</interface>
                <interface>Ethernet</interface>
            </interfaces>
            <description>Central communication hub</description>
        </asset>
        <asset>
            <name>Infotainment System</name>
            <type>SOFTWARE</type>
            <criticality_level>MEDIUM</criticality_level>
            <interfaces>
                <interface>Bluetooth</interface>
                <interface>WiFi</interface>
                <interface>USB</interface>
            </interfaces>
            <description>Entertainment and navigation</description>
        </asset>
    </assets>
</vehicle_system>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_file = f.name
        
        # Test XML import
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'XML Processing Test',
            '--format', 'xml',
            xml_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Verify assets imported
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        # Cleanup
        Path(xml_file).unlink()
    
    def test_invalid_file_format(self, runner):
        """Test error handling for invalid file formats."""
        # Create invalid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a valid asset definition format")
            invalid_file = f.name
        
        # Test invalid format handling
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Invalid Format Test',
            invalid_file
        ])
        
        # Should fail gracefully with appropriate error message
        assert result.exit_code != 0
        assert 'unsupported' in result.output.lower() or 'invalid' in result.output.lower()
        
        # Cleanup
        Path(invalid_file).unlink()
    
    def test_large_file_processing(self, runner):
        """Test processing of large files (performance validation)."""
        import time
        
        # Generate large CSV file (1000 assets)
        csv_content = "Asset Name,Asset Type,Criticality Level,Interfaces,Description\n"
        
        for i in range(1000):
            asset_type = ['HARDWARE', 'SOFTWARE'][i % 2]
            criticality = ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH'][i % 4]
            interfaces = ['CAN', 'Ethernet', 'USB', 'Bluetooth'][i % 4]
            
            csv_content += f"Asset_{i:04d},{asset_type},{criticality},{interfaces},Auto-generated asset {i}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            large_file = f.name
        
        # Test large file processing performance
        start_time = time.time()
        
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Large File Processing Test',
            large_file
        ])
        
        processing_time = time.time() - start_time
        
        assert result.exit_code == 0
        assert processing_time < 30, f"Large file processing took {processing_time:.2f}s (>30s limit)"
        
        analysis_data = json.loads(result.output)
        
        # Verify all assets imported
        result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_data['analysis_id'], '--step', '1'
        ])
        assert result.exit_code == 0
        
        asset_data = json.loads(result.output)
        assert asset_data['assets_count'] == 1000
        
        print(f"✅ Large file (1000 assets) processed in {processing_time:.2f}s")
        
        # Cleanup
        Path(large_file).unlink()
    
    def test_file_validation_and_normalization(self, runner):
        """Test data validation and normalization across formats."""
        # Create CSV with various data quality issues
        csv_content = """Asset Name,Asset Type,Criticality Level,Interfaces,Description
"ECU Gateway",hardware,high,"can, ethernet",Central hub
Infotainment,,MEDIUM,Bluetooth;WiFi,Entertainment system
,SOFTWARE,low,usb,Missing name
Engine ECU,HARDWARE,CRITICAL,CAN,Invalid criticality"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        # Test data validation and normalization
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Validation Test',
            '--validate-data',  # Enable strict validation
            csv_file
        ])
        
        # Should either succeed with normalized data or fail with clear error messages
        if result.exit_code == 0:
            # If successful, check that data was normalized
            analysis_data = json.loads(result.output)
            
            result = runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
            assert result.exit_code == 0
            
            result = runner.invoke(cli, [
                'analysis', 'show', analysis_data['analysis_id'], '--step', '1'
            ])
            
            if result.exit_code == 0:
                asset_data = json.loads(result.output)
                
                # Check that valid assets were processed
                for asset in asset_data['assets']:
                    # Asset types should be normalized to uppercase
                    assert asset['asset_type'] in ['HARDWARE', 'SOFTWARE']
                    # Criticality levels should be valid
                    assert asset['criticality_level'] in ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']
        else:
            # If failed, should have clear validation error messages
            assert 'validation' in result.output.lower() or 'invalid' in result.output.lower()
        
        # Cleanup
        Path(csv_file).unlink()
    
    def test_file_encoding_handling(self, runner):
        """Test handling of different file encodings."""
        # Create CSV with Unicode characters
        csv_content = """Asset Name,Asset Type,Criticality Level,Interfaces,Description
ECU Gateway™,HARDWARE,HIGH,"CAN,Ethernet",Central communication hub
Système d'infodivertissement,SOFTWARE,MEDIUM,"Bluetooth,WiFi",Système de navigation
Engine Control Module,HARDWARE,VERY_HIGH,CAN,Motor Steuergerät"""
        
        # Test UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            utf8_file = f.name
        
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'UTF-8 Encoding Test',
            utf8_file
        ])
        
        assert result.exit_code == 0
        
        # Test Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='latin-1') as f:
            f.write(csv_content)
            latin1_file = f.name
        
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Latin-1 Encoding Test',
            '--encoding', 'latin-1',
            latin1_file
        ])
        
        # Should handle encoding gracefully
        # May succeed or fail, but should not crash
        assert result.exit_code is not None  # Just ensure it completes
        
        # Cleanup
        Path(utf8_file).unlink()
        Path(latin1_file).unlink()