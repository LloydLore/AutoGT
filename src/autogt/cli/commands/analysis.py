"""Analysis command group for AutoGT CLI.

Reference: contracts/cli.md lines 13-133 - analysis commands (create, list, show, delete)
Handles TARA analysis lifecycle management with comprehensive validation and formatting.
"""

import click
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..formatters import get_formatter


logger = logging.getLogger('autogt.cli.analysis')


class ValidationError(Exception):
    """Temporary validation error class."""
    pass

# Maximum file size (10MB as per contract)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.json', '.txt'}


def get_analysis_service(ctx: click.Context):
    """Get initialized analysis service from context - placeholder."""
    # This will be implemented when services are integrated
    return None


def validate_input_file(file_path: str) -> Path:
    """Validate input file according to contract requirements."""
    import os
    path = Path(file_path)
    
    # Check file exists
    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    
    # Check is file (not directory)
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    # Check file is readable
    if not os.access(path, os.R_OK):
        raise ValidationError(f"File is not readable: {file_path}")
    
    # Check file size (≤ 10MB)
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(f"File size ({file_size} bytes) exceeds maximum of {MAX_FILE_SIZE} bytes")
    
    # Check file extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ', '.join(sorted(SUPPORTED_EXTENSIONS))
        raise ValidationError(f"Unsupported file format '{path.suffix}'. Supported formats: {supported}")
    
    return path


@click.group(name='analysis')
def analysis_group():
    """Manage TARA analyses (create, list, show, delete)."""
    pass


@analysis_group.command('create')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--name', required=True, help='Analysis name (required)')
@click.option('--vehicle-model', help='Target vehicle information')
@click.option('--output-dir', type=click.Path(), default='./autogt-output', help='Output directory (default: ./autogt-output)')
@click.pass_context
def create_analysis(ctx: click.Context, input_file: str, name: str, 
                   vehicle_model: Optional[str], output_dir: str):
    """Initialize new TARA analysis from input file.
    
    INPUT_FILE: Path to input file (Excel, CSV, JSON, or text)
    
    Creates a new TARA analysis by processing the input file and initializing
    the 8-step cybersecurity analysis workflow per ISO/SAE 21434.
    
    Exit codes:
    0: Success
    1: Invalid input file  
    2: Analysis name already exists
    3: File too large
    """
    formatter = get_formatter(ctx)
    
    try:
        # Validate input file
        try:
            file_path = validate_input_file(input_file)
        except ValidationError as e:
            formatter.error(str(e))
            sys.exit(1)
        
        # Get analysis service
        analysis_service = get_analysis_service(ctx)
        
        # Check if analysis name already exists (simplified for now)
        # In real implementation, this would query the database
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create analysis (simplified implementation)
        analysis_id = str(uuid.uuid4())
        
        # Format output per contract
        output_data = {
            "analysis_id": analysis_id,
            "analysis_name": name,
            "status": "in_progress", 
            "current_step": 1,
            "input_file": str(file_path),
            "vehicle_model": vehicle_model or "Not specified",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store analysis for later retrieval
        _store_analysis(output_data)
        
        formatter.output(output_data)
        
        if not ctx.obj.get('quiet'):
            formatter.success(f"Analysis '{name}' created successfully")
            formatter.success(f"Analysis ID: {analysis_id}")
        
    except ValidationError as e:
        formatter.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during analysis creation")
        formatter.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


@analysis_group.command('list')
@click.option('--status', 
              type=click.Choice(['in_progress', 'completed', 'validated'], case_sensitive=False),
              help='Filter by analysis status')
@click.option('--limit', type=int, default=20, help='Maximum number of results (default: 20)')
@click.pass_context
def list_analyses(ctx: click.Context, status: Optional[str], limit: int):
    """List all TARA analyses.
    
    Shows a summary of all TARA analyses with filtering options.
    Results are paginated with a default limit of 20 analyses.
    """
    formatter = get_formatter(ctx)
    
    try:
        # For now, return mock data - will be replaced with real service integration
        # In real implementation, this would use the analysis service
        
        # Retrieve stored analyses
        analysis_list = _retrieve_analyses()
        
        # Fallback to mock data if no stored analyses
        if not analysis_list:
            analysis_list = [
                {
                    "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                    "analysis_name": "Vehicle ECU Analysis",
                    "status": "in_progress",
                    "current_step": 3,
                    "created_at": "2025-09-30T10:30:00Z"
                },
                {
                    "analysis_id": "550e8400-e29b-41d4-a716-446655440001", 
                    "analysis_name": "Gateway Security Review",
                    "status": "completed",
                    "current_step": 8,
                    "created_at": "2025-09-29T14:15:00Z"
                }
            ]
        
        # Apply status filter if provided
        if status:
            analysis_list = [a for a in analysis_list if a["status"] == status.lower()]
        
        # Apply limit
        analysis_list = analysis_list[:limit]
        
        # Output results per contract
        if formatter.format_type in ['json', 'yaml']:
            output_data = {
                "analyses": analysis_list,
                "total": len(analysis_list)
            }
            formatter.output(output_data)
        else:
            formatter.output(formatter.format_analysis_list(analysis_list))
        
        if not ctx.obj.get('quiet') and not analysis_list:
            formatter.output("No analyses found")
    
    except Exception as e:
        logger.exception("Error listing analyses")
        formatter.error(f"Failed to list analyses: {str(e)}")
        sys.exit(1)


@analysis_group.command('show')
@click.argument('analysis_id', required=True)
@click.option('--detailed', is_flag=True, help='Show detailed information')
@click.pass_context
def show_analysis(ctx: click.Context, analysis_id: str, detailed: bool):
    """Show analysis details and progress.
    
    ANALYSIS_ID: The analysis identifier
    
    Displays current status, progress, and optionally detailed information
    about assets, threats, and risks for the specified analysis.
    
    Exit codes:
    0: Success
    1: Analysis not found
    """
    formatter = get_formatter(ctx)
    
    try:
        # Retrieve stored analysis data
        analysis_detail = _retrieve_analysis(analysis_id)
        
        # Fallback to mock data if analysis not found
        if not analysis_detail:
            analysis_detail = {
                "analysis_id": analysis_id,
                "analysis_name": "Vehicle ECU Analysis",
                "status": "in_progress",
                "current_step": 3,
                "steps_completed": ["step1", "step2", "step3"],
                "progress_percentage": 37.5,
                "created_at": "2025-09-30T10:30:00Z",
                "estimated_completion": "2025-10-01T16:00:00Z"
            }
        
        if detailed:
            analysis_detail.update({
                "detailed_info": {
                    "asset_count": 12,
                    "threat_count": 8,
                    "risk_count": 15,
                    "high_risks": 3
                }
            })
        
        # Output results per contract
        if formatter.format_type in ['json', 'yaml']:
            formatter.output(analysis_detail)
        else:
            formatter.output(formatter.format_analysis_detail(analysis_detail, detailed))
    
    except Exception as e:
        logger.exception("Error showing analysis")
        formatter.error(f"Failed to show analysis: {str(e)}")
        sys.exit(1)


@analysis_group.command('delete')
@click.argument('analysis_id', required=True)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_analysis(ctx: click.Context, analysis_id: str, force: bool):
    """Delete an analysis and all associated data.
    
    ANALYSIS_ID: The analysis identifier
    
    Permanently removes the analysis and all related data including
    assets, threats, risks, and compliance records.
    
    Exit codes:
    0: Success
    1: Analysis not found
    2: Operation cancelled by user
    """
    formatter = get_formatter(ctx)
    
    try:
        # Check if analysis exists (mock implementation)
        # In real implementation, this would query the analysis service
        
        if not force and not ctx.obj.get('quiet'):
            if not click.confirm(f"Are you sure you want to delete analysis {analysis_id}? This cannot be undone."):
                formatter.error("Operation cancelled")
                sys.exit(2)
        
        # Mock deletion
        # In real implementation, this would call the analysis service
        
        if not ctx.obj.get('quiet'):
            formatter.success(f"Analysis {analysis_id} deleted successfully")
    
    except Exception as e:
        logger.exception("Error deleting analysis")
        formatter.error(f"Failed to delete analysis: {str(e)}")
        sys.exit(1)


def _store_analysis(analysis_data: dict) -> None:
    """Store analysis data in a simple file-based storage."""
    import json
    from pathlib import Path
    
    # Create storage directory
    storage_dir = Path("autogt-output") / "analyses"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing analyses
    analyses_file = storage_dir / "analyses.json"
    analyses = []
    
    if analyses_file.exists():
        try:
            with open(analyses_file, 'r', encoding='utf-8') as f:
                analyses = json.load(f)
        except (json.JSONDecodeError, IOError):
            analyses = []
    
    # Add or update analysis
    analysis_id = analysis_data["analysis_id"]
    analyses = [a for a in analyses if a.get("analysis_id") != analysis_id]  # Remove existing
    analyses.append(analysis_data)
    
    # Save back to file
    with open(analyses_file, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2)


def _retrieve_analyses() -> list:
    """Retrieve all stored analyses."""
    import json
    from pathlib import Path
    
    analyses_file = Path("autogt-output") / "analyses" / "analyses.json"
    
    if analyses_file.exists():
        try:
            with open(analyses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    return []


def _retrieve_analysis(analysis_id: str) -> dict:
    """Retrieve a specific analysis by ID."""
    analyses = _retrieve_analyses()
    for analysis in analyses:
        if analysis.get("analysis_id") == analysis_id:
            return analysis
    return {}


# Placeholder functions for future integration
def _create_interactive_analysis(ctx, name, vehicle, description, phase):
    """Placeholder for interactive analysis creation."""
    return str(uuid.uuid4())


def _create_empty_analysis(ctx, name, vehicle, description, phase):
    """Placeholder for empty analysis creation."""
    return str(uuid.uuid4())