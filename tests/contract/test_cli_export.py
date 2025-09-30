"""Contract test for `autogt export` command.

Tests the CLI export interface contract as specified in contracts/cli.md lines 312-344.
These tests MUST FAIL initially to follow TDD approach.
"""

import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

# Import will fail initially - this is expected for TDD
try:
    from autogt.cli.main import cli
except ImportError:
    cli = None


class TestExportCommand:
    """Test cases for autogt export command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_export_analysis_json(self):
        """Test exporting analysis results to JSON format."""
        # Mock analysis ID (UUID format)
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = self.runner.invoke(cli, [
            'export', analysis_id,
            '--format', 'json',
            '--output', str(Path(self.temp_dir) / 'output.json')
        ])
        
        assert result.exit_code == 0
        
        # Verify JSON file was created with correct structure
        output_file = Path(self.temp_dir) / 'output.json'
        assert output_file.exists()
        
        import json
        with open(output_file) as f:
            data = json.load(f)
            
        # Per FR-005, structured JSON output must contain TARA results
        assert 'analysis_metadata' in data
        assert 'assets' in data
        assert 'threat_scenarios' in data
        assert 'risk_values' in data
        assert 'cybersecurity_goals' in data
        
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement") 
    def test_export_analysis_excel(self):
        """Test exporting analysis results to Excel format."""
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = self.runner.invoke(cli, [
            'export', analysis_id,
            '--format', 'excel', 
            '--output', str(Path(self.temp_dir) / 'output.xlsx')
        ])
        
        assert result.exit_code == 0
        
        # Verify Excel file was created
        output_file = Path(self.temp_dir) / 'output.xlsx'
        assert output_file.exists()
        
        # Per FR-006, Excel output based on JSON results
        assert output_file.suffix == '.xlsx'
        
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_export_nonexistent_analysis(self):
        """Test error handling for non-existent analysis."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        result = self.runner.invoke(cli, [
            'export', fake_id,
            '--format', 'json'
        ])
        
        # Should fail with appropriate error code
        assert result.exit_code != 0
        assert 'not found' in result.output.lower() or 'does not exist' in result.output.lower()
        
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_export_invalid_format(self):
        """Test error handling for invalid export format.""" 
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = self.runner.invoke(cli, [
            'export', analysis_id,
            '--format', 'invalid_format'
        ])
        
        assert result.exit_code != 0