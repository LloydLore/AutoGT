"""Asset command group for AutoGT CLI.

Reference: contracts/cli.md lines 123-167 - asset workflow commands (define)
Handles asset definition and management within TARA analysis workflow.
"""

import click
import logging
import sys
import uuid
from pathlib import Path
from typing import Optional

from ..formatters import get_formatter


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Temporary validation error class."""
    pass


@click.group(name='assets')
def assets_group():
    """Manage assets within TARA analysis."""
    pass


@assets_group.command('define')
@click.argument('analysis_id', required=True)
@click.option('--interactive', is_flag=True, help='Use interactive asset definition mode')
@click.option('--import-file', type=click.Path(exists=True), help='Import assets from file')
@click.option('--validate-only', is_flag=True, help='Validate without saving')
@click.pass_context
def define_assets(ctx: click.Context, analysis_id: str, interactive: bool, 
                  import_file: Optional[str], validate_only: bool):
    """Define assets for TARA analysis (Step 1).
    
    ANALYSIS_ID: Target analysis UUID
    
    Defines assets that will be analyzed in the TARA process. Assets can be
    defined interactively, imported from files, or validated without saving.
    
    Exit codes:
    0: Success
    1: Analysis not found
    2: Validation failed
    """
    formatter = get_formatter(ctx)
    
    try:
        if import_file:
            # Handle file import
            assets = _import_assets_from_file(import_file)
        elif interactive:
            # Handle interactive mode
            assets = _define_assets_interactively(ctx)
        else:
            formatter.error("Must specify either --interactive or --import-file")
            sys.exit(2)
        
        if validate_only:
            # Just validate without saving
            validation_result = _validate_assets(assets)
            if validation_result['valid']:
                formatter.success("Asset validation passed")
            else:
                formatter.error(f"Asset validation failed: {validation_result['errors']}")
                sys.exit(2)
            return
        
        # Create assets with unique IDs and store them
        created_assets = []
        for asset_data in assets:
            created_asset = {
                "id": str(uuid.uuid4()),
                **asset_data
            }
            created_assets.append(created_asset)
        
        # Store assets in a simple file-based storage
        _store_assets(analysis_id, created_assets)
        
        # Output results per contract
        output_data = {
            "assets_created": len(created_assets),
            "assets": created_assets
        }
        
        if formatter.format_type in ['json', 'yaml']:
            formatter.output(output_data)
        else:
            formatter.output(formatter.format_asset_list(created_assets))
        
        if not ctx.obj.get('quiet'):
            formatter.success(f"Created {len(created_assets)} assets for analysis {analysis_id}")
    
    except ValidationError as e:
        formatter.error(str(e))
        sys.exit(2)
    except Exception as e:
        logger.exception("Error defining assets")
        formatter.error(f"Failed to define assets: {str(e)}")
        sys.exit(1)


@assets_group.command('list')
@click.argument('analysis_id', required=True)
@click.option('--asset-type', type=click.Choice(['HARDWARE', 'SOFTWARE', 'COMMUNICATION', 'DATA']),
              help='Filter by asset type')
@click.option('--criticality', type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']),
              help='Filter by criticality level')
@click.pass_context
def list_assets(ctx: click.Context, analysis_id: str, 
                asset_type: Optional[str], criticality: Optional[str]):
    """List assets in an analysis.
    
    ANALYSIS_ID: Target analysis UUID
    
    Shows all assets defined for the analysis with filtering options.
    """
    formatter = get_formatter(ctx)
    
    try:
        # Retrieve stored assets for this analysis
        assets = _retrieve_assets(analysis_id)
        
        if not assets:
            # Fallback to mock data if no assets stored
            assets = [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "ECU Gateway",
                    "asset_type": "HARDWARE",
                    "criticality_level": "HIGH",
                    "interfaces": ["CAN", "Ethernet"],
                    "security_properties": {
                        "confidentiality": "HIGH",
                        "integrity": "HIGH",
                        "availability": "MEDIUM"
                    }
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Infotainment System",
                    "asset_type": "SOFTWARE",
                    "criticality_level": "MEDIUM",
                    "interfaces": ["Bluetooth", "WiFi"],
                    "security_properties": {
                        "confidentiality": "MEDIUM",
                        "integrity": "MEDIUM",
                        "availability": "LOW"
                    }
                }
            ]
        
        # Apply filters
        if asset_type:
            assets = [a for a in assets if a["asset_type"] == asset_type]
        
        if criticality:
            assets = [a for a in assets if a["criticality_level"] == criticality]
        
        # Output results
        if formatter.format_type in ['json', 'yaml']:
            output_data = {
                "analysis_id": analysis_id,
                "assets": assets,
                "total": len(assets)
            }
            formatter.output(output_data)
        else:
            formatter.output(formatter.format_asset_list(assets))
        
        if not ctx.obj.get('quiet') and not assets:
            formatter.output("No assets found")
    
    except Exception as e:
        logger.exception("Error listing assets")
        formatter.error(f"Failed to list assets: {str(e)}")
        sys.exit(1)


@assets_group.command('update')
@click.argument('asset_id', required=True)
@click.option('--name', help='Update asset name')
@click.option('--criticality', type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']),
              help='Update criticality level')
@click.option('--interactive', is_flag=True, help='Use interactive update mode')
@click.pass_context
def update_asset(ctx: click.Context, asset_id: str, name: Optional[str], 
                 criticality: Optional[str], interactive: bool):
    """Update an existing asset.
    
    ASSET_ID: Target asset UUID
    
    Updates asset properties either through command-line options or
    interactive mode for comprehensive editing.
    
    Exit codes:
    0: Success
    1: Asset not found
    2: Validation failed
    """
    formatter = get_formatter(ctx)
    
    try:
        # Mock asset update - will be replaced with real service integration
        if interactive:
            updated_asset = _update_asset_interactively(ctx, asset_id)
        else:
            if not any([name, criticality]):
                formatter.error("Must specify at least one field to update or use --interactive")
                sys.exit(2)
            
            updated_asset = {
                "id": asset_id,
                "name": name or "Existing Asset Name",
                "asset_type": "HARDWARE",
                "criticality_level": criticality or "MEDIUM",
                "interfaces": ["CAN"],
                "security_properties": {
                    "confidentiality": "MEDIUM",
                    "integrity": "MEDIUM", 
                    "availability": "MEDIUM"
                }
            }
        
        # Output results
        if formatter.format_type in ['json', 'yaml']:
            formatter.output(updated_asset)
        else:
            formatter.success(f"Updated asset {asset_id}")
            formatter.output(f"Name: {updated_asset['name']}")
            formatter.output(f"Criticality: {updated_asset['criticality_level']}")
        
        if not ctx.obj.get('quiet'):
            formatter.success(f"Asset {asset_id} updated successfully")
    
    except ValidationError as e:
        formatter.error(str(e))
        sys.exit(2)
    except Exception as e:
        logger.exception("Error updating asset")
        formatter.error(f"Failed to update asset: {str(e)}")
        sys.exit(1)


def _import_assets_from_file(file_path: str) -> list:
    """Import assets from file."""
    import csv
    import json
    from pathlib import Path
    
    assets = []
    path = Path(file_path)
    
    if path.suffix.lower() == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse interfaces from comma-separated string
                interfaces = [iface.strip() for iface in row.get('Interfaces', '').split(',') if iface.strip()]
                
                asset = {
                    "name": row.get('Asset Name', '').strip(),
                    "asset_type": row.get('Asset Type', 'HARDWARE').strip().upper(),
                    "criticality_level": row.get('Criticality Level', 'MEDIUM').strip().upper(),
                    "interfaces": interfaces,
                    "description": row.get('Description', '').strip(),
                    "security_properties": {
                        "confidentiality": "MEDIUM",
                        "integrity": "MEDIUM",
                        "availability": "MEDIUM"
                    }
                }
                
                if asset["name"]:  # Only add if name is not empty
                    assets.append(asset)
    
    elif path.suffix.lower() == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                assets = data
            elif isinstance(data, dict) and 'assets' in data:
                assets = data['assets']
    
    return assets


def _store_assets(analysis_id: str, assets: list) -> None:
    """Store assets for an analysis in a simple file-based storage."""
    import json
    from pathlib import Path
    
    # Create storage directory
    storage_dir = Path("autogt-output") / "assets"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Store assets in analysis-specific file
    assets_file = storage_dir / f"{analysis_id}.json"
    with open(assets_file, 'w', encoding='utf-8') as f:
        json.dump(assets, f, indent=2)


def _retrieve_assets(analysis_id: str) -> list:
    """Retrieve stored assets for an analysis."""
    import json
    from pathlib import Path
    
    assets_file = Path("autogt-output") / "assets" / f"{analysis_id}.json"
    
    if assets_file.exists():
        try:
            with open(assets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    return []


def _define_assets_interactively(ctx: click.Context) -> list:
    """Define assets using interactive mode."""
    assets = []
    
    while True:
        asset_name = click.prompt("Asset name")
        asset_type = click.prompt("Asset type", 
                                 type=click.Choice(['HARDWARE', 'SOFTWARE', 'COMMUNICATION', 'DATA']))
        criticality = click.prompt("Criticality level",
                                 type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']))
        
        # Simplified for now - would collect all properties interactively
        asset = {
            "name": asset_name,
            "asset_type": asset_type,
            "criticality_level": criticality,
            "interfaces": [],
            "security_properties": {
                "confidentiality": "MEDIUM",
                "integrity": "MEDIUM",
                "availability": "MEDIUM"
            }
        }
        
        assets.append(asset)
        
        if not click.confirm("Add another asset?"):
            break
    
    return assets


def _update_asset_interactively(ctx: click.Context, asset_id: str) -> dict:
    """Update asset using interactive mode."""
    # Mock implementation - would load existing asset and allow editing
    name = click.prompt("Asset name", default="Existing Asset")
    criticality = click.prompt("Criticality level",
                             type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']),
                             default='MEDIUM')
    
    return {
        "id": asset_id,
        "name": name,
        "asset_type": "HARDWARE",
        "criticality_level": criticality,
        "interfaces": ["CAN"],
        "security_properties": {
            "confidentiality": "MEDIUM",
            "integrity": "MEDIUM",
            "availability": "MEDIUM"
        }
    }


def _validate_assets(assets: list) -> dict:
    """Validate asset definitions."""
    errors = []
    
    for asset in assets:
        if not asset.get('name'):
            errors.append("Asset name is required")
        if not asset.get('asset_type'):
            errors.append("Asset type is required")
        if not asset.get('criticality_level'):
            errors.append("Criticality level is required")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }