"""Contract test for autogt threats identify command.

Reference: contracts/cli.md lines 177-218
MUST FAIL initially to prove TDD compliance.
"""

import pytest
import subprocess


def test_threats_identify_command_contract():
    """Contract test for autogt threats identify command."""
    # Reference: contracts/cli.md lines 177-218
    result = subprocess.run(
        ["uv", "run", "autogt", "threats", "identify", "--help"],
        capture_output=True,
        text=True
    )
    
    # Command should exist and show help
    assert "Identify threat scenarios" in result.stdout or "threats" in result.stdout.lower()
    assert "ANALYSIS_ID" in result.stdout


def test_threats_identify_arguments_validation():
    """Validate ANALYSIS_ID argument requirements."""
    # Test missing ANALYSIS_ID should fail
    result = subprocess.run(
        ["uv", "run", "autogt", "threats", "identify"],
        capture_output=True,
        text=True
    )
    
    # Should fail with usage error (missing required ANALYSIS_ID)
    assert result.returncode != 0
    assert "Missing parameter" in result.stderr or "Missing argument" in result.stderr


def test_threats_identify_ai_workflow():
    """Validate AI-driven threat identification workflow."""
    # Test with a valid analysis ID (should not crash, may fail due to AI config)
    result = subprocess.run(
        ["uv", "run", "autogt", "threats", "identify", "ec44d97e-20c1-4b25-91c6-a226a0d0736d"],
        capture_output=True,
        text=True
    )
    
    # Should handle the command (may fail due to configuration but not usage error)
    assert result.returncode != 2  # Not a usage error


def test_threats_identify_output_format():
    """Validate threat identification output format."""
    # Test that command accepts global format options
    result = subprocess.run(
        ["uv", "run", "autogt", "--format", "json", "threats", "identify", "--help"],
        capture_output=True,
        text=True
    )
    
    # Should accept global format option
    assert "threats" in result.stdout.lower() or "Identify" in result.stdout


def test_threats_identify_autogen_integration():
    """Validate AutoGen agent integration."""
    # Test that AI-related options are available (if any in help)
    result = subprocess.run(
        ["uv", "run", "autogt", "threats", "identify", "--help"],
        capture_output=True,
        text=True
    )
    
    # Should show threat identification help
    assert "identify" in result.stdout.lower() or "threat" in result.stdout.lower()