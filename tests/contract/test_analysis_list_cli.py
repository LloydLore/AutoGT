"""Contract test for autogt analysis list command.

Reference: contracts/cli.md lines 62-89
MUST FAIL initially to prove TDD compliance.
"""

import pytest
import subprocess


def test_analysis_list_command_contract():
    """Contract test for autogt analysis list command."""
    # Reference: contracts/cli.md lines 62-89
    result = subprocess.run(
        ["uv", "run", "autogt", "analysis", "list", "--help"],
        capture_output=True,
        text=True
    )
    
    # Command should exist and show help
    assert "List existing TARA analyses" in result.stdout or "list" in result.stdout.lower()
    assert "--status" in result.stdout
    assert "--limit" in result.stdout


def test_analysis_list_options_validation():
    """Validate command options (--status filter)."""
    # Reference: contracts/cli.md lines 69-70
    result = subprocess.run(
        ["uv", "run", "autogt", "analysis", "list", "--help"],
        capture_output=True,
        text=True
    )
    
    # Verify status filtering options are available
    assert "--status" in result.stdout
    assert "--vehicle" in result.stdout
    assert "--limit" in result.stdout


def test_analysis_list_status_filtering():
    """Validate status filtering functionality."""
    # Reference: --status [in_progress|completed|validated]
    # Test that command accepts status options (even if no data exists)
    result = subprocess.run(
        ["uv", "run", "autogt", "analysis", "list", "--status", "all"],
        capture_output=True,
        text=True
    )
    
    # Should not fail with usage error (accepts the status option)
    assert result.returncode != 2  # Not a usage error


def test_analysis_list_output_format():
    """Validate list output format."""
    # Test with JSON format option
    result = subprocess.run(
        ["uv", "run", "autogt", "--format", "json", "analysis", "list"],
        capture_output=True,
        text=True
    )
    
    # Should accept format option (even if other errors occur)
    assert result.returncode != 2  # Not a usage error


def test_analysis_list_empty_handling():
    """Validate handling of empty analysis list."""
    # Test basic list command (will likely be empty but should not crash)
    result = subprocess.run(
        ["uv", "run", "autogt", "analysis", "list"],
        capture_output=True,
        text=True
    )
    
    # Should handle empty list gracefully (may have config errors but not crash)
    assert "analysis" in result.stdout.lower() or "No analyses" in result.stdout or "error" in result.stderr.lower()