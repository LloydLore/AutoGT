"""TARA Analysis model implementation per data-model.md specification lines 196-225."""

from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Text, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel, ISO21434Mixin
from .enums import AnalysisStatus, ReviewStatus


class TaraAnalysis(BaseModel, ISO21434Mixin):
    """Represents complete TARA (Threat Analysis and Risk Assessment) session.
    
    Per data-model.md TaraAnalysis entity specification as root container for
    all cybersecurity analysis artifacts with workflow management and reporting.
    """
    
    __tablename__ = "tara_analyses"
    
    # Core analysis identification
    name = Column(String(255), nullable=False,
                 comment="Human-readable analysis name (e.g., 'Model X Infotainment TARA')")
    description = Column(Text, nullable=True,
                        comment="Detailed analysis scope and objectives")
    
    # Analysis context and scope
    vehicle_model = Column(String(100), nullable=True,
                          comment="Target vehicle model or platform")
    system_boundary = Column(Text, nullable=True,
                           comment="Definition of analysis scope and boundaries")
    analysis_objectives = Column(JSON, nullable=True,
                               comment="List of specific analysis goals")
    
    # Workflow management per data-model.md
    status = Column(SQLEnum(AnalysisStatus), 
                   default=AnalysisStatus.INITIATED, nullable=False,
                   comment="Current analysis workflow state")
    review_status = Column(SQLEnum(ReviewStatus), 
                          default=ReviewStatus.IDENTIFIED, nullable=False,
                          comment="Manual review and approval state")
    
    # Analysis timeline tracking
    start_date = Column(String(20), nullable=False,
                       comment="Analysis initiation date")
    target_completion_date = Column(String(20), nullable=True,
                              comment="Planned completion date")
    actual_completion_date = Column(String(20), nullable=True,
                                  comment="Actual completion date")
    
    # Input documentation management
    source_documents = Column(JSON, nullable=True,
                            comment="List of source documents analyzed")
    document_versions = Column(JSON, nullable=True,
                             comment="Version tracking for source documents")
    
    # Analysis methodology configuration
    analysis_approach = Column(String(100), nullable=False, default='STRIDE_AUTOMATED',
                             comment="Analysis methodology used")
    ai_models_used = Column(JSON, nullable=True,
                          comment="AI models and versions employed")
    analysis_parameters = Column(JSON, nullable=True,
                               comment="Configuration parameters for analysis")
    
    # Quality and validation tracking
    validation_criteria = Column(JSON, nullable=True,
                               comment="Criteria for analysis validation")
    quality_metrics = Column(JSON, nullable=True,
                           comment="Quality assessment results")
    is_validated = Column(Boolean, default=False,
                         comment="Whether analysis has passed validation")
    
    # Reporting and output configuration
    report_format = Column(String(50), nullable=False, default='JSON',
                          comment="Output format for analysis results")
    export_settings = Column(JSON, nullable=True,
                           comment="Configuration for data export")
    
    # Regulatory compliance tracking
    compliance_frameworks = Column(JSON, nullable=True,
                                 comment="Applicable regulatory frameworks")
    certification_requirements = Column(JSON, nullable=True,
                                      comment="Certification and approval requirements")
    
    # Relationships per data-model.md relationship specifications
    assets = relationship("Asset", back_populates="analysis", cascade="all, delete-orphan")
    threat_scenarios = relationship("ThreatScenario", back_populates="analysis", cascade="all, delete-orphan")
    impact_ratings = relationship("ImpactRating", back_populates="analysis", cascade="all, delete-orphan")
    risk_values = relationship("RiskValue", back_populates="analysis", cascade="all, delete-orphan")
    controls = relationship("SecurityControl", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TaraAnalysis(id={self.id}, name='{self.name}', status={self.status}, assets={len(self.assets) if self.assets else 0})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate TARA analysis per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Analysis name must be descriptive
        if not self.name or not self.name.strip():
            errors.append("Analysis name must be non-empty")
        if self.name and len(self.name.strip()) < 5:
            errors.append("Analysis name should be descriptive (minimum 5 characters)")
            
        # System boundary must be defined for meaningful analysis
        if not self.system_boundary or len(self.system_boundary.strip()) < 20:
            errors.append("System boundary must be clearly defined (minimum 20 characters)")
            
        # Start date validation
        if not self.start_date:
            errors.append("Analysis start date is required")
            
        # Date consistency validation
        if self.target_completion_date and self.start_date:
            # Would validate date format and ordering in real implementation
            pass
            
        # Source documents validation
        if not self.source_documents or len(self.source_documents) == 0:
            errors.append("At least one source document must be provided")
            
        # Completion validation
        if self.status == AnalysisStatus.COMPLETED and not self.actual_completion_date:
            errors.append("Completed analysis must have actual completion date")
            
        # Asset count validation for meaningful analysis
        if hasattr(self, 'assets') and self.assets is not None:
            if len(self.assets) == 0 and self.status != AnalysisStatus.INITIATED:
                errors.append("Analysis must identify at least one asset")
                
        return len(errors) == 0, errors
    
    def transition_status(self, new_status: AnalysisStatus, reason: str = None) -> bool:
        """Handle analysis status transitions per data-model.md workflow rules.
        
        Valid transitions:
        - INITIATED → IN_PROGRESS (begin analysis)
        - IN_PROGRESS → UNDER_REVIEW (analysis complete, awaiting review)
        - UNDER_REVIEW → APPROVED / REQUIRES_REVISION (review decision)
        - APPROVED → COMPLETED (final approval)
        - * → FAILED (can fail from any state)
        """
        valid_transitions = {
            AnalysisStatus.INITIATED: [AnalysisStatus.IN_PROGRESS, AnalysisStatus.FAILED],
            AnalysisStatus.IN_PROGRESS: [AnalysisStatus.UNDER_REVIEW, AnalysisStatus.FAILED],
            AnalysisStatus.UNDER_REVIEW: [AnalysisStatus.APPROVED, AnalysisStatus.REQUIRES_REVISION, AnalysisStatus.FAILED],
            AnalysisStatus.APPROVED: [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED],
            AnalysisStatus.REQUIRES_REVISION: [AnalysisStatus.IN_PROGRESS, AnalysisStatus.FAILED],
            AnalysisStatus.COMPLETED: [],  # Terminal state
            AnalysisStatus.FAILED: [AnalysisStatus.INITIATED]  # Can restart
        }
        
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            
            # Set completion date for terminal states
            if new_status == AnalysisStatus.COMPLETED and not self.actual_completion_date:
                self.actual_completion_date = datetime.now().strftime('%Y-%m-%d')
                
            return True
        return False
    
    def calculate_analysis_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive analysis metrics and statistics."""
        if not hasattr(self, 'assets') or self.assets is None:
            return {}
            
        metrics = {
            'total_assets': len(self.assets),
            'total_threats': len(self.threat_scenarios) if self.threat_scenarios else 0,
            'total_risks': len(self.risk_values) if self.risk_values else 0,
            'total_controls': len(self.controls) if self.controls else 0
        }
        
        # Risk level distribution
        if self.risk_values:
            risk_levels = {}
            total_risk_score = 0
            for risk in self.risk_values:
                level = risk.risk_level.value
                risk_levels[level] = risk_levels.get(level, 0) + 1
                total_risk_score += risk.risk_score
                
            metrics['risk_distribution'] = risk_levels
            metrics['average_risk_score'] = total_risk_score / len(self.risk_values)
        
        # Asset criticality distribution
        if self.assets:
            criticality_levels = {}
            for asset in self.assets:
                level = asset.criticality_level.value
                criticality_levels[level] = criticality_levels.get(level, 0) + 1
            metrics['criticality_distribution'] = criticality_levels
        
        # Control effectiveness assessment
        if self.controls:
            total_effectiveness = 0
            implemented_controls = 0
            for control in self.controls:
                if control.implementation_status.value in ['IMPLEMENTED', 'VERIFIED']:
                    implemented_controls += 1
                    total_effectiveness += control.risk_reduction_factor
                    
            metrics['implemented_controls'] = implemented_controls
            metrics['control_implementation_rate'] = implemented_controls / len(self.controls)
            if implemented_controls > 0:
                metrics['average_control_effectiveness'] = total_effectiveness / implemented_controls
        
        return metrics
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary for reporting and dashboard display."""
        metrics = self.calculate_analysis_metrics()
        
        # Risk assessment summary
        high_risk_count = metrics.get('risk_distribution', {}).get('HIGH', 0) + \
                         metrics.get('risk_distribution', {}).get('CRITICAL', 0)
        
        # Control gap analysis
        total_controls = metrics.get('total_controls', 0)
        implemented_controls = metrics.get('implemented_controls', 0)
        control_gap = total_controls - implemented_controls
        
        return {
            'analysis_name': self.name,
            'vehicle_model': self.vehicle_model,
            'status': self.status.value,
            'completion_percentage': self.calculate_completion_percentage(),
            'key_findings': {
                'assets_analyzed': metrics.get('total_assets', 0),
                'threats_identified': metrics.get('total_threats', 0),
                'high_risk_issues': high_risk_count,
                'control_coverage': f"{implemented_controls}/{total_controls}",
                'average_risk_score': round(metrics.get('average_risk_score', 0), 2)
            },
            'recommendations': self.generate_recommendations(metrics),
            'compliance_status': self.assess_compliance_status()
        }
    
    def calculate_completion_percentage(self) -> float:
        """Calculate analysis completion percentage based on workflow milestones."""
        status_weights = {
            AnalysisStatus.INITIATED: 0.0,
            AnalysisStatus.IN_PROGRESS: 0.5,
            AnalysisStatus.UNDER_REVIEW: 0.8,
            AnalysisStatus.APPROVED: 0.9,
            AnalysisStatus.COMPLETED: 1.0,
            AnalysisStatus.REQUIRES_REVISION: 0.6,
            AnalysisStatus.FAILED: 0.0
        }
        
        return status_weights.get(self.status, 0.0) * 100
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis results."""
        recommendations = []
        
        # High-risk issue recommendations
        high_risk_count = metrics.get('risk_distribution', {}).get('HIGH', 0) + \
                         metrics.get('risk_distribution', {}).get('CRITICAL', 0)
        if high_risk_count > 0:
            recommendations.append(f"Address {high_risk_count} high/critical risk items immediately")
            
        # Control implementation recommendations
        control_rate = metrics.get('control_implementation_rate', 0)
        if control_rate < 0.8:
            recommendations.append("Improve security control implementation rate (currently {:.0%})".format(control_rate))
            
        # Asset coverage recommendations
        total_assets = metrics.get('total_assets', 0)
        total_threats = metrics.get('total_threats', 0)
        if total_assets > 0 and total_threats / total_assets < 2:
            recommendations.append("Consider more comprehensive threat identification")
            
        return recommendations
    
    def assess_compliance_status(self) -> str:
        """Assess compliance with regulatory frameworks."""
        if not self.compliance_frameworks:
            return 'NOT_ASSESSED'
            
        # Simplified compliance assessment
        required_elements = ['asset_identification', 'threat_analysis', 'risk_assessment', 'risk_treatment']
        completed_elements = 0
        
        if hasattr(self, 'assets') and self.assets and len(self.assets) > 0:
            completed_elements += 1
        if hasattr(self, 'threat_scenarios') and self.threat_scenarios and len(self.threat_scenarios) > 0:
            completed_elements += 1
        if hasattr(self, 'risk_values') and self.risk_values and len(self.risk_values) > 0:
            completed_elements += 1
        if hasattr(self, 'controls') and self.controls and len(self.controls) > 0:
            completed_elements += 1
            
        compliance_percentage = completed_elements / len(required_elements)
        
        if compliance_percentage >= 1.0:
            return 'COMPLIANT'
        elif compliance_percentage >= 0.75:
            return 'MOSTLY_COMPLIANT'
        elif compliance_percentage >= 0.5:
            return 'PARTIALLY_COMPLIANT'
        else:
            return 'NON_COMPLIANT'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with calculated fields and relationships."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.status:
            result['status'] = self.status.value
        if self.review_status:
            result['review_status'] = self.review_status.value
            
        # Include calculated fields
        result['metrics'] = self.calculate_analysis_metrics()
        result['executive_summary'] = self.generate_executive_summary()
        result['completion_percentage'] = self.calculate_completion_percentage()
        
        return result
    
    @classmethod
    def create_new_analysis(cls, name: str, vehicle_model: str, system_boundary: str,
                          source_documents: List[str], analysis_approach: str = 'STRIDE_AUTOMATED') -> 'TaraAnalysis':
        """Create new TARA analysis with proper initialization.
        
        Args:
            name: Analysis name
            vehicle_model: Target vehicle/system
            system_boundary: Analysis scope definition
            source_documents: List of input documents
            analysis_approach: Analysis methodology
        """
        return cls(
            name=name,
            vehicle_model=vehicle_model,
            system_boundary=system_boundary,
            source_documents=source_documents,
            analysis_approach=analysis_approach,
            start_date=datetime.now().strftime('%Y-%m-%d'),
            compliance_frameworks=['ISO_21434', 'UNECE_WP29'],
            analysis_objectives=[
                'Identify cybersecurity assets',
                'Analyze threat scenarios',
                'Assess cybersecurity risks',
                'Define security controls'
            ],
            iso_section='5.4.1'  # ISO/SAE 21434 cybersecurity analysis section
        )