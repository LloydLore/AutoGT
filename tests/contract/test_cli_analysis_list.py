"""Contract test for `autogt analysis list` command.

Tests the CLI interface contract as specified in contracts/cli.md lines 56-82.
These tests MUST FAIL initially to follow TDD approach.
"""

import pytest
from click.testing import CliRunner

# Import will fail initially - this is expected for TDD
try:
    from autogt.cli.main import cli
except ImportError:
    cli = None


class TestAnalysisListCommand:
    """Test cases for autogt analysis list command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_list_all_analyses(self):
        """Test listing all TARA analyses."""
        result = self.runner.invoke(cli, ['analysis', 'list'])
        
        assert result.exit_code == 0
        # Per contracts/cli.md lines 69-82, expect JSON output
        import json
        response = json.loads(result.output)
        assert 'analyses' in response
        assert 'total' in response
        assert isinstance(response['analyses'], list)
        
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_list_analyses_with_status_filter(self):
        """Test filtering analyses by status."""
        result = self.runner.invoke(cli, [
            'analysis', 'list',
            '--status', 'in_progress'
        ])
        
        assert result.exit_code == 0
        import json
        response = json.loads(result.output)
        # All returned analyses should have in_progress status
        for analysis in response['analyses']:
            assert analysis['status'] == 'in_progress'
            
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_list_analyses_with_limit(self):
        """Test limiting number of results."""
        result = self.runner.invoke(cli, [
            'analysis', 'list',
            '--limit', '5'
        ])
        
        assert result.exit_code == 0
        import json
        response = json.loads(result.output)
        # Should return at most 5 analyses
        assert len(response['analyses']) <= 5
        
    @pytest.mark.skip(reason="CLI not implemented yet - TDD requirement")
    def test_list_analyses_table_format(self):
        """Test table output format."""
        result = self.runner.invoke(cli, [
            '--format', 'table',
            'analysis', 'list'
        ])
        
        assert result.exit_code == 0
        # Should contain table headers, not JSON
        assert 'analysis_id' in result.output or 'Analysis ID' in result.output
        assert '{' not in result.output  # Not JSON format