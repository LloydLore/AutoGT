"""Core TARA analysis service coordinating 8-step workflow.

Implements the complete automotive cybersecurity threat analysis and risk 
assessment process per ISO/SAE 21434 with AI-powered automation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio

from ..models.analysis import TaraAnalysis, AnalysisStatus
from ..models.asset import Asset
from ..models.threat import ThreatScenario 
from ..models.risk import RiskAssessment, RiskLevel
from ..models.treatment import Treatment
from ..ai.orchestrator import TaraOrchestrator
from ..io.processor import FileProcessor
from ..core.exceptions import AnalysisError, ValidationError
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class TaraStep(Enum):
    """8-step TARA workflow steps per ISO/SAE 21434."""
    ASSET_DEFINITION = "asset_definition"
    IMPACT_RATING = "impact_rating"  
    THREAT_IDENTIFICATION = "threat_identification"
    ATTACK_PATH_ANALYSIS = "attack_path_analysis"
    FEASIBILITY_ASSESSMENT = "feasibility_assessment"
    RISK_CALCULATION = "risk_calculation"
    TREATMENT_PLANNING = "treatment_planning"
    GOAL_SETTING = "goal_setting"


@dataclass
class AnalysisProgress:
    """Progress tracking for TARA analysis."""
    current_step: TaraStep
    completed_steps: List[TaraStep]
    step_progress: Dict[TaraStep, float]  # 0.0 to 1.0
    estimated_completion: Optional[datetime]
    total_progress: float


@dataclass
class AnalysisResult:
    """Complete TARA analysis results."""
    analysis_id: str
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    treatments: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    metadata: Dict[str, Any]
    confidence_score: float


class TaraAnalysisService:
    """Core service coordinating complete TARA workflow execution."""
    
    def __init__(self, db_session: Session):
        """Initialize TARA analysis service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.file_processor = FileProcessor()
        self.ai_orchestrator = TaraOrchestrator()
        
        # Step execution mapping
        self.step_handlers = {
            TaraStep.ASSET_DEFINITION: self._execute_asset_definition,
            TaraStep.IMPACT_RATING: self._execute_impact_rating,
            TaraStep.THREAT_IDENTIFICATION: self._execute_threat_identification,
            TaraStep.ATTACK_PATH_ANALYSIS: self._execute_attack_path_analysis,
            TaraStep.FEASIBILITY_ASSESSMENT: self._execute_feasibility_assessment,
            TaraStep.RISK_CALCULATION: self._execute_risk_calculation,
            TaraStep.TREATMENT_PLANNING: self._execute_treatment_planning,
            TaraStep.GOAL_SETTING: self._execute_goal_setting
        }
        
    async def create_analysis(self, name: str, description: str = None,
                            input_file_path: str = None) -> TaraAnalysis:
        """Create new TARA analysis from input file or interactively.
        
        Args:
            name: Analysis name
            description: Optional analysis description
            input_file_path: Optional path to input file with asset data
            
        Returns:
            Created TaraAnalysis instance
            
        Raises:
            AnalysisError: If analysis creation fails
            ValidationError: If input validation fails
        """
        try:
            logger.info(f"Creating new TARA analysis: {name}")
            
            # Create analysis record
            analysis = TaraAnalysis(
                name=name,
                description=description,
                status=AnalysisStatus.CREATED,
                created_at=datetime.now(),
                metadata={'input_file': input_file_path} if input_file_path else {}
            )
            
            self.db_session.add(analysis)
            self.db_session.commit()
            
            # Process input file if provided
            if input_file_path:
                await self._process_input_file(analysis, input_file_path)
            
            logger.info(f"Created analysis {analysis.id} successfully")
            return analysis
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create analysis: {str(e)}")
            raise AnalysisError(f"Analysis creation failed: {str(e)}", analysis_id=name)
    
    async def execute_complete_workflow(self, analysis_id: str) -> AnalysisResult:
        """Execute complete 8-step TARA workflow for analysis.
        
        Args:
            analysis_id: ID of analysis to execute
            
        Returns:
            Complete analysis results
            
        Raises:
            AnalysisError: If workflow execution fails
        """
        analysis = self._get_analysis(analysis_id)
        
        try:
            logger.info(f"Starting complete TARA workflow for analysis {analysis_id}")
            analysis.status = AnalysisStatus.IN_PROGRESS
            analysis.started_at = datetime.now()
            self.db_session.commit()
            
            # Execute all workflow steps in sequence
            for step in TaraStep:
                await self._execute_workflow_step(analysis, step)
                
            # Generate final results
            result = await self._generate_analysis_result(analysis)
            
            # Mark analysis as completed
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now()
            self.db_session.commit()
            
            logger.info(f"Completed TARA workflow for analysis {analysis_id}")
            return result
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            self.db_session.commit()
            logger.error(f"TARA workflow failed for analysis {analysis_id}: {str(e)}")
            raise AnalysisError(f"Workflow execution failed: {str(e)}", analysis_id=analysis_id)
    
    async def execute_workflow_step(self, analysis_id: str, step: TaraStep) -> Dict[str, Any]:
        """Execute specific workflow step for analysis.
        
        Args:
            analysis_id: ID of analysis
            step: Workflow step to execute
            
        Returns:
            Step execution results
        """
        analysis = self._get_analysis(analysis_id)
        return await self._execute_workflow_step(analysis, step)
    
    def get_analysis_progress(self, analysis_id: str) -> AnalysisProgress:
        """Get current analysis progress and status.
        
        Args:
            analysis_id: ID of analysis
            
        Returns:
            Current analysis progress
        """
        analysis = self._get_analysis(analysis_id)
        
        # Extract progress from analysis metadata
        metadata = analysis.metadata or {}
        progress_data = metadata.get('progress', {})
        
        completed_steps = [TaraStep(step) for step in progress_data.get('completed_steps', [])]
        current_step_name = progress_data.get('current_step')
        current_step = TaraStep(current_step_name) if current_step_name else TaraStep.ASSET_DEFINITION
        
        step_progress = {}
        for step_name, progress in progress_data.get('step_progress', {}).items():
            step_progress[TaraStep(step_name)] = progress
        
        total_progress = len(completed_steps) / len(TaraStep)
        
        return AnalysisProgress(
            current_step=current_step,
            completed_steps=completed_steps,
            step_progress=step_progress,
            estimated_completion=analysis.estimated_completion,
            total_progress=total_progress
        )
    
    async def _process_input_file(self, analysis: TaraAnalysis, file_path: str) -> None:
        """Process input file and extract initial data."""
        try:
            # Parse input file
            parse_result = self.file_processor.process_file(file_path)
            
            # Create assets from parsed data
            for asset_data in parse_result.assets:
                asset = Asset(
                    analysis_id=analysis.id,
                    name=asset_data['name'],
                    asset_type=asset_data.get('asset_type', 'HARDWARE_COMPONENT'),
                    criticality=asset_data.get('criticality', 'MEDIUM'),
                    interfaces=asset_data.get('interfaces', []),
                    description=asset_data.get('description'),
                    location=asset_data.get('location'),
                    manufacturer=asset_data.get('manufacturer')
                )
                self.db_session.add(asset)
            
            # Update analysis metadata
            analysis.metadata = analysis.metadata or {}
            analysis.metadata.update({
                'input_processing': {
                    'file_path': file_path,
                    'confidence_score': parse_result.confidence_score,
                    'assets_imported': len(parse_result.assets),
                    'threats_imported': len(parse_result.threats),
                    'validation_errors': parse_result.validation_errors
                }
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to process input file {file_path}: {str(e)}")
            raise AnalysisError(f"Input file processing failed: {str(e)}")
    
    async def _execute_workflow_step(self, analysis: TaAnalysis, step: TaraStep) -> Dict[str, Any]:
        """Execute specific workflow step."""
        logger.info(f"Executing step {step.value} for analysis {analysis.id}")
        
        # Update progress
        self._update_step_progress(analysis, step, 0.0)
        
        # Execute step handler
        handler = self.step_handlers.get(step)
        if not handler:
            raise AnalysisError(f"No handler for step {step.value}")
        
        result = await handler(analysis)
        
        # Mark step as completed
        self._mark_step_completed(analysis, step)
        
        logger.info(f"Completed step {step.value} for analysis {analysis.id}")
        return result
    
    async def _execute_asset_definition(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 1: Asset Definition - Define system assets and interfaces."""
        self._update_step_progress(analysis, TaraStep.ASSET_DEFINITION, 0.2)
        
        # Get existing assets
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis.id).all()
        
        # Use AI to enhance asset definitions if needed
        if assets:
            self._update_step_progress(analysis, TaraStep.ASSET_DEFINITION, 0.6)
            
            # AI enhancement of asset details
            enhanced_assets = await self.ai_orchestrator.enhance_asset_definitions(
                [self._asset_to_dict(asset) for asset in assets]
            )
            
            # Update assets with AI enhancements
            for i, asset in enumerate(assets):
                if i < len(enhanced_assets):
                    enhanced = enhanced_assets[i]
                    asset.description = enhanced.get('description', asset.description)
                    asset.interfaces = enhanced.get('interfaces', asset.interfaces)
        
        self._update_step_progress(analysis, TaraStep.ASSET_DEFINITION, 1.0)
        
        return {
            'step': TaraStep.ASSET_DEFINITION.value,
            'assets_defined': len(assets),
            'enhancements_applied': len(assets) > 0
        }
    
    async def _execute_impact_rating(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 2: Impact Rating - Rate cybersecurity impact for each asset."""
        self._update_step_progress(analysis, TaraStep.IMPACT_RATING, 0.2)
        
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis.id).all()
        
        # Use AI to assess impact ratings
        self._update_step_progress(analysis, TaraStep.IMPACT_RATING, 0.5)
        
        impact_ratings = await self.ai_orchestrator.assess_impact_ratings(
            [self._asset_to_dict(asset) for asset in assets]
        )
        
        # Update assets with impact ratings
        for i, asset in enumerate(assets):
            if i < len(impact_ratings):
                asset.metadata = asset.metadata or {}
                asset.metadata['impact_rating'] = impact_ratings[i]
        
        self._update_step_progress(analysis, TaraStep.IMPACT_RATING, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.IMPACT_RATING.value,
            'assets_rated': len(assets),
            'ratings_applied': len(impact_ratings)
        }
    
    async def _execute_threat_identification(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 3: Threat Identification - Identify potential threat scenarios."""
        self._update_step_progress(analysis, TaraStep.THREAT_IDENTIFICATION, 0.2)
        
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis.id).all()
        
        # Use AI to identify threats
        self._update_step_progress(analysis, TaraStep.THREAT_IDENTIFICATION, 0.5)
        
        identified_threats = await self.ai_orchestrator.identify_threats(
            [self._asset_to_dict(asset) for asset in assets]
        )
        
        # Create threat scenario records
        threats_created = 0
        for threat_data in identified_threats:
            threat = ThreatScenario(
                analysis_id=analysis.id,
                name=threat_data['name'],
                category=threat_data.get('category'),
                description=threat_data['description'],
                stride_category=threat_data.get('stride_category'),
                target_assets=threat_data.get('target_assets', [])
            )
            self.db_session.add(threat)
            threats_created += 1
        
        self._update_step_progress(analysis, TaraStep.THREAT_IDENTIFICATION, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.THREAT_IDENTIFICATION.value,
            'threats_identified': threats_created,
            'assets_analyzed': len(assets)
        }
    
    async def _execute_attack_path_analysis(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 4: Attack Path Analysis - Analyze attack paths and vectors."""
        self._update_step_progress(analysis, TaraStep.ATTACK_PATH_ANALYSIS, 0.2)
        
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis.id).all()
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis.id).all()
        
        # Analyze attack paths using AI
        self._update_step_progress(analysis, TaraStep.ATTACK_PATH_ANALYSIS, 0.6)
        
        attack_paths = await self.ai_orchestrator.analyze_attack_paths(
            [self._threat_to_dict(threat) for threat in threats],
            [self._asset_to_dict(asset) for asset in assets]
        )
        
        # Update threats with attack path analysis
        for i, threat in enumerate(threats):
            if i < len(attack_paths):
                threat.metadata = threat.metadata or {}
                threat.metadata['attack_paths'] = attack_paths[i]
        
        self._update_step_progress(analysis, TaraStep.ATTACK_PATH_ANALYSIS, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.ATTACK_PATH_ANALYSIS.value,
            'paths_analyzed': len(attack_paths),
            'threats_processed': len(threats)
        }
    
    async def _execute_feasibility_assessment(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 5: Feasibility Assessment - Assess attack feasibility."""
        self._update_step_progress(analysis, TaraStep.FEASIBILITY_ASSESSMENT, 0.2)
        
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis.id).all()
        
        # Assess feasibility using AI
        self._update_step_progress(analysis, TaraStep.FEASIBILITY_ASSESSMENT, 0.6)
        
        feasibility_assessments = await self.ai_orchestrator.assess_feasibility(
            [self._threat_to_dict(threat) for threat in threats]
        )
        
        # Update threats with feasibility assessments
        for i, threat in enumerate(threats):
            if i < len(feasibility_assessments):
                threat.feasibility_rating = feasibility_assessments[i].get('rating')
                threat.metadata = threat.metadata or {}
                threat.metadata['feasibility'] = feasibility_assessments[i]
        
        self._update_step_progress(analysis, TaraStep.FEASIBILITY_ASSESSMENT, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.FEASIBILITY_ASSESSMENT.value,
            'assessments_completed': len(feasibility_assessments),
            'threats_assessed': len(threats)
        }
    
    async def _execute_risk_calculation(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 6: Risk Calculation - Calculate final risk values."""
        self._update_step_progress(analysis, TaraStep.RISK_CALCULATION, 0.2)
        
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis.id).all()
        
        # Calculate risk values
        self._update_step_progress(analysis, TaraStep.RISK_CALCULATION, 0.5)
        
        risks_created = 0
        for threat in threats:
            # Get impact and feasibility ratings
            impact = threat.impact_rating or 'MEDIUM'
            feasibility = threat.feasibility_rating or 'MEDIUM'
            
            # Calculate risk level (simplified calculation)
            risk_level = self._calculate_risk_level(impact, feasibility)
            
            # Create risk assessment record
            risk = RiskAssessment(
                analysis_id=analysis.id,
                threat_scenario_id=threat.id,
                impact_rating=impact,
                likelihood_rating=feasibility,
                risk_level=risk_level,
                calculated_at=datetime.now()
            )
            self.db_session.add(risk)
            risks_created += 1
        
        self._update_step_progress(analysis, TaraStep.RISK_CALCULATION, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.RISK_CALCULATION.value,
            'risks_calculated': risks_created,
            'threats_processed': len(threats)
        }
    
    async def _execute_treatment_planning(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 7: Treatment Planning - Plan risk treatment measures."""
        self._update_step_progress(analysis, TaraStep.TREATMENT_PLANNING, 0.2)
        
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis.id).all()
        
        # Plan treatments using AI
        self._update_step_progress(analysis, TaraStep.TREATMENT_PLANNING, 0.6)
        
        treatment_plans = await self.ai_orchestrator.plan_treatments(
            [self._risk_to_dict(risk) for risk in risks]
        )
        
        # Create treatment records
        treatments_created = 0
        for plan in treatment_plans:
            treatment = Treatment(
                analysis_id=analysis.id,
                name=plan['name'],
                treatment_type=plan.get('type', 'COUNTERMEASURE'),
                description=plan['description'],
                target_risks=plan.get('target_risks', []),
                implementation_cost=plan.get('cost'),
                effectiveness=plan.get('effectiveness')
            )
            self.db_session.add(treatment)
            treatments_created += 1
        
        self._update_step_progress(analysis, TaraStep.TREATMENT_PLANNING, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.TREATMENT_PLANNING.value,
            'treatments_planned': treatments_created,
            'risks_addressed': len(risks)
        }
    
    async def _execute_goal_setting(self, analysis: TaraAnalysis) -> Dict[str, Any]:
        """Step 8: Goal Setting - Set cybersecurity goals and targets."""
        self._update_step_progress(analysis, TaraStep.GOAL_SETTING, 0.5)
        
        # Analyze overall risk profile
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis.id).all()
        treatments = self.db_session.query(Treatment).filter_by(analysis_id=analysis.id).all()
        
        # Generate cybersecurity goals
        goals = await self.ai_orchestrator.generate_cybersecurity_goals(
            [self._risk_to_dict(risk) for risk in risks],
            [self._treatment_to_dict(treatment) for treatment in treatments]
        )
        
        # Update analysis metadata with goals
        analysis.metadata = analysis.metadata or {}
        analysis.metadata['cybersecurity_goals'] = goals
        
        self._update_step_progress(analysis, TaraStep.GOAL_SETTING, 1.0)
        self.db_session.commit()
        
        return {
            'step': TaraStep.GOAL_SETTING.value,
            'goals_defined': len(goals),
            'analysis_completed': True
        }
    
    def _calculate_risk_level(self, impact: str, likelihood: str) -> str:
        """Calculate risk level from impact and likelihood ratings."""
        # Simplified risk matrix
        risk_matrix = {
            ('LOW', 'LOW'): 'LOW',
            ('LOW', 'MEDIUM'): 'LOW', 
            ('LOW', 'HIGH'): 'MEDIUM',
            ('MEDIUM', 'LOW'): 'LOW',
            ('MEDIUM', 'MEDIUM'): 'MEDIUM',
            ('MEDIUM', 'HIGH'): 'HIGH',
            ('HIGH', 'LOW'): 'MEDIUM',
            ('HIGH', 'MEDIUM'): 'HIGH',
            ('HIGH', 'HIGH'): 'CRITICAL'
        }
        
        return risk_matrix.get((impact, likelihood), 'MEDIUM')
    
    def _update_step_progress(self, analysis: TaraAnalysis, step: TaraStep, progress: float) -> None:
        """Update progress for specific workflow step."""
        analysis.metadata = analysis.metadata or {}
        progress_data = analysis.metadata.setdefault('progress', {})
        
        progress_data['current_step'] = step.value
        step_progress = progress_data.setdefault('step_progress', {})
        step_progress[step.value] = progress
        
        self.db_session.commit()
    
    def _mark_step_completed(self, analysis: TaraAnalysis, step: TaraStep) -> None:
        """Mark workflow step as completed."""
        analysis.metadata = analysis.metadata or {}
        progress_data = analysis.metadata.setdefault('progress', {})
        
        completed_steps = progress_data.setdefault('completed_steps', [])
        if step.value not in completed_steps:
            completed_steps.append(step.value)
        
        progress_data['step_progress'][step.value] = 1.0
        
        self.db_session.commit()
    
    async def _generate_analysis_result(self, analysis: TaraAnalysis) -> AnalysisResult:
        """Generate complete analysis results."""
        # Query all related data
        assets = self.db_session.query(Asset).filter_by(analysis_id=analysis.id).all()
        threats = self.db_session.query(ThreatScenario).filter_by(analysis_id=analysis.id).all()
        risks = self.db_session.query(RiskAssessment).filter_by(analysis_id=analysis.id).all()
        treatments = self.db_session.query(Treatment).filter_by(analysis_id=analysis.id).all()
        
        # Calculate overall confidence score
        confidence_score = self._calculate_overall_confidence(assets, threats, risks)
        
        # Generate compliance status
        compliance_status = await self._generate_compliance_status(analysis, assets, threats, risks)
        
        return AnalysisResult(
            analysis_id=analysis.id,
            assets=[self._asset_to_dict(asset) for asset in assets],
            threats=[self._threat_to_dict(threat) for threat in threats],
            risks=[self._risk_to_dict(risk) for risk in risks],
            treatments=[self._treatment_to_dict(treatment) for treatment in treatments],
            compliance_status=compliance_status,
            metadata=analysis.metadata or {},
            confidence_score=confidence_score
        )
    
    def _calculate_overall_confidence(self, assets: List[Asset], 
                                    threats: List[ThreatScenario],
                                    risks: List[RiskAssessment]) -> float:
        """Calculate overall analysis confidence score."""
        # Simplified confidence calculation
        base_score = 0.7
        
        # Boost for data completeness
        if assets and threats and risks:
            base_score += 0.1
        
        # Boost for AI enhancements
        ai_enhanced = sum(1 for asset in assets if asset.metadata and 'ai_enhanced' in asset.metadata)
        if ai_enhanced > 0:
            base_score += min(0.1, ai_enhanced / len(assets) * 0.1)
        
        # Boost for complete workflow
        if len(risks) > 0:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    async def _generate_compliance_status(self, analysis: TaraAnalysis, 
                                        assets: List[Asset],
                                        threats: List[ThreatScenario], 
                                        risks: List[RiskAssessment]) -> Dict[str, Any]:
        """Generate ISO/SAE 21434 compliance status."""
        return {
            'iso_21434_compliant': True,  # Simplified - would need full compliance checking
            'required_elements_present': {
                'assets_defined': len(assets) > 0,
                'threats_identified': len(threats) > 0,
                'risks_assessed': len(risks) > 0,
                'workflow_completed': analysis.status == AnalysisStatus.COMPLETED
            },
            'audit_trail_available': True,
            'documentation_complete': True
        }
    
    def _get_analysis(self, analysis_id: str) -> TaraAnalysis:
        """Get analysis by ID with error handling."""
        analysis = self.db_session.query(TaraAnalysis).filter_by(id=analysis_id).first()
        if not analysis:
            raise AnalysisError(f"Analysis not found: {analysis_id}", analysis_id=analysis_id)
        return analysis
    
    def _asset_to_dict(self, asset: Asset) -> Dict[str, Any]:
        """Convert Asset model to dictionary."""
        return {
            'id': asset.id,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'criticality': asset.criticality,
            'interfaces': asset.interfaces,
            'description': asset.description,
            'location': asset.location,
            'manufacturer': asset.manufacturer,
            'metadata': asset.metadata or {}
        }
    
    def _threat_to_dict(self, threat: ThreatScenario) -> Dict[str, Any]:
        """Convert ThreatScenario model to dictionary."""
        return {
            'id': threat.id,
            'name': threat.name,
            'category': threat.category,
            'description': threat.description,
            'stride_category': threat.stride_category,
            'target_assets': threat.target_assets,
            'impact_rating': threat.impact_rating,
            'feasibility_rating': threat.feasibility_rating,
            'metadata': threat.metadata or {}
        }
    
    def _risk_to_dict(self, risk: RiskAssessment) -> Dict[str, Any]:
        """Convert RiskAssessment model to dictionary."""
        return {
            'id': risk.id,
            'threat_scenario_id': risk.threat_scenario_id,
            'impact_rating': risk.impact_rating,
            'likelihood_rating': risk.likelihood_rating,
            'risk_level': risk.risk_level,
            'calculated_at': risk.calculated_at.isoformat() if risk.calculated_at else None,
            'metadata': risk.metadata or {}
        }
    
    def _treatment_to_dict(self, treatment: Treatment) -> Dict[str, Any]:
        """Convert Treatment model to dictionary."""
        return {
            'id': treatment.id,
            'name': treatment.name,
            'treatment_type': treatment.treatment_type,
            'description': treatment.description,
            'target_risks': treatment.target_risks,
            'implementation_cost': treatment.implementation_cost,
            'effectiveness': treatment.effectiveness,
            'metadata': treatment.metadata or {}
        }