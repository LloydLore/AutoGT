"""The autogt analysis click group tests.

"""
import pytest
import sys
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from autogt.cli.main import cli, analysis
from autogt.lib.config import Config

def test_analysis_command_registered():
    """Test that the analysis command is registered and has the expected subcommands."""
    runner = CliRunner()
    
    # Instead of testing the entire CLI, we'll test the analysis command group directly
    result = runner.invoke(analysis.analysis, ['--help'])
    
    # This should pass without needing to mock the Config
    assert result.exit_code == 0
    assert "create" in result.output
    assert "list" in result.output
    assert "show" in result.output

# Test create command
def test_analysis_create_requires_parameters():
    """Test that the create command requires necessary parameters."""
    runner = CliRunner()

    # Test without required parameters
    result = runner.invoke(analysis.analysis, ['create'])
    assert result.exit_code != 0
    assert "Missing option" in result.output
    assert "--name" in result.output

def test_analysis_create_success(monkeypatch):
    """Test a successful analysis creation by mocking the internal functions and context."""
    runner = CliRunner()
    
    # Create mock services
    mock_processor = MagicMock()
    mock_db_service = MagicMock()
    
    # Now let's override the get_services function directly
    def mock_get_services(ctx):
        return mock_processor, mock_db_service
    
    monkeypatch.setattr("autogt.cli.commands.analysis.get_services", mock_get_services)
    
    # Override _create_empty_analysis to return our test ID
    def mock_create_empty_analysis(ctx, name, vehicle, description, phase):
        return "test-uuid-123"
    
    monkeypatch.setattr(
        "autogt.cli.commands.analysis._create_empty_analysis", 
        mock_create_empty_analysis
    )
    
    # Create a test CLI environment with context
    with runner.isolated_filesystem():
        # Test with the analysis command directly and required options
        result = runner.invoke(
            analysis.analysis, 
            ['create', '--name', 'Test Analysis', '--vehicle', 'Model X'],
            obj={"config_instance": MagicMock()}  # Initialize context.obj
        )
        
        # Print debug info
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        
        # Check expectations
        assert result.exit_code == 0
        assert "Empty analysis created: test-uuid-123" in result.output
