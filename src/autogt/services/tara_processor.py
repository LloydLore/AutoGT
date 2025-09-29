"""TARA processor for orchestrating 8-step automotive cybersecurity analysis.

Reference: research.md section on TARA methodology and implement.prompt.md T034
Orchestrates complete ISO/SAE 21434 threat analysis and risk assessment workflow.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from ..models import (
    TaraAnalysis, Asset, ThreatScenario, AttackPath, AttackFeasibility,
    ImpactRating, RiskValue, RiskTreatment, CybersecurityGoal,
    AnalysisPhase, CompletionStatus, AssetType, CriticalityLevel,
    ThreatActor, RiskLevel, TreatmentDecision, ProtectionLevel,
    ImplementationPhase
)
from .autogen_agent import AutoGenTaraAgent, TaraAgentConfig
from .database import DatabaseService
from .file_handler import FileHandler


class TaraStep(Enum):
    """TARA methodology steps per ISO/SAE 21434."""
    ASSET_IDENTIFICATION = "asset_identification"
    THREAT_SCENARIO_IDENTIFICATION = "threat_scenario_identification"
    ATTACK_PATH_ANALYSIS = "attack_path_analysis"
    ATTACK_FEASIBILITY_RATING = "attack_feasibility_rating"
    IMPACT_RATING = "impact_rating"
    RISK_VALUE_DETERMINATION = "risk_value_determination"
    RISK_TREATMENT_DECISION = "risk_treatment_decision"
    CYBERSECURITY_GOALS = "cybersecurity_goals"


@dataclass
class TaraProcessorConfig:
    """Configuration for TARA processor."""
    batch_size: int = 10
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_parallel_processing: bool = True
    save_intermediate_results: bool = True
    validation_enabled: bool = True
    performance_tracking: bool = True


@dataclass
class StepResult:
    """Result of a single TARA step."""
    step: TaraStep
    success: bool
    execution_time_seconds: float
    items_processed: int
    items_created: int
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaraProcessorResult:
    """Result of complete TARA processing."""
    analysis_id: str
    success: bool
    total_execution_time_seconds: float
    steps_completed: List[TaraStep]
    step_results: List[StepResult]
    final_status: CompletionStatus
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class TaraProcessorError(Exception):
    """Custom exception for TARA processor operations."""
    pass


class TaraProcessor:
    """Main TARA processor orchestrating 8-step analysis workflow.
    
    Coordinates between AutoGen agents and data persistence to execute
    complete ISO/SAE 21434 threat analysis and risk assessment.
    
    Reference: research.md TARA methodology section
    """
    
    def __init__(
        self, 
        db_service: DatabaseService,
        file_handler: FileHandler,
        autogen_agent: AutoGenTaraAgent,
        config: Optional[TaraProcessorConfig] = None
    ):
        """Initialize TARA processor.
        
        Args:
            db_service: Database service instance
            file_handler: File handler for input processing
            autogen_agent: AutoGen agent for AI processing
            config: Processor configuration
        """
        self.db_service = db_service
        self.file_handler = file_handler
        self.autogen_agent = autogen_agent
        self.config = config or TaraProcessorConfig()
        
        self.logger = logging.getLogger(__name__)
        
        # Step sequence for TARA methodology
        self.step_sequence = [
            TaraStep.ASSET_IDENTIFICATION,
            TaraStep.THREAT_SCENARIO_IDENTIFICATION,
            TaraStep.ATTACK_PATH_ANALYSIS,
            TaraStep.ATTACK_FEASIBILITY_RATING,
            TaraStep.IMPACT_RATING,
            TaraStep.RISK_VALUE_DETERMINATION,
            TaraStep.RISK_TREATMENT_DECISION,
            TaraStep.CYBERSECURITY_GOALS
        ]
    
    def process_analysis(self, analysis_id: str) -> TaraProcessorResult:
        """Execute complete TARA analysis workflow.
        
        Args:
            analysis_id: ID of analysis to process
            
        Returns:
            TaraProcessorResult with processing details
        """
        start_time = datetime.now()
        step_results = []
        steps_completed = []
        
        try:
            self.logger.info(f"Starting TARA analysis processing: {analysis_id}")
            
            # Load analysis
            analysis = self._load_analysis(analysis_id)
            
            # Execute each step in sequence
            for step in self.step_sequence:
                self.logger.info(f"Executing step: {step.value}")
                
                step_result = self._execute_step(analysis, step)
                step_results.append(step_result)
                
                if step_result.success:
                    steps_completed.append(step)
                    self._update_analysis_progress(analysis, step)
                else:
                    # Stop on first failure unless configured otherwise
                    error_msg = f"Step {step.value} failed: {step_result.error_message}"
                    self.logger.error(error_msg)
                    
                    return TaraProcessorResult(
                        analysis_id=analysis_id,
                        success=False,
                        total_execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                        steps_completed=steps_completed,
                        step_results=step_results,
                        final_status=CompletionStatus.FAILED,
                        error_message=error_msg
                    )
            
            # Mark analysis as completed
            self._finalize_analysis(analysis)
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            return TaraProcessorResult(
                analysis_id=analysis_id,
                success=True,
                total_execution_time_seconds=total_time,
                steps_completed=steps_completed,
                step_results=step_results,
                final_status=CompletionStatus.COMPLETED,
                performance_metrics=self._calculate_performance_metrics(step_results, total_time)
            )
            
        except Exception as e:
            error_msg = f"TARA processing failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return TaraProcessorResult(
                analysis_id=analysis_id,
                success=False,
                total_execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                steps_completed=steps_completed,
                step_results=step_results,
                final_status=CompletionStatus.FAILED,
                error_message=error_msg
            )
    
    def process_analysis_from_file(self, file_path: str, analysis_name: str, vehicle_model: str) -> TaraProcessorResult:
        """Process TARA analysis from input file.
        
        Args:
            file_path: Path to input file (Excel, CSV, JSON, etc.)
            analysis_name: Name for the analysis
            vehicle_model: Vehicle model being analyzed
            
        Returns:
            TaraProcessorResult with processing details
        """
        try:
            # Process input file
            file_data = self.file_handler.parse_file(file_path)
            
            # Create new analysis
            analysis = self._create_analysis_from_file_data(
                file_data, analysis_name, vehicle_model, str(file_path)
            )
            
            # Process the analysis
            return self.process_analysis(str(analysis.id))
            
        except Exception as e:
            error_msg = f"File processing failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return TaraProcessorResult(
                analysis_id="",
                success=False,
                total_execution_time_seconds=0,
                steps_completed=[],
                step_results=[],
                final_status=CompletionStatus.FAILED,
                error_message=error_msg
            )
    
    def _execute_step(self, analysis: TaraAnalysis, step: TaraStep) -> StepResult:
        """Execute a single TARA step.
        
        Args:
            analysis: Analysis being processed
            step: Step to execute
            
        Returns:
            StepResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Route to appropriate step handler
            if step == TaraStep.ASSET_IDENTIFICATION:
                return self._execute_asset_identification(analysis, start_time)
            elif step == TaraStep.THREAT_SCENARIO_IDENTIFICATION:
                return self._execute_threat_identification(analysis, start_time)
            elif step == TaraStep.ATTACK_PATH_ANALYSIS:
                return self._execute_attack_path_analysis(analysis, start_time)
            elif step == TaraStep.ATTACK_FEASIBILITY_RATING:
                return self._execute_feasibility_rating(analysis, start_time)
            elif step == TaraStep.IMPACT_RATING:
                return self._execute_impact_rating(analysis, start_time)
            elif step == TaraStep.RISK_VALUE_DETERMINATION:
                return self._execute_risk_determination(analysis, start_time)
            elif step == TaraStep.RISK_TREATMENT_DECISION:
                return self._execute_risk_treatment(analysis, start_time)
            elif step == TaraStep.CYBERSECURITY_GOALS:
                return self._execute_cybersecurity_goals(analysis, start_time)
            else:
                raise TaraProcessorError(f"Unknown step: {step}")
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return StepResult(
                step=step,
                success=False,
                execution_time_seconds=execution_time,
                items_processed=0,
                items_created=0,
                error_message=str(e)
            )
    
    def _execute_asset_identification(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute asset identification step."""
        # Get system description context
        context = {
            "analysis_name": analysis.analysis_name,
            "vehicle_model": analysis.vehicle_model,
            "existing_assets": [asset.name for asset in analysis.assets]
        }
        
        # Use AutoGen asset analyst
        agent_result = self.autogen_agent.analyze_assets(context)
        
        items_created = 0
        with self.db_service.get_session() as session:
            for asset_data in agent_result.get("assets", []):
                asset = Asset(
                    analysis_id=analysis.id,
                    name=asset_data["name"],
                    asset_type=AssetType(asset_data["type"]),
                    criticality_level=CriticalityLevel(asset_data["criticality"]),
                    interfaces=asset_data.get("interfaces", []),
                    data_flows=asset_data.get("data_flows", []),
                    security_properties=asset_data.get("security_properties", {}),
                    iso_section=asset_data.get("iso_section", "15.6")
                )
                session.add(asset)
                items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.ASSET_IDENTIFICATION,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=1,
            items_created=items_created
        )
    
    def _execute_threat_identification(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute threat scenario identification step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Process each asset
            for asset in analysis.assets:
                context = {
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type.value,
                    "criticality": asset.criticality_level.value,
                    "interfaces": asset.interfaces,
                    "data_flows": asset.data_flows
                }
                
                # Use AutoGen threat hunter
                agent_result = self.autogen_agent.identify_threats(context)
                
                for threat_data in agent_result.get("threats", []):
                    threat = ThreatScenario(
                        asset_id=asset.id,
                        threat_name=threat_data["name"],
                        threat_actor=ThreatActor(threat_data["actor"]),
                        motivation=threat_data.get("motivation", ""),
                        attack_vectors=threat_data.get("attack_vectors", []),
                        prerequisites=threat_data.get("prerequisites", []),
                        iso_section=threat_data.get("iso_section", "15.7")
                    )
                    session.add(threat)
                    items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.THREAT_SCENARIO_IDENTIFICATION,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=len(analysis.assets),
            items_created=items_created
        )
    
    def _execute_attack_path_analysis(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute attack path analysis step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Get all threat scenarios
            from sqlalchemy.orm import selectinload
            
            updated_analysis = session.query(TaraAnalysis).options(
                selectinload(TaraAnalysis.assets).selectinload(Asset.threat_scenarios)
            ).filter(TaraAnalysis.id == analysis.id).first()
            
            for asset in updated_analysis.assets:
                for threat in asset.threat_scenarios:
                    context = {
                        "asset_name": asset.name,
                        "threat_name": threat.threat_name,
                        "attack_vectors": threat.attack_vectors,
                        "prerequisites": threat.prerequisites
                    }
                    
                    # Use AutoGen attack modeler
                    agent_result = self.autogen_agent.model_attack_paths(context)
                    
                    for path_data in agent_result.get("attack_paths", []):
                        attack_path = AttackPath(
                            threat_scenario_id=threat.id,
                            step_sequence=path_data["sequence"],
                            attack_step=path_data["step"],
                            intermediate_targets=path_data.get("targets", []),
                            technical_barriers=path_data.get("barriers", []),
                            required_resources=path_data.get("resources", [])
                        )
                        session.add(attack_path)
                        items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.ATTACK_PATH_ANALYSIS,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=sum(len(asset.threat_scenarios) for asset in analysis.assets),
            items_created=items_created
        )
    
    def _execute_feasibility_rating(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute attack feasibility rating step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Get all attack paths
            from sqlalchemy.orm import selectinload
            
            updated_analysis = session.query(TaraAnalysis).options(
                selectinload(TaraAnalysis.assets)
                .selectinload(Asset.threat_scenarios)
                .selectinload(ThreatScenario.attack_paths)
            ).filter(TaraAnalysis.id == analysis.id).first()
            
            for asset in updated_analysis.assets:
                for threat in asset.threat_scenarios:
                    for path in threat.attack_paths:
                        context = {
                            "attack_step": path.attack_step,
                            "technical_barriers": path.technical_barriers,
                            "required_resources": path.required_resources
                        }
                        
                        # Use AutoGen feasibility analyzer
                        agent_result = self.autogen_agent.assess_feasibility(context)
                        
                        feasibility_data = agent_result.get("feasibility", {})
                        feasibility = AttackFeasibility(
                            attack_path_id=path.id,
                            elapsed_time=feasibility_data.get("elapsed_time", "HIGH"),
                            specialist_expertise=feasibility_data.get("specialist_expertise", "EXPERT"),
                            knowledge_of_target=feasibility_data.get("knowledge_of_target", "LIMITED"),
                            window_of_opportunity=feasibility_data.get("window_of_opportunity", "MODERATE"),
                            equipment_required=feasibility_data.get("equipment_required", "SPECIALIZED"),
                            feasibility_score=feasibility_data.get("score", 50)
                        )
                        session.add(feasibility)
                        items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.ATTACK_FEASIBILITY_RATING,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=sum(
                len(path.attack_paths) 
                for asset in analysis.assets 
                for path in asset.threat_scenarios
            ),
            items_created=items_created
        )
    
    def _execute_impact_rating(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute impact rating step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            for asset in analysis.assets:
                context = {
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type.value,
                    "criticality": asset.criticality_level.value,
                    "security_properties": asset.security_properties
                }
                
                # Use AutoGen impact assessor
                agent_result = self.autogen_agent.assess_impact(context)
                
                impact_data = agent_result.get("impact", {})
                impact = ImpactRating(
                    asset_id=asset.id,
                    safety_impact=impact_data.get("safety", "NEGLIGIBLE"),
                    financial_impact=impact_data.get("financial", "NEGLIGIBLE"),
                    operational_impact=impact_data.get("operational", "NEGLIGIBLE"),
                    privacy_impact=impact_data.get("privacy", "NEGLIGIBLE"),
                    impact_score=impact_data.get("score", 10),
                    iso_section=impact_data.get("iso_section", "15.8")
                )
                session.add(impact)
                items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.IMPACT_RATING,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=len(analysis.assets),
            items_created=items_created
        )
    
    def _execute_risk_determination(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute risk value determination step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Load complete data with relationships
            from sqlalchemy.orm import selectinload
            
            updated_analysis = session.query(TaraAnalysis).options(
                selectinload(TaraAnalysis.assets).selectinload(Asset.threat_scenarios),
                selectinload(TaraAnalysis.assets).selectinload(Asset.impact_ratings)
            ).filter(TaraAnalysis.id == analysis.id).first()
            
            for asset in updated_analysis.assets:
                impact_rating = asset.impact_ratings[0] if asset.impact_ratings else None
                if not impact_rating:
                    continue
                
                for threat in asset.threat_scenarios:
                    # Get attack feasibility from paths
                    feasibility = None
                    if threat.attack_paths:
                        feasibility = threat.attack_paths[0].attack_feasibility
                    
                    if feasibility:
                        context = {
                            "impact_score": impact_rating.impact_score,
                            "feasibility_score": feasibility.feasibility_score,
                            "asset_criticality": asset.criticality_level.value
                        }
                        
                        # Use AutoGen risk calculator
                        agent_result = self.autogen_agent.calculate_risk(context)
                        
                        risk_data = agent_result.get("risk", {})
                        risk_value = RiskValue(
                            threat_scenario_id=threat.id,
                            impact_rating_id=impact_rating.id,
                            attack_feasibility_id=feasibility.id,
                            risk_level=RiskLevel(risk_data.get("level", "MEDIUM")),
                            risk_score=risk_data.get("score", 50),
                            calculation_method=risk_data.get("method", "ISO/SAE 21434 Matrix")
                        )
                        session.add(risk_value)
                        items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.RISK_VALUE_DETERMINATION,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=sum(len(asset.threat_scenarios) for asset in analysis.assets),
            items_created=items_created
        )
    
    def _execute_risk_treatment(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute risk treatment decision step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Get all risk values
            from sqlalchemy.orm import selectinload
            
            updated_analysis = session.query(TaraAnalysis).options(
                selectinload(TaraAnalysis.assets)
                .selectinload(Asset.threat_scenarios)
                .selectinload(ThreatScenario.risk_values)
            ).filter(TaraAnalysis.id == analysis.id).first()
            
            for asset in updated_analysis.assets:
                for threat in asset.threat_scenarios:
                    for risk_value in threat.risk_values:
                        context = {
                            "risk_level": risk_value.risk_level.value,
                            "risk_score": risk_value.risk_score,
                            "asset_name": asset.name,
                            "threat_name": threat.threat_name
                        }
                        
                        # Use AutoGen treatment planner
                        agent_result = self.autogen_agent.plan_treatment(context)
                        
                        treatment_data = agent_result.get("treatment", {})
                        treatment = RiskTreatment(
                            risk_value_id=risk_value.id,
                            treatment_decision=TreatmentDecision(
                                treatment_data.get("decision", "MITIGATE")
                            ),
                            countermeasures=treatment_data.get("countermeasures", []),
                            residual_risk_level=RiskLevel(
                                treatment_data.get("residual_risk", "LOW")
                            ),
                            implementation_cost=treatment_data.get("cost", "MEDIUM"),
                            rationale=treatment_data.get("rationale", ""),
                            iso_section=treatment_data.get("iso_section", "15.11")
                        )
                        session.add(treatment)
                        items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.RISK_TREATMENT_DECISION,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=sum(
                len(threat.risk_values) 
                for asset in analysis.assets 
                for threat in asset.threat_scenarios
            ),
            items_created=items_created
        )
    
    def _execute_cybersecurity_goals(self, analysis: TaraAnalysis, start_time: datetime) -> StepResult:
        """Execute cybersecurity goals step."""
        items_created = 0
        
        with self.db_service.get_session() as session:
            # Analyze all risks and treatments to derive goals
            context = {
                "analysis_name": analysis.analysis_name,
                "vehicle_model": analysis.vehicle_model,
                "asset_count": len(analysis.assets),
                "high_risks": []  # Will be populated from risk analysis
            }
            
            # Use AutoGen goals architect
            agent_result = self.autogen_agent.architect_goals(context)
            
            for goal_data in agent_result.get("goals", []):
                goal = CybersecurityGoal(
                    analysis_id=analysis.id,
                    goal_name=goal_data["name"],
                    protection_level=ProtectionLevel(goal_data.get("protection_level", "CAL1")),
                    security_controls=goal_data.get("controls", []),
                    verification_method=goal_data.get("verification", ""),
                    implementation_phase=ImplementationPhase(
                        goal_data.get("phase", "DEVELOPMENT")
                    ),
                    iso_section=goal_data.get("iso_section", "15.5")
                )
                session.add(goal)
                items_created += 1
            
            session.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step=TaraStep.CYBERSECURITY_GOALS,
            success=True,
            execution_time_seconds=execution_time,
            items_processed=1,
            items_created=items_created
        )
    
    def _load_analysis(self, analysis_id: str) -> TaraAnalysis:
        """Load analysis from database with relationships."""
        with self.db_service.get_session() as session:
            from sqlalchemy.orm import selectinload
            
            analysis = session.query(TaraAnalysis).options(
                selectinload(TaraAnalysis.assets),
                selectinload(TaraAnalysis.cybersecurity_goals)
            ).filter(TaraAnalysis.id == analysis_id).first()
            
            if not analysis:
                raise TaraProcessorError(f"Analysis not found: {analysis_id}")
            
            return analysis
    
    def _create_analysis_from_file_data(
        self, file_data: Dict[str, Any], analysis_name: str, vehicle_model: str, input_file_path: str
    ) -> TaraAnalysis:
        """Create new analysis from file data."""
        with self.db_service.get_session() as session:
            analysis = TaraAnalysis(
                analysis_name=analysis_name,
                vehicle_model=vehicle_model,
                analysis_phase=AnalysisPhase.DESIGN,
                completion_status=CompletionStatus.IN_PROGRESS,
                input_file_path=input_file_path
            )
            
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            return analysis
    
    def _update_analysis_progress(self, analysis: TaraAnalysis, completed_step: TaraStep) -> None:
        """Update analysis progress after step completion."""
        with self.db_service.get_session() as session:
            # Update the analysis in the session
            analysis_in_session = session.merge(analysis)
            
            # Set current step
            step_index = self.step_sequence.index(completed_step)
            if step_index < len(self.step_sequence) - 1:
                next_step = self.step_sequence[step_index + 1]
                analysis_in_session.current_step = next_step.value
            
            session.commit()
    
    def _finalize_analysis(self, analysis: TaraAnalysis) -> None:
        """Mark analysis as completed."""
        with self.db_service.get_session() as session:
            analysis_in_session = session.merge(analysis)
            analysis_in_session.completion_status = CompletionStatus.COMPLETED
            analysis_in_session.completed_at = datetime.now()
            session.commit()
    
    def _calculate_performance_metrics(
        self, step_results: List[StepResult], total_time: float
    ) -> Dict[str, Any]:
        """Calculate performance metrics for the analysis."""
        return {
            "total_steps": len(step_results),
            "successful_steps": sum(1 for r in step_results if r.success),
            "total_items_processed": sum(r.items_processed for r in step_results),
            "total_items_created": sum(r.items_created for r in step_results),
            "average_step_time": total_time / len(step_results) if step_results else 0,
            "processing_rate_items_per_second": (
                sum(r.items_processed for r in step_results) / total_time 
                if total_time > 0 else 0
            )
        }
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get current status of analysis processing.
        
        Args:
            analysis_id: Analysis ID to check
            
        Returns:
            Dictionary with current analysis status
        """
        try:
            analysis = self._load_analysis(analysis_id)
            
            return {
                "analysis_id": str(analysis.id),
                "analysis_name": analysis.analysis_name,
                "completion_status": analysis.completion_status.value,
                "current_step": analysis.get_current_step(),
                "progress_percentage": self._calculate_progress_percentage(analysis),
                "created_at": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
            }
            
        except Exception as e:
            return {
                "analysis_id": analysis_id,
                "error": f"Status check failed: {e}"
            }
    
    def _calculate_progress_percentage(self, analysis: TaraAnalysis) -> int:
        """Calculate completion percentage for analysis."""
        if analysis.completion_status == CompletionStatus.COMPLETED:
            return 100
        elif analysis.completion_status == CompletionStatus.FAILED:
            return 0
        
        # Calculate based on current step
        current_step = analysis.get_current_step()
        if not current_step:
            return 0
        
        try:
            current_step_enum = TaraStep(current_step)
            step_index = self.step_sequence.index(current_step_enum)
            return int((step_index / len(self.step_sequence)) * 100)
        except (ValueError, IndexError):
            return 0