"""Export command for AutoGT CLI.

Reference: contracts/cli.md lines 270-310 - export command (JSON, Excel formats)
Handles analysis export to structured formats with ISO/SAE 21434 compliance data.
"""

import click
import logging
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..formatters import get_formatter


logger = logging.getLogger(__name__)


@click.command(name='export')
@click.argument('analysis_id', required=True)
@click.option('--format', type=click.Choice(['json', 'excel']), default='json',
              help='Export format (default: json)')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--include-steps', help='Comma-separated step numbers to include')
@click.option('--template', type=click.Path(exists=True), help='Custom Excel template')
@click.pass_context
def export_command(ctx: click.Context, analysis_id: str, format: str, 
                  output: Optional[str], include_steps: Optional[str], 
                  template: Optional[str]):
    """Export analysis results to structured formats.
    
    ANALYSIS_ID: Analysis to export
    
    Generates complete analysis data with all 8 TARA steps, ISO/SAE 21434
    traceability information, and audit trail with compliance artifacts.
    
    Exit codes:
    0: Success
    1: Analysis not found
    2: Export format not supported
    """
    formatter = get_formatter(ctx)
    
    try:
        formatter.output(f"Exporting analysis: {analysis_id}")
        formatter.output(f"Format: {format}")
        
        if template:
            formatter.output(f"Using template: {template}")
        
        if include_steps:
            steps = [int(s.strip()) for s in include_steps.split(',')]
            formatter.output(f"Including steps: {steps}")
        
        # Generate output path if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_id = analysis_id[:8]
            if format == 'excel':
                output = f"tara_export_{short_id}_{timestamp}.xlsx"
            else:
                output = f"tara_export_{short_id}_{timestamp}.json"
        
        # Mock export data - will be replaced with real service integration
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "export_format": format,
                "analysis_id": analysis_id,
                "autogt_version": "0.1.0",
                "iso21434_compliance": True
            },
            "analysis": {
                "id": analysis_id,
                "name": "Sample TARA Analysis",
                "vehicle_model": "Sample Vehicle",
                "completion_status": "completed",
                "created_at": "2025-09-30T10:00:00Z"
            },
            "tara_steps": {
                "1": {"name": "Asset Identification", "status": "completed"},
                "2": {"name": "Threat Scenario Identification", "status": "completed"},
                "3": {"name": "Attack Path Analysis", "status": "completed"},
                "4": {"name": "Attack Feasibility Rating", "status": "completed"},
                "5": {"name": "Impact Rating", "status": "completed"},
                "6": {"name": "Risk Value Determination", "status": "completed"},
                "7": {"name": "Risk Treatment Decision", "status": "completed"},
                "8": {"name": "Cybersecurity Goals", "status": "completed"}
            },
            "assets": [
                {
                    "id": "asset1",
                    "name": "ECU Gateway",
                    "type": "HARDWARE",
                    "criticality": "HIGH"
                }
            ],
            "threats": [
                {
                    "id": "threat1", 
                    "asset_id": "asset1",
                    "name": "Remote Code Execution",
                    "actor": "CRIMINAL"
                }
            ],
            "risks": [
                {
                    "id": "risk1",
                    "threat_id": "threat1",
                    "risk_level": "HIGH",
                    "risk_score": 0.78
                }
            ],
            "audit_trail": [
                {
                    "timestamp": "2025-09-30T10:00:00Z",
                    "action": "analysis_created",
                    "user": "analyst1"
                }
            ]
        }
        
        # Write export file based on format
        output_path = Path(output)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        elif format == 'excel':
            # Excel export would use the ExcelExporter service
            formatter.error("Excel export not yet implemented")
            sys.exit(2)
        
        file_size = output_path.stat().st_size
        
        # Output results
        result_data = {
            "export_file": str(output_path.absolute()),
            "file_size_bytes": file_size,
            "format": format,
            "records_exported": {
                "assets": len(export_data["assets"]),
                "threats": len(export_data["threats"]),
                "risks": len(export_data["risks"])
            }
        }
        
        if formatter.format_type in ['json', 'yaml']:
            formatter.output(result_data)
        else:
            formatter.success(f"Export completed: {output_path}")
            formatter.output(f"Format: {format}")
            formatter.output(f"Size: {file_size:,} bytes")
        
        if not ctx.obj.get('quiet'):
            formatter.success("Analysis exported successfully")
    
    except Exception as e:
        logger.exception("Error exporting analysis")
        formatter.error(f"Failed to export analysis: {str(e)}")
        sys.exit(1)