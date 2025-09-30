"""Output formatting utilities for CLI commands.

Provides consistent output formatting across all CLI commands with support
for JSON, YAML, and table formats per contracts/cli.md global options.
"""

import json
import yaml
from typing import Any, Dict, List, Optional
from datetime import datetime
from tabulate import tabulate
import click


class OutputFormatter:
    """Handles output formatting for CLI commands."""
    
    def __init__(self, format_type: str = 'table', enable_output: bool = True):
        """Initialize formatter.
        
        Args:
            format_type: Output format ('json', 'yaml', 'table')
            enable_output: Whether to produce output (False for --quiet)
        """
        self.format_type = format_type.lower()
        self.enable_output = enable_output
        
        # Validate format type
        if self.format_type not in ['json', 'yaml', 'table']:
            raise ValueError(f"Invalid format type: {format_type}")
    
    def format_output(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data according to configured format.
        
        Args:
            data: Data to format (dict, list, or primitive)
            headers: Table headers for table format
            
        Returns:
            Formatted string output
        """
        if not self.enable_output:
            return ""
        
        if self.format_type == 'json':
            return self._format_json(data)
        elif self.format_type == 'yaml':
            return self._format_yaml(data)
        elif self.format_type == 'table':
            return self._format_table(data, headers)
        else:
            # Fallback to JSON
            return self._format_json(data)
    
    def output(self, data: Any, headers: Optional[List[str]] = None):
        """Format and output data to stdout.
        
        Args:
            data: Data to output
            headers: Table headers for table format
        """
        if not self.enable_output:
            return
        
        formatted = self.format_output(data, headers)
        if formatted:
            click.echo(formatted)
    
    def error(self, message: str):
        """Output error message to stderr.
        
        Args:
            message: Error message to output
        """
        click.echo(f"Error: {message}", err=True)
    
    def success(self, message: str):
        """Output success message.
        
        Args:
            message: Success message to output
        """
        if self.enable_output:
            click.echo(click.style(message, fg='green'))
    
    def warning(self, message: str):
        """Output warning message.
        
        Args:
            message: Warning message to output
        """
        if self.enable_output:
            click.echo(click.style(f"Warning: {message}", fg='yellow'))
    
    def _format_json(self, data: Any) -> str:
        """Format data as JSON."""
        try:
            return json.dumps(
                data,
                indent=2,
                default=self._json_serializer,
                ensure_ascii=False
            )
        except (TypeError, ValueError) as e:
            return json.dumps({"error": f"JSON serialization failed: {str(e)}"}, indent=2)
    
    def _format_yaml(self, data: Any) -> str:
        """Format data as YAML."""
        try:
            return yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                default=self._yaml_serializer
            )
        except (TypeError, ValueError) as e:
            return f"error: YAML serialization failed: {str(e)}\n"
    
    def _format_table(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data as table."""
        if data is None:
            return "No data available"
        
        # Handle different data types
        if isinstance(data, dict):
            if headers:
                # Use provided headers for dict
                rows = [[str(data.get(header, '')) for header in headers]]
            else:
                # Convert dict to key-value pairs
                rows = [[str(k), str(v)] for k, v in data.items()]
                headers = ['Key', 'Value']
        
        elif isinstance(data, list):
            if not data:
                return "No items found"
            
            if isinstance(data[0], dict):
                # List of dictionaries - use dict keys as headers
                if not headers:
                    headers = list(data[0].keys())
                rows = [[str(item.get(header, '')) for header in headers] for item in data]
            else:
                # List of primitives
                headers = headers or ['Value']
                rows = [[str(item)] for item in data]
        
        else:
            # Primitive value
            headers = headers or ['Value']
            rows = [[str(data)]]
        
        try:
            return tabulate(rows, headers=headers, tablefmt='grid')
        except Exception as e:
            return f"Table formatting failed: {str(e)}"
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def _yaml_serializer(self, obj: Any) -> Any:
        """Custom YAML serializer for datetime and other objects."""
        return self._json_serializer(obj)
    
    def format_analysis_list(self, analyses: List[Dict[str, Any]]) -> str:
        """Format analysis list with appropriate columns."""
        if not analyses:
            return self.format_output("No analyses found")
        
        if self.format_type == 'table':
            headers = ['Analysis ID', 'Name', 'Status', 'Step', 'Created']
            table_data = []
            for analysis in analyses:
                table_data.append([
                    analysis.get('analysis_id', '')[:8] + '...',  # Truncate ID
                    analysis.get('analysis_name', ''),
                    analysis.get('status', ''),
                    str(analysis.get('current_step', '')),
                    analysis.get('created_at', '')
                ])
            return self._format_table(table_data, headers)
        else:
            return self.format_output({"analyses": analyses, "total": len(analyses)})
    
    def format_analysis_detail(self, analysis: Dict[str, Any], detailed: bool = False) -> str:
        """Format detailed analysis information."""
        if self.format_type == 'table':
            # Create a structured table view
            basic_info = [
                ['ID', analysis.get('analysis_id', '')],
                ['Name', analysis.get('analysis_name', '')],
                ['Status', analysis.get('status', '')],
                ['Current Step', str(analysis.get('current_step', ''))],
                ['Vehicle Model', analysis.get('vehicle_model', 'Not specified')],
                ['Created', analysis.get('created_at', '')],
                ['Updated', analysis.get('updated_at', '')]
            ]
            
            result = "Analysis Details:\n"
            result += tabulate(basic_info, headers=['Property', 'Value'], tablefmt='grid')
            
            # Add steps information if available
            if 'steps' in analysis:
                result += "\n\nStep Progress:\n"
                steps_data = []
                for step_num, step_info in analysis['steps'].items():
                    steps_data.append([
                        step_num,
                        step_info.get('name', ''),
                        step_info.get('status', ''),
                        str(step_info.get('count', ''))
                    ])
                result += tabulate(steps_data, headers=['Step', 'Name', 'Status', 'Count'], tablefmt='grid')
            
            return result
        else:
            return self.format_output(analysis)
    
    def format_asset_list(self, assets: List[Dict[str, Any]]) -> str:
        """Format asset list with appropriate columns."""
        if not assets:
            return self.format_output("No assets found")
        
        if self.format_type == 'table':
            headers = ['ID', 'Name', 'Type', 'Criticality', 'Interfaces']
            table_data = []
            for asset in assets:
                interfaces = asset.get('interfaces', [])
                interface_str = ', '.join(interfaces) if interfaces else 'None'
                table_data.append([
                    asset.get('id', '')[:8] + '...',
                    asset.get('name', ''),
                    asset.get('asset_type', ''),
                    asset.get('criticality_level', ''),
                    interface_str
                ])
            return self._format_table(table_data, headers)
        else:
            return self.format_output({"assets": assets, "total": len(assets)})
    
    def format_threat_list(self, threats: List[Dict[str, Any]]) -> str:
        """Format threat list with appropriate columns.""" 
        if not threats:
            return self.format_output("No threats found")
        
        if self.format_type == 'table':
            headers = ['ID', 'Name', 'Category', 'Target Assets', 'Risk Level']
            table_data = []
            for threat in threats:
                target_assets = threat.get('target_assets', [])
                assets_str = ', '.join(target_assets[:2])  # Show first 2 assets
                if len(target_assets) > 2:
                    assets_str += f" (+{len(target_assets)-2} more)"
                
                table_data.append([
                    threat.get('id', '')[:8] + '...',
                    threat.get('name', ''),
                    threat.get('category', ''),
                    assets_str,
                    threat.get('risk_level', 'Not assessed')
                ])
            return self._format_table(table_data, headers)
        else:
            return self.format_output({"threats": threats, "total": len(threats)})
    
    def format_risk_list(self, risks: List[Dict[str, Any]]) -> str:
        """Format risk assessment list with appropriate columns."""
        if not risks:
            return self.format_output("No risks found")
        
        if self.format_type == 'table':
            headers = ['ID', 'Threat', 'Impact', 'Likelihood', 'Risk Level', 'Treatment']
            table_data = []
            for risk in risks:
                table_data.append([
                    risk.get('id', '')[:8] + '...',
                    risk.get('threat_name', ''),
                    risk.get('impact_rating', ''),
                    risk.get('likelihood_rating', ''),
                    risk.get('risk_level', ''),
                    risk.get('treatment_status', 'Not planned')
                ])
            return self._format_table(table_data, headers)
        else:
            return self.format_output({"risks": risks, "total": len(risks)})
    
    def format_progress(self, step: int, total: int, message: str = "") -> str:
        """Format progress indicator.
        
        Args:
            step: Current step number
            total: Total number of steps
            message: Optional progress message
            
        Returns:
            Formatted progress string
        """
        if not self.enable_output:
            return ""
        
        percentage = int((step / total) * 100)
        bar_length = 20
        filled_length = int((step / total) * bar_length)
        
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        progress_str = f"Progress: [{bar}] {percentage}% ({step}/{total})"
        
        if message:
            progress_str += f" - {message}"
        
        return progress_str


def get_formatter(ctx_or_format: any = 'table', enable_output: bool = True) -> OutputFormatter:
    """Factory function to create appropriate formatter instance.
    
    Args:
        ctx_or_format: Click context object or format string ('table', 'json', 'yaml')
        enable_output: Whether to enable output (for quiet mode)
    
    Returns:
        OutputFormatter: Configured formatter instance
    """
    # Handle Click context object
    if hasattr(ctx_or_format, 'obj') and ctx_or_format.obj:
        format_type = ctx_or_format.obj.get('format', 'table')
        quiet_mode = ctx_or_format.obj.get('quiet', False)
        return OutputFormatter(format_type, not quiet_mode)
    else:
        # Handle direct string format
        format_type = ctx_or_format if isinstance(ctx_or_format, str) else 'table'
        return OutputFormatter(format_type, enable_output)