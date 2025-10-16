"""Main CLI entry point for AutoGT TARA platform.

Reference: contracts/cli.md main command structure and global options
Provides Click-based command line interface for automotive cybersecurity analysis.
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional, Any

from ..lib.config import Config, ConfigError
from ..lib.exceptions import AutoGTError
from .commands import analysis, assets, threats, risks, export as export_cmd


# Version information
__version__ = "1.0.0"


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if verbose else '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    logger = logging.getLogger('autogt')
    logger.setLevel(level)
    logger.addHandler(console_handler)


def validate_config_file(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Optional[str]:
    """Validate config file path callback.
    
    Args:
        ctx: Click context
        param: Parameter being validated
        value: Config file path
        
    Returns:
        Validated config file path or None
        
    Raises:
        click.BadParameter: If config file is invalid
    """
    if value is None:
        return None
    
    config_path = Path(value)
    if not config_path.exists():
        raise click.BadParameter(f"Config file not found: {value}")
    
    if not config_path.is_file():
        raise click.BadParameter(f"Config path is not a file: {value}")
    
    return str(config_path.resolve())


def format_output(data: Any, output_format: str) -> str:
    """Format output data according to specified format.
    
    Args:
        data: Data to format
        output_format: Output format (json, yaml, table)
        
    Returns:
        Formatted string output
    """
    if output_format == "json":
        import json
        return json.dumps(data, indent=2, default=str)
    
    elif output_format == "yaml":
        import yaml
        return yaml.dump(data, default_flow_style=False)
    
    elif output_format == "table":
        # Simple table format for basic data structures
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Table format for list of dictionaries
            if not data:
                return "No data available"
            
            # Get headers
            headers = list(data[0].keys())
            
            # Calculate column widths
            widths = {h: len(str(h)) for h in headers}
            for row in data:
                for header in headers:
                    value_len = len(str(row.get(header, "")))
                    widths[header] = max(widths[header], value_len)
            
            # Build table
            lines = []
            
            # Header row
            header_row = " | ".join(str(h).ljust(widths[h]) for h in headers)
            lines.append(header_row)
            
            # Separator row
            separator = " | ".join("-" * widths[h] for h in headers)
            lines.append(separator)
            
            # Data rows
            for row in data:
                data_row = " | ".join(
                    str(row.get(h, "")).ljust(widths[h]) for h in headers
                )
                lines.append(data_row)
            
            return "\n".join(lines)
        
        elif isinstance(data, dict):
            # Simple key-value format for dictionaries
            max_key_length = max(len(str(k)) for k in data.keys()) if data else 0
            lines = []
            for key, value in data.items():
                lines.append(f"{str(key).ljust(max_key_length)} : {value}")
            return "\n".join(lines)
        
        else:
            # Fallback to string representation
            return str(data)
    
    else:
        raise click.BadParameter(f"Unsupported output format: {output_format}")


class AutoGTGroup(click.Group):
    """Custom Click group with enhanced error handling."""
    
    def invoke(self, ctx: click.Context) -> Any:
        """Invoke command with error handling."""
        # Skip custom error handling for help command
        if '--help' in sys.argv or '-h' in sys.argv:
            return super().invoke(ctx)
            
        try:
            return super().invoke(ctx)
        except AutoGTError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except SystemExit as e:
            # Pass through SystemExit unchanged to support --help properly
            raise
        except Exception as e:
            if ctx.find_root().params.get('verbose'):
                import traceback
                click.echo(f"Unexpected error: {e}", err=True)
                click.echo(traceback.format_exc(), err=True)
            else:
                click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)


@click.group(cls=AutoGTGroup, invoke_without_command=True)
@click.option(
    '--config', '-c',
    type=str,
    callback=validate_config_file,
    help='Path to configuration file'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--format', '-f',
    'output_format',
    type=click.Choice(['json', 'yaml', 'table'], case_sensitive=False),
    default='table',
    help='Output format (default: table)'
)
@click.version_option(version=__version__, prog_name='autogt')
@click.pass_context
def cli(
    ctx: click.Context, 
    config: Optional[str], 
    verbose: bool, 
    output_format: str
) -> None:
    """AutoGT TARA Platform - Automotive Cybersecurity Threat Analysis and Risk Assessment.
    
    A comprehensive platform for conducting automotive cybersecurity analysis
    following ISO/SAE 21434 standards. Supports 8-step TARA methodology
    with AI-powered threat identification and risk assessment.
    
    Examples:
    
        # Create new analysis from Excel file
        autogt analysis create --file vehicle-data.xlsx --name "Model X" --vehicle "Tesla Model X"
        
        # View analysis status
        autogt analysis show analysis-uuid
        
        # Export analysis results
        autogt export analysis-uuid --format excel
        
        # Validate analysis against ISO standards
        autogt validate analysis-uuid
    
    For command-specific help, use:
        autogt COMMAND --help
    """
    # Initialize context object
    if ctx.obj is None:
        ctx.obj = {}
    
    # Setup logging first
    setup_logging(verbose)
    logger = logging.getLogger('autogt.cli')
    logger.debug(f"AutoGT CLI v{__version__} starting")
    
    # Store global options in context
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['output_format'] = output_format
    ctx.obj['format_output'] = format_output
    
    # If help is requested, skip configuration loading
    if '--help' in sys.argv or '-h' in sys.argv:
        # Set a placeholder config instance to avoid errors in subcommands
        ctx.obj['config_instance'] = None
        return
    
    # Load configuration
    try:
        config_instance = Config(config_file=config)
        ctx.obj['config_instance'] = config_instance
        logger.debug(f"Configuration loaded from: {config or 'default locations'}")
    
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        if not ctx.invoked_subcommand:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(1)
        # Store error for subcommands to handle
        ctx.obj['config_error'] = str(e)
    
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return


# Register command groups
cli.add_command(analysis.analysis)
cli.add_command(assets.assets)
cli.add_command(threats.threats) 
cli.add_command(risks.risks)
cli.add_command(export_cmd.export)
cli.add_command(export_cmd.validate)


def main() -> None:
    """Main entry point for the autogt command."""
    cli()


if __name__ == '__main__':
    main()