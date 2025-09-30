"""Export endpoints for AutoGT TARA Platform API.

Reference: contracts/api.yaml lines 147-190 - export endpoints
Provides REST endpoints for exporting analysis results in various formats.
"""

import logging
import json
from typing import Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path
import tempfile

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class ExportRequest(BaseModel):
    """Request model for analysis export."""
    format: str = "json"
    include_steps: Optional[str] = None
    template_path: Optional[str] = None


class ExportResponse(BaseModel):
    """Response model for export operations."""
    export_file: str
    file_size_bytes: int
    format: str
    records_exported: dict


# Export endpoints
@router.get("/{analysis_id}")
async def export_analysis(
    analysis_id: str,
    format: str = Query("json", regex="^(json|excel)$"),
    include_steps: Optional[str] = Query(None),
    template: Optional[str] = Query(None)
):
    """Export analysis results to structured formats.
    
    Generate complete analysis data with all 8 TARA steps, ISO/SAE 21434
    traceability information, and audit trail with compliance artifacts.
    
    Supports JSON and Excel formats with optional step filtering and templates.
    """
    try:
        # Validate UUID format
        try:
            UUID(analysis_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis ID format"
            )
        
        # Parse include_steps if provided
        steps_to_include = None
        if include_steps:
            try:
                steps_to_include = [int(s.strip()) for s in include_steps.split(',')]
                if not all(1 <= step <= 8 for step in steps_to_include):
                    raise ValueError("Steps must be between 1 and 8")
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid include_steps format: {str(e)}"
                )
        
        # Mock export data - will be replaced with real service integration
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "export_format": format,
                "analysis_id": analysis_id,
                "autogt_version": "1.0.0",
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
        
        # Filter steps if requested
        if steps_to_include:
            filtered_steps = {
                str(step): export_data["tara_steps"][str(step)]
                for step in steps_to_include
                if str(step) in export_data["tara_steps"]
            }
            export_data["tara_steps"] = filtered_steps
        
        # Generate export file
        if format == "json":
            # Create temporary JSON file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                json.dump(export_data, temp_file, indent=2, default=str)
                temp_path = temp_file.name
            
            # Return file response
            filename = f"tara_export_{analysis_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return FileResponse(
                path=temp_path,
                media_type="application/json",
                filename=filename,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Export-Format": format,
                    "X-Analysis-ID": analysis_id
                }
            )
        
        elif format == "excel":
            # Excel export would be implemented here using openpyxl or xlsxwriter
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Excel export not yet implemented"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error exporting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analysis"
        )


@router.post("/{analysis_id}")
async def export_analysis_with_config(analysis_id: str, export_config: ExportRequest):
    """Export analysis with detailed configuration.
    
    Alternative endpoint that accepts configuration in request body for
    more complex export scenarios with custom templates and options.
    """
    try:
        # Validate UUID format
        try:
            UUID(analysis_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis ID format"
            )
        
        # Redirect to GET endpoint with query parameters
        return await export_analysis(
            analysis_id=analysis_id,
            format=export_config.format,
            include_steps=export_config.include_steps,
            template=export_config.template_path
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in export configuration for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process export configuration"
        )


@router.get("/{analysis_id}/status")
async def get_export_status(analysis_id: str):
    """Get export status for long-running operations.
    
    Check the status of ongoing export operations for large analyses
    that may take time to process.
    """
    try:
        # Validate UUID format
        try:
            UUID(analysis_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis ID format"
            )
        
        # Mock export status - will be replaced with real service integration
        export_status = {
            "analysis_id": analysis_id,
            "export_status": "completed",
            "progress_percentage": 100,
            "estimated_completion": None,
            "available_formats": ["json", "excel"],
            "last_export": {
                "timestamp": "2025-09-30T11:00:00Z",
                "format": "json",
                "file_size_bytes": 2048576
            }
        }
        
        return export_status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting export status for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export status"
        )


@router.delete("/{analysis_id}/cache")
async def clear_export_cache(analysis_id: str):
    """Clear cached export files for an analysis.
    
    Remove temporary export files and cached data to free up storage space.
    """
    try:
        # Validate UUID format  
        try:
            UUID(analysis_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis ID format"
            )
        
        # Mock cache clearing - will be replaced with real implementation
        logger.info(f"Cleared export cache for analysis {analysis_id}")
        
        return {
            "analysis_id": analysis_id,
            "cache_cleared": True,
            "files_removed": 3,
            "space_freed_bytes": 5242880
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error clearing export cache for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear export cache"
        )