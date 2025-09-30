"""Analysis command group for AutoGT CLI.

Reference: contracts/cli.md analysis commands (create, list, show)
Handles TARA analysis lifecycle management.
"""

import click
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from ...services import TaraProcessor, DatabaseService, FileHandler, AutoGenTaraAgent
from ...models import TaraAnalysis, CompletionStatus
from ...lib.exceptions import AutoGTError


logger = logging.getLogger('autogt.cli.analysis')


def get_services(ctx: click.Context) -> tuple:
    """Get initialized services from context."""
    config = ctx.obj.get('config_instance')
    if not config:
        raise AutoGTError("Configuration not available")
    
    # Initialize services
    db_service = DatabaseService(
        database_url=config.get_database_url()
    )
    
    file_handler = FileHandler()
    autogen_agent = AutoGenTaraAgent(config.get_gemini_config())
    
    tara_processor = TaraProcessor(
        db_service=db_service,
        file_handler=file_handler,
        autogen_agent=autogen_agent
    )
    
    return tara_processor, db_service


@click.group()
def analysis():
    """Manage TARA analyses (create, list, show)."""
    pass


@analysis.command()
@click.option(
    '--file', '-f',
    'input_file',
    type=click.Path(exists=True, path_type=Path),
    help='Input file (Excel, CSV, JSON, or text)'
)
@click.option(
    '--name', '-n',
    required=True,
    help='Analysis name'
)
@click.option(
    '--vehicle', '-v',
    required=True,
    help='Vehicle model being analyzed'
)
@click.option(
    '--description', '-d',
    help='Analysis description'
)
@click.option(
    '--phase',
    type=click.Choice(['concept', 'design', 'implementation', 'integration'], case_sensitive=False),
    default='design',
    help='Development phase (default: design)'
)
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help='Use interactive mode for asset definition'
)
@click.pass_context
def create(
    ctx: click.Context,
    input_file: Optional[Path],
    name: str,
    vehicle: str,
    description: Optional[str],
    phase: str,
    interactive: bool
) -> None:
    """Create a new TARA analysis.
    
    Creates a new threat analysis and risk assessment for the specified vehicle model.
    Can process input files or use interactive mode for asset definition.
    
    Examples:
    
        # Create analysis from Excel file
        autogt analysis create -f vehicle-data.xlsx -n "Model X Analysis" -v "Tesla Model X"
        
        # Create analysis with interactive asset definition
        autogt analysis create -n "Model Y Security" -v "Tesla Model Y" --interactive
        
        # Create analysis in concept phase
        autogt analysis create -f system-spec.csv -n "Concept Review" -v "Vehicle XYZ" --phase concept
    """
    try:
        logger.info(f"Creating new analysis: {name} for vehicle: {vehicle}")
        
        # Get services
        tara_processor, db_service = get_services(ctx)
        
        if input_file:
            # Process analysis from file
            click.echo(f"Processing input file: {input_file}")
            
            result = tara_processor.process_analysis_from_file(
                file_path=str(input_file),
                analysis_name=name,
                vehicle_model=vehicle
            )
            
            if result.success:
                click.echo(f"Analysis created successfully!")
                click.echo(f"Analysis ID: {result.analysis_id}")
                click.echo(f"Processing time: {result.total_execution_time_seconds:.2f}s")
                click.echo(f"Steps completed: {len(result.steps_completed)}/8")
                
                if result.final_status == CompletionStatus.COMPLETED:
                    click.echo("✅ Analysis completed successfully")
                else:
                    click.echo(f"⚠️  Analysis status: {result.final_status.value}")
            else:
                raise AutoGTError(f"Analysis creation failed: {result.error_message}")
        
        elif interactive:
            # Interactive mode
            click.echo("Starting interactive analysis creation...")
            analysis_id = _create_interactive_analysis(ctx, name, vehicle, description, phase)
            click.echo(f"Analysis created: {analysis_id}")
            click.echo("Use 'autogt assets define' to start defining assets interactively")
        
        else:
            # Create empty analysis
            analysis_id = _create_empty_analysis(ctx, name, vehicle, description, phase)
            click.echo(f"Empty analysis created: {analysis_id}")
            click.echo("Use 'autogt assets define' or provide input files to populate analysis")
        
        # Format output according to global format option
        if ctx.obj.get('output_format') == 'json':
            output_data = {
                "analysis_id": result.analysis_id if input_file else analysis_id,
                "name": name,
                "vehicle": vehicle,
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            click.echo(ctx.obj['format_output'](output_data, 'json'))
        
    except Exception as e:
        logger.error(f"Analysis creation failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to create analysis: {e}")


@analysis.command()
@click.option(
    '--status',
    type=click.Choice(['all', 'in_progress', 'completed', 'failed'], case_sensitive=False),
    default='all',
    help='Filter by completion status (default: all)'
)
@click.option(
    '--vehicle', '-v',
    help='Filter by vehicle model'
)
@click.option(
    '--limit', '-l',
    type=int,
    default=10,
    help='Maximum number of results (default: 10)'
)
@click.pass_context
def list(
    ctx: click.Context,
    status: str,
    vehicle: Optional[str],
    limit: int
) -> None:
    """List existing TARA analyses with filtering options.
    
    Shows a table of analyses with basic information including status,
    creation date, and progress indicators.
    
    Examples:
    
        # List all analyses
        autogt analysis list
        
        # List only completed analyses
        autogt analysis list --status completed
        
        # List analyses for specific vehicle
        autogt analysis list --vehicle "Tesla Model X"
        
        # List in JSON format
        autogt analysis list --format json
    """
    try:
        logger.info(f"Listing analyses with status={status}, vehicle={vehicle}")
        
        # Get database service
        _, db_service = get_services(ctx)
        
        with db_service.get_session() as session:
            # Build query
            query = session.query(TaraAnalysis)
            
            # Apply filters
            if status != 'all':
                status_enum = CompletionStatus(status.upper())
                query = query.filter(TaraAnalysis.completion_status == status_enum)
            
            if vehicle:
                query = query.filter(TaraAnalysis.vehicle_model.ilike(f'%{vehicle}%'))
            
            # Order by creation date (newest first)
            query = query.order_by(TaraAnalysis.created_at.desc())
            
            # Apply limit
            analyses = query.limit(limit).all()
            
            if not analyses:
                click.echo("No analyses found matching the criteria.")
                return
            
            # Prepare output data
            output_data = []
            for analysis in analyses:
                output_data.append({
                    "id": str(analysis.id)[:8],  # Short ID for display
                    "name": analysis.analysis_name,
                    "vehicle": analysis.vehicle_model,
                    "status": analysis.completion_status.value.lower().replace('_', ' '),
                    "phase": analysis.analysis_phase.value.lower(),
                    "progress": f"{_calculate_progress_percentage(analysis)}%",
                    "created": analysis.created_at.strftime("%Y-%m-%d %H:%M"),
                    "completed": analysis.completed_at.strftime("%Y-%m-%d %H:%M") if analysis.completed_at else "-"
                })
            
            # Format and display output
            formatted_output = ctx.obj['format_output'](output_data, ctx.obj['output_format'])
            click.echo(formatted_output)
            
            # Show summary
            if ctx.obj['output_format'] == 'table':
                click.echo(f"\nShowing {len(output_data)} of {len(output_data)} analyses")
    
    except Exception as e:
        logger.error(f"Failed to list analyses: {e}", exc_info=True)
        raise AutoGTError(f"Failed to list analyses: {e}")


@analysis.command()
@click.argument('analysis_id', required=True)
@click.option(
    '--details', '-d',
    is_flag=True,
    help='Show detailed information including assets and risks'
)
@click.pass_context
def show(
    ctx: click.Context,
    analysis_id: str,
    details: bool
) -> None:
    """Show detailed information about a specific analysis.
    
    Displays comprehensive information about an analysis including status,
    progress, assets, threats, and risk summary.
    
    Examples:
    
        # Show basic analysis information
        autogt analysis show abc12345
        
        # Show detailed information including assets and risks  
        autogt analysis show abc12345 --details
        
        # Show in JSON format
        autogt analysis show abc12345 --format json
    """
    try:
        logger.info(f"Showing analysis details for: {analysis_id}")
        
        # Get services
        tara_processor, db_service = get_services(ctx)
        
        # Get analysis status from processor
        status_data = tara_processor.get_analysis_status(analysis_id)
        
        if 'error' in status_data:
            raise AutoGTError(status_data['error'])
        
        # Get detailed information if requested
        if details:
            detailed_data = _get_detailed_analysis_info(db_service, analysis_id)
            status_data.update(detailed_data)
        
        # Format and display output
        formatted_output = ctx.obj['format_output'](status_data, ctx.obj['output_format'])
        click.echo(formatted_output)
    
    except Exception as e:
        logger.error(f"Failed to show analysis: {e}", exc_info=True)
        raise AutoGTError(f"Failed to show analysis: {e}")


def _create_interactive_analysis(
    ctx: click.Context, name: str, vehicle: str, description: Optional[str], phase: str
) -> str:
    """Create analysis using interactive mode."""
    # This will be implemented when we create the assets command
    # For now, create empty analysis
    return _create_empty_analysis(ctx, name, vehicle, description, phase)


def _create_empty_analysis(
    ctx: click.Context, name: str, vehicle: str, description: Optional[str], phase: str
) -> str:
    """Create empty analysis."""
    from ...models import AnalysisPhase
    
    _, db_service = get_services(ctx)
    
    with db_service.get_session() as session:
        analysis = TaraAnalysis(
            analysis_name=name,
            vehicle_model=vehicle,
            analysis_phase=AnalysisPhase(phase.upper()),
            completion_status=CompletionStatus.IN_PROGRESS
        )
        
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        
        return str(analysis.id)


def _calculate_progress_percentage(analysis: TaraAnalysis) -> int:
    """Calculate progress percentage for analysis."""
    if analysis.completion_status == CompletionStatus.COMPLETED:
        return 100
    elif analysis.completion_status == CompletionStatus.FAILED:
        return 0
    
    # Simple progress based on current step
    current_step = analysis.get_current_step()
    if not current_step:
        return 0
    
    # Map steps to progress percentages
    step_progress = {
        "asset_identification": 12,
        "threat_scenario_identification": 25,
        "attack_path_analysis": 37,
        "attack_feasibility_rating": 50,
        "impact_rating": 62,
        "risk_value_determination": 75,
        "risk_treatment_decision": 87,
        "cybersecurity_goals": 100
    }
    
    return step_progress.get(current_step, 0)


def _get_detailed_analysis_info(db_service: DatabaseService, analysis_id: str) -> Dict[str, Any]:
    """Get detailed analysis information."""
    with db_service.get_session() as session:
        from sqlalchemy.orm import selectinload
        from ...models import TaraAnalysis
        
        analysis = session.query(TaraAnalysis).options(
            selectinload(TaraAnalysis.assets),
            selectinload(TaraAnalysis.cybersecurity_goals)
        ).filter(TaraAnalysis.id == analysis_id).first()
        
        if not analysis:
            return {"error": "Analysis not found"}
        
        # Count various elements
        total_assets = len(analysis.assets)
        total_threats = sum(len(asset.threat_scenarios) for asset in analysis.assets)
        total_risks = sum(
            len(threat.risk_values)
            for asset in analysis.assets
            for threat in asset.threat_scenarios
        )
        total_goals = len(analysis.cybersecurity_goals)
        
        return {
            "asset_count": total_assets,
            "threat_count": total_threats, 
            "risk_count": total_risks,
            "goal_count": total_goals,
            "assets": [
                {
                    "name": asset.name,
                    "type": asset.asset_type.value,
                    "criticality": asset.criticality_level.value
                }
                for asset in analysis.assets[:5]  # Show first 5 assets
            ],
            "high_risks": []  # Would need to calculate from risk values
        }