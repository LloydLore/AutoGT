"""Contract test for autogt assets define command.

Reference: contracts/cli.md lines 123-176
MUST FAIL initially to prove TDD compliance.
"""

import pytest
import subprocess


def test_assets_define_command_contract():
    """Contract test for autogt assets define command."""
    # Reference: contracts/cli.md lines 123-176
    result = subprocess.run(
        ["uv", "run", "autogt", "assets", "define", "--help"],
        capture_output=True,
        text=True
    )
    
    # Command should exist and show help
    assert "Define assets for a TARA analysis" in result.stdout
    assert "ANALYSIS_ID" in result.stdout
    assert "--interactive" in result.stdout
    assert "--file" in result.stdout


def test_assets_define_arguments_validation():
    """Validate ANALYSIS_ID argument requirements."""
    # Test missing ANALYSIS_ID should fail
    result = subprocess.run(
        ["uv", "run", "autogt", "assets", "define"],
        capture_output=True,
        text=True
    )
    
    # Should fail with usage error (missing required ANALYSIS_ID)
    assert result.returncode != 0
    assert "Missing parameter" in result.stderr or "Missing argument" in result.stderr or "Usage:" in result.stdout


def test_assets_define_interactive_process():
    """Validate interactive asset definition process."""
    # Test that interactive option is accepted
    result = subprocess.run(
        ["uv", "run", "autogt", "assets", "define", "test-id", "--interactive"],
        capture_output=True,
        text=True,
        input="\n",  # Send enter to exit interactive mode quickly
        timeout=5
    )
    
    # Should accept interactive option (may fail later due to invalid ID, but not usage error)
    assert result.returncode != 2  # Not a usage error


def test_assets_define_validation_rules():
    """Validate asset definition validation."""
    # Test with invalid analysis ID format
    result = subprocess.run(
        ["uv", "run", "autogt", "assets", "define", "invalid-id-format"],
        capture_output=True,
        text=True
    )
    
    # Should handle invalid ID gracefully (not crash)
    assert "assets" in result.stdout.lower() or "error" in result.stderr.lower() or "not found" in result.stderr.lower()


def test_assets_define_output_format():
    """Validate asset definition output format."""
    # Test that command accepts format options (via global flags)
    result = subprocess.run(
        ["uv", "run", "autogt", "--format", "json", "assets", "define", "--help"],
        capture_output=True,
        text=True
    )
    
    # Should accept global format option (help should still work)
    assert "Define assets" in result.stdout or "assets" in result.stdout.lower()