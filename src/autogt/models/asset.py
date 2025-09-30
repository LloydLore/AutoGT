"""Asset model implementation per data-model.md specification lines 8-46."""

from typing import List, Dict, Any, Optional
from sqlalchemy import String, Float, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, ISO21434Mixin
from .enums import AssetType, CriticalityLevel, ReviewStatus


class Asset(BaseModel, ISO21434Mixin):
    """Represents vehicle system components analyzed for cybersecurity threats.
    
    Per data-model.md Asset entity specification with full field definitions,
    relationships, validation rules, and state transitions.
    """
    
    __tablename__ = "assets"
    
    # Core identification fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True,
                                     comment="Human-readable asset name (e.g., 'ECU Gateway', 'Infotainment System')")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True,
                                                      comment="Detailed asset description")
    
    # Asset classification per data-model.md
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), nullable=False,
                                                 comment="Classification: HARDWARE, SOFTWARE, COMMUNICATION, DATA, HUMAN, PHYSICAL")
    criticality_level: Mapped[CriticalityLevel] = mapped_column(SQLEnum(CriticalityLevel), nullable=False,
                                                               comment="Safety/security importance: LOW, MEDIUM, HIGH, CRITICAL")
    
    # System integration fields
    interfaces: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True,
                                                      comment="List of connection points to other assets")
    data_flows: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True,
                                                      comment="List of information exchanges with other assets")
    security_properties: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True,
                                                               comment="Confidentiality, integrity, availability requirements")
    
    # AI analysis fields per FR-008, FR-009, FR-012
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                             comment="AI identification confidence (0.0-1.0)")
    review_status: Mapped[ReviewStatus] = mapped_column(SQLEnum(ReviewStatus), 
                                                       default=ReviewStatus.IDENTIFIED, nullable=False,
                                                       comment="Manual review state for uncertain assets per FR-011")
    source_files: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True,
                                                        comment="List of original documentation references")
    
    # Foreign key relationships
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("tara_analyses.id"), nullable=False,
                                            comment="Parent TARA analysis session")
    
    # Relationships per data-model.md relationship specifications
    analysis = relationship("TaraAnalysis", back_populates="assets")
    threat_scenarios = relationship("ThreatScenario", back_populates="asset", cascade="all, delete-orphan")
    impact_ratings = relationship("ImpactRating", back_populates="asset", cascade="all, delete-orphan")
    risk_values = relationship("RiskValue", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type={self.asset_type}, criticality={self.criticality_level})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate asset per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Asset name must be non-empty and unique within analysis (enforced by DB constraint)
        if not self.name or not self.name.strip():
            errors.append("Asset name must be non-empty")
            
        # Criticality level must align with safety requirements (business logic validation)
        if self.asset_type == AssetType.HARDWARE and self.criticality_level == CriticalityLevel.LOW:
            # Hardware assets typically have higher criticality
            errors.append("Hardware assets should typically have MEDIUM or higher criticality")
            
        # Confidence score validation per FR-012 multi-factor scoring
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                errors.append("Confidence score must be between 0.0 and 1.0")
                
        # ISO section reference validation
        if self.iso_section and not self.iso_section.startswith(("4.", "5.", "6.", "7.", "8.", "9.")):
            errors.append("ISO section must reference valid ISO/SAE 21434 sections (4-9)")
            
        return len(errors) == 0, errors
    
    def transition_review_status(self, new_status: ReviewStatus, reason: str = None) -> bool:
        """Handle state transitions per data-model.md state transition rules.
        
        Valid transitions:
        - IDENTIFIED → UNDER_REVIEW (for uncertain assets per FR-011)
        - UNDER_REVIEW → APPROVED / REJECTED (manual validation)
        - APPROVED → ANALYZED (ready for threat analysis)
        """
        valid_transitions = {
            ReviewStatus.IDENTIFIED: [ReviewStatus.UNDER_REVIEW, ReviewStatus.APPROVED],
            ReviewStatus.UNDER_REVIEW: [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.NEEDS_CLARIFICATION],
            ReviewStatus.APPROVED: [],  # Terminal state for asset definition
            ReviewStatus.REJECTED: [ReviewStatus.UNDER_REVIEW],  # Can be reconsidered
            ReviewStatus.NEEDS_CLARIFICATION: [ReviewStatus.UNDER_REVIEW]
        }
        
        if new_status in valid_transitions.get(self.review_status, []):
            self.review_status = new_status
            return True
        return False
    
    def calculate_confidence_factors(self) -> Dict[str, float]:
        """Calculate multi-factor confidence score per FR-012.
        
        Factors: 40% data completeness + 35% model confidence + 25% validation checks
        """
        # Data completeness factor (40%)
        required_fields = [self.name, self.asset_type, self.criticality_level]
        optional_fields = [self.description, self.interfaces, self.data_flows, self.security_properties]
        
        required_complete = sum(1 for field in required_fields if field is not None)
        optional_complete = sum(1 for field in optional_fields if field is not None)
        
        data_completeness = (required_complete / len(required_fields)) * 0.7 + \
                          (optional_complete / len(optional_fields)) * 0.3
        
        # Model confidence factor (35%) - would be set by AI agent
        model_confidence = 0.8  # Placeholder - actual value from AI analysis
        
        # Validation checks factor (25%)
        is_valid, _ = self.validate()
        validation_score = 1.0 if is_valid else 0.5
        
        factors = {
            'data_completeness': data_completeness * 0.40,
            'model_confidence': model_confidence * 0.35,
            'validation_checks': validation_score * 0.25
        }
        
        # Update confidence score
        self.confidence_score = sum(factors.values())
        
        return factors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.asset_type:
            result['asset_type'] = self.asset_type.value
        if self.criticality_level:
            result['criticality_level'] = self.criticality_level.value
        if self.review_status:
            result['review_status'] = self.review_status.value
            
        return result
        
    @classmethod
    def from_ai_analysis(cls, ai_data: Dict[str, Any], analysis_id: str, confidence_score: float) -> 'Asset':
        """Create Asset from AI analysis results per FR-008, FR-010.
        
        Args:
            ai_data: Dictionary containing AI-identified asset information
            analysis_id: Parent TARA analysis ID
            confidence_score: AI confidence in identification
        """
        return cls(
            name=ai_data.get('name'),
            description=ai_data.get('description'),
            asset_type=AssetType(ai_data.get('type', 'SOFTWARE')),
            criticality_level=CriticalityLevel(ai_data.get('criticality', 'MEDIUM')),
            interfaces=ai_data.get('interfaces', []),
            data_flows=ai_data.get('data_flows', []),
            security_properties=ai_data.get('security_properties', {}),
            confidence_score=confidence_score,
            review_status=ReviewStatus.UNDER_REVIEW if confidence_score < 0.8 else ReviewStatus.IDENTIFIED,
            source_files=ai_data.get('source_files', []),
            analysis_id=analysis_id,
            iso_section=ai_data.get('iso_section', '5.4.1')  # Default to asset identification section
        )