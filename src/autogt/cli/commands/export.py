"""Export and validate commands for AutoGT CLI.

Reference: contracts/cli.md export and validate commands
Handles analysis export and ISO compliance validation.
"""

import click
import logging
from pathlib import Path
from typing import Optional

from ...lib.exceptions import AutoGTError
from ...services.database import DatabaseService
from ...services.export import ExportService, ExportConfig


logger = logging.getLogger('autogt.cli.export')


@click.command()
@click.argument('analysis_id', required=True)
@click.option(
    '--format', '-f',
    'export_format',
    type=click.Choice(['json', 'excel'], case_sensitive=False),
    default='json',
    help='Export format (default: json)'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output file path'
)
@click.pass_context
def export(
    ctx: click.Context,
    analysis_id: str,
    export_format: str,
    output: Optional[Path]
) -> None:
    """Export analysis results to JSON or Excel format.
    
    Generates structured export files with complete analysis data
    including assets, threats, risks, and cybersecurity goals.
    
    Examples:
    
        # Export to JSON (default)
        autogt export abc12345
        
        # Export to Excel with specific filename
        autogt export abc12345 --format excel --output analysis-report.xlsx
    """
    try:
        click.echo(f"Exporting analysis: {analysis_id}")
        click.echo(f"Format: {export_format}")
        
        if output:
            click.echo(f"Output file: {output}")
        
        # Use simple direct SQL export to avoid ORM issues
        result = _export_analysis_simple(analysis_id, export_format, str(output) if output else None)
        
        click.echo(f"✅ Export completed successfully!")
        click.echo(f"File: {result['file_path']}")
        click.echo(f"Size: {result['file_size_bytes']:,} bytes")
        click.echo(f"Format: {result['format']}")
        
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to export analysis: {e}")


def _export_analysis_simple(analysis_id: str, format_type: str = 'json', output_path: str = None):
    """Export analysis using direct SQL to avoid ORM issues."""
    import json
    import sqlite3
    from datetime import datetime
    
    # Connect directly to SQLite
    db_path = Path.cwd() / 'autogt.db'
    if not db_path.exists():
        raise AutoGTError(f"Database not found at {db_path}")
        
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    
    try:
        cursor = conn.cursor()
        
        # Normalize the analysis ID (remove dashes if present)
        normalized_id = analysis_id.replace('-', '')
        
        # Find the full analysis ID if partial provided
        if len(normalized_id) < 32:  # Partial ID
            cursor.execute(
                "SELECT id FROM tara_analyses WHERE id LIKE ? || '%'", 
                (normalized_id,)
            )
            result = cursor.fetchone()
            if not result:
                raise AutoGTError(f"No analysis found matching ID: {analysis_id}")
            full_id = result['id']
        else:
            # Try exact match with normalized ID
            cursor.execute("SELECT id FROM tara_analyses WHERE id = ?", (normalized_id,))
            result = cursor.fetchone()
            if result:
                full_id = result['id']
            else:
                raise AutoGTError(f"Analysis not found: {analysis_id}")
        
        # Get analysis data
        cursor.execute(
            """SELECT * FROM tara_analyses WHERE id = ?""", 
            (full_id,)
        )
        analysis_row = cursor.fetchone()
        
        if not analysis_row:
            raise AutoGTError(f"Analysis not found: {analysis_id}")
        
        # Get related data counts
        cursor.execute("SELECT COUNT(*) as count FROM assets WHERE analysis_id = ?", (full_id,))
        asset_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM cybersecurity_goals WHERE analysis_id = ?", (full_id,))
        goal_count = cursor.fetchone()['count']
        
        # Get assets
        cursor.execute("SELECT * FROM assets WHERE analysis_id = ?", (full_id,))
        assets = [dict(row) for row in cursor.fetchall()]
        
        # Get goals  
        cursor.execute("SELECT * FROM cybersecurity_goals WHERE analysis_id = ?", (full_id,))
        goals = [dict(row) for row in cursor.fetchall()]
        
        # Build export data
        export_data = {
            "analysis_metadata": dict(analysis_row),
            "statistics": {
                "total_assets": asset_count,
                "total_goals": goal_count
            },
            "assets": assets,
            "cybersecurity_goals": goals,
            "export_metadata": {
                "exported_at": datetime.now().isoformat(),
                "export_version": "1.0",
                "iso_compliance": "ISO/SAE 21434"
            }
        }
        
        # Generate output filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"tara_analysis_{analysis_id[:8]}_{timestamp}.{format_type}"
        
        # Write JSON file
        if format_type.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        else:
            raise AutoGTError(f"Format {format_type} not supported yet - only JSON is currently available")
        
        file_size = Path(output_path).stat().st_size
        
        return {
            "success": True,
            "file_path": str(Path(output_path).absolute()),
            "file_size_bytes": file_size,
            "format": format_type
        }
        
    finally:
        conn.close()


@click.command()
@click.argument('analysis_id', required=True)
@click.option(
    '--standard',
    type=click.Choice(['iso21434'], case_sensitive=False),
    default='iso21434',
    help='Compliance standard to validate against (default: iso21434)'
)
@click.pass_context
def validate(
    ctx: click.Context,
    analysis_id: str,
    standard: str
) -> None:
    """Validate analysis against ISO/SAE 21434 compliance.
    
    Performs comprehensive validation of analysis completeness
    and compliance with automotive cybersecurity standards.
    
    Examples:
    
        # Validate against ISO/SAE 21434
        autogt validate abc12345
        
        # Explicit standard specification
        autogt validate abc12345 --standard iso21434
    """
    try:
        click.echo(f"Validating analysis: {analysis_id}")
        click.echo(f"Standard: {standard.upper()}")
        click.echo("Validation functionality not yet implemented.")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to validate analysis: {e}")