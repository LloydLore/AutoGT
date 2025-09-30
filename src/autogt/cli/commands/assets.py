"""Assets command group for AutoGT CLI.

Reference: contracts/cli.md assets define command
Handles asset definition and management for TARA analyses.
"""

import click
import logging
import csv
import json
from typing import Optional, Dict, Any
from uuid import UUID

from ...lib.exceptions import AutoGTError
from ...services.database import DatabaseService
from ...models.asset import Asset, AssetType, CriticalityLevel
from ...models.analysis import TaraAnalysis
from ...lib.config import Config


logger = logging.getLogger('autogt.cli.assets')


@click.group()
def assets():
    """Manage assets for TARA analyses."""
    pass


@assets.command()
@click.argument('analysis_id', required=True)
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help='Use interactive mode for asset definition'
)
@click.option(
    '--file', '-f',
    'input_file',
    type=click.Path(exists=True),
    help='Input file with asset definitions'
)
@click.pass_context
def define(
    ctx: click.Context,
    analysis_id: str,
    interactive: bool,
    input_file: Optional[str]
) -> None:
    """Define assets for a TARA analysis.
    
    Assets can be defined interactively or loaded from a file.
    Interactive mode provides guided prompts for asset definition.
    
    Examples:
    
        # Interactive asset definition
        autogt assets define abc12345 --interactive
        
        # Load assets from file
        autogt assets define abc12345 --file assets.csv
    """
    try:
        if interactive:
            click.echo("Starting interactive asset definition...")
            _interactive_asset_definition(ctx, analysis_id)
        elif input_file:
            click.echo(f"Loading assets from file: {input_file}")
            _load_assets_from_file(ctx, analysis_id, input_file)
        else:
            raise AutoGTError("Either --interactive or --file option must be specified")
    
    except Exception as e:
        logger.error(f"Asset definition failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to define assets: {e}")


def _interactive_asset_definition(ctx: click.Context, analysis_id: str) -> None:
    """Handle interactive asset definition."""
    try:
        # Get services
        config = ctx.obj.get('config_instance')
        if not config:
            config = Config()
        
        db_service = DatabaseService(database_url=config.get_database_url())
        
        # Verify analysis exists
        with db_service.get_session() as session:
            resolved_id = _resolve_analysis_id(session, analysis_id)
            analysis = session.query(TaraAnalysis).filter(
                TaraAnalysis.id == resolved_id
            ).first()
            
            if not analysis:
                raise AutoGTError(f"Analysis {analysis_id} not found")
            
            click.echo(f"\n🔧 Interactive Asset Definition for: {analysis.analysis_name}")
            click.echo("=" * 60)
            click.echo("Define assets for your TARA analysis. Press Ctrl+C to finish.\n")
            
            assets_added = 0
            
            while True:
                try:
                    # Asset name
                    name = click.prompt("Asset name", type=str)
                    if not name.strip():
                        continue
                        
                    # Asset type
                    click.echo("\nAsset types: HARDWARE, SOFTWARE, COMMUNICATION, DATA, ECU")
                    asset_type_str = click.prompt("Asset type", type=str).upper()
                    
                    try:
                        asset_type = AssetType(asset_type_str)
                    except ValueError:
                        click.echo(f"Invalid asset type. Using HARDWARE as default.")
                        asset_type = AssetType.HARDWARE
                    
                    # Criticality level
                    click.echo("\nCriticality levels: LOW, MEDIUM, HIGH, VERY_HIGH")
                    criticality_str = click.prompt("Criticality level", type=str).upper()
                    
                    try:
                        criticality = CriticalityLevel(criticality_str)
                    except ValueError:
                        click.echo(f"Invalid criticality level. Using MEDIUM as default.")
                        criticality = CriticalityLevel.MEDIUM
                    
                    # Optional description
                    description = click.prompt("Description (optional)", default="", show_default=False)
                    
                    # Interfaces (optional)
                    interfaces_str = click.prompt("Interfaces (comma-separated, optional)", default="", show_default=False)
                    interfaces = [i.strip() for i in interfaces_str.split(",")] if interfaces_str else []
                    
                    # Create asset
                    asset = Asset(
                        name=name.strip(),
                        asset_type=asset_type,
                        criticality_level=criticality,
                        interfaces=interfaces,
                        data_flows=[],
                        security_properties={"description": description} if description else {},
                        iso_section="21434-15.6",  # Default ISO section
                        analysis_id=resolved_id
                    )
                    
                    # Save to database
                    session.add(asset)
                    session.commit()
                    assets_added += 1
                    
                    click.echo(f"✅ Asset '{name}' added successfully!\n")
                    
                    # Continue?
                    if not click.confirm("Add another asset?"):
                        break
                        
                except KeyboardInterrupt:
                    click.echo("\n\n⚠️  Asset definition cancelled by user")
                    break
                except Exception as e:
                    click.echo(f"❌ Error adding asset: {e}")
                    if not click.confirm("Continue with next asset?"):
                        break
            
            click.echo(f"\n🎉 Interactive asset definition completed!")
            click.echo(f"📊 Total assets added: {assets_added}")
            
            if assets_added > 0:
                click.echo(f"\n💡 Next steps:")
                click.echo(f"   • Run: autogt threats identify {analysis_id}")
                click.echo(f"   • Run: autogt risks calculate {analysis_id}")
                
    except Exception as e:
        logger.error(f"Interactive asset definition failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to define assets interactively: {e}")


def _load_assets_from_file(ctx: click.Context, analysis_id: str, file_path: str) -> None:
    """Load assets from input file (CSV or JSON)."""
    try:
        # Get services
        config = ctx.obj.get('config_instance')
        if not config:
            config = Config()
        
        db_service = DatabaseService(database_url=config.get_database_url())
        
        # Verify analysis exists
        with db_service.get_session() as session:
            resolved_id = _resolve_analysis_id(session, analysis_id)
            analysis = session.query(TaraAnalysis).filter(
                TaraAnalysis.id == resolved_id
            ).first()
            
            if not analysis:
                raise AutoGTError(f"Analysis {analysis_id} not found")
            
            click.echo(f"📁 Loading assets from: {file_path}")
            click.echo(f"🎯 Target analysis: {analysis.analysis_name}\n")
            
            # Determine file format
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'csv':
                assets_data = _load_csv_assets(file_path)
            elif file_extension == 'json':
                assets_data = _load_json_assets(file_path)
            else:
                raise AutoGTError(f"Unsupported file format: {file_extension}. Supported: csv, json")
            
            # Process and save assets
            assets_added = 0
            assets_skipped = 0
            
            for asset_data in assets_data:
                try:
                    # Validate required fields
                    if not asset_data.get('name'):
                        click.echo(f"⚠️  Skipping asset without name")
                        assets_skipped += 1
                        continue
                    
                    # Check if asset already exists
                    existing = session.query(Asset).filter(
                        Asset.analysis_id == resolved_id,
                        Asset.name == asset_data['name']
                    ).first()
                    
                    if existing:
                        click.echo(f"⚠️  Asset '{asset_data['name']}' already exists, skipping")
                        assets_skipped += 1
                        continue
                    
                    # Parse asset type
                    try:
                        asset_type = AssetType(asset_data.get('type', 'HARDWARE').upper())
                    except ValueError:
                        asset_type = AssetType.HARDWARE
                        click.echo(f"⚠️  Invalid asset type for '{asset_data['name']}', using HARDWARE")
                    
                    # Parse criticality
                    try:
                        criticality = CriticalityLevel(asset_data.get('criticality', 'MEDIUM').upper())
                    except ValueError:
                        criticality = CriticalityLevel.MEDIUM
                        click.echo(f"⚠️  Invalid criticality for '{asset_data['name']}', using MEDIUM")
                    
                    # Create asset
                    asset = Asset(
                        name=asset_data['name'].strip(),
                        asset_type=asset_type,
                        criticality_level=criticality,
                        interfaces=asset_data.get('interfaces', []),
                        data_flows=asset_data.get('data_flows', []),
                        security_properties=asset_data.get('security_properties', {
                            'description': asset_data.get('description', '')
                        }),
                        iso_section=asset_data.get('iso_section', '21434-15.6'),
                        analysis_id=resolved_id
                    )
                    
                    # Save asset
                    session.add(asset)
                    assets_added += 1
                    click.echo(f"✅ Asset '{asset_data['name']}' added successfully")
                    
                except Exception as e:
                    click.echo(f"❌ Error processing asset '{asset_data.get('name', 'unknown')}': {e}")
                    assets_skipped += 1
                    continue
            
            # Commit all changes
            session.commit()
            
            # Summary
            click.echo(f"\n🎉 Asset loading completed!")
            click.echo(f"📊 Assets added: {assets_added}")
            click.echo(f"⚠️  Assets skipped: {assets_skipped}")
            
            if assets_added > 0:
                click.echo(f"\n💡 Next steps:")
                click.echo(f"   • Run: autogt threats identify {analysis_id}")
                click.echo(f"   • Run: autogt risks calculate {analysis_id}")
                
    except Exception as e:
        logger.error(f"File-based asset loading failed: {e}", exc_info=True)
        raise AutoGTError(f"Failed to load assets from file: {e}")


def _load_csv_assets(file_path: str) -> list:
    """Load assets from CSV file."""
    assets = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Detect delimiter
        sample = f.read(1024)
        f.seek(0)
        
        # Try common delimiters
        delimiter = ','
        if ';' in sample and sample.count(';') > sample.count(','):
            delimiter = ';'
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        for row in reader:
            # Convert CSV row to asset data
            asset_data = {
                'name': row.get('name', ''),
                'type': row.get('type', 'HARDWARE'),
                'criticality': row.get('criticality', 'MEDIUM'),
                'description': row.get('description', ''),
                'iso_section': row.get('iso_section', '21434-15.6')
            }
            
            # Parse interfaces (comma-separated in CSV)
            interfaces_str = row.get('interfaces', '')
            if interfaces_str:
                asset_data['interfaces'] = [i.strip() for i in interfaces_str.split(',')]
            
            # Parse data flows (comma-separated in CSV)
            data_flows_str = row.get('data_flows', '')
            if data_flows_str:
                asset_data['data_flows'] = [d.strip() for d in data_flows_str.split(',')]
            
            assets.append(asset_data)
    
    return assets


def _resolve_analysis_id(session, analysis_id: str) -> UUID:
    """Resolve partial analysis ID to full UUID."""
    # Remove dashes and normalize
    normalized_id = analysis_id.replace('-', '')
    
    if len(normalized_id) < 32:  # Partial ID
        # Convert to UUID format for LIKE query
        from sqlalchemy import text
        result = session.execute(
            text("SELECT id FROM tara_analyses WHERE REPLACE(CAST(id as TEXT), '-', '') LIKE :partial_id || '%'"),
            {"partial_id": normalized_id}
        ).first()
        
        if not result:
            raise AutoGTError(f"No analysis found matching ID: {analysis_id}")
        
        return result[0]
    else:
        # Try to construct full UUID
        try:
            return UUID(analysis_id)
        except ValueError:
            # Try with dashes if needed
            if len(normalized_id) == 32:
                formatted_uuid = f"{normalized_id[:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:]}"
                return UUID(formatted_uuid)
            else:
                raise AutoGTError(f"Invalid analysis ID format: {analysis_id}")


def _load_json_assets(file_path: str) -> list:
    """Load assets from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'assets' in data:
        return data['assets']
    else:
        raise AutoGTError("Invalid JSON format. Expected list of assets or object with 'assets' key")


def _resolve_analysis_id(session, analysis_id: str) -> UUID:
    """Resolve partial analysis ID to full UUID."""
    # Remove dashes and normalize
    normalized_id = analysis_id.replace('-', '')
    
    if len(normalized_id) < 32:  # Partial ID
        # Convert to UUID format for LIKE query
        from sqlalchemy import text
        result = session.execute(
            text("SELECT id FROM tara_analyses WHERE REPLACE(CAST(id as TEXT), '-', '') LIKE :partial_id || '%'"),
            {"partial_id": normalized_id}
        ).first()
        
        if not result:
            raise AutoGTError(f"No analysis found matching ID: {analysis_id}")
        
        return result[0]
    else:
        # Try to construct full UUID
        try:
            return UUID(analysis_id)
        except ValueError:
            # Try with dashes if needed
            if len(normalized_id) == 32:
                formatted_uuid = f"{normalized_id[:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:]}"
                return UUID(formatted_uuid)
            else:
                raise AutoGTError(f"Invalid analysis ID format: {analysis_id}")