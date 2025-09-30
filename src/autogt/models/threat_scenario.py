"""Threat Scenario model implementation per data-model.md specification lines 47-99."""

from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Float, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel, ISO21434Mixin
from .enums import ThreatCategory, AttackVector, AttackComplexity, ReviewStatus


class ThreatScenario(BaseModel, ISO21434Mixin):
    """Represents specific cybersecurity threats targeting vehicle assets.
    
    Per data-model.md ThreatScenario entity specification with STRIDE threat analysis,
    CVSS-based scoring, attack path modeling, and lifecycle management.
    """
    
    __tablename__ = "threat_scenarios"
    
    # Core threat identification fields
    name = Column(String(255), nullable=False,
                 comment="Descriptive threat scenario name")
    description = Column(Text, nullable=False,
                        comment="Detailed threat scenario description with attack methodology")
    
    # STRIDE threat categorization per data-model.md
    threat_category = Column(SQLEnum(ThreatCategory), nullable=False,
                           comment="STRIDE category: SPOOFING, TAMPERING, REPUDIATION, INFORMATION_DISCLOSURE, DENIAL_OF_SERVICE, ELEVATION_OF_PRIVILEGE")
    
    # Attack vector characterization per CVSS methodology
    attack_vector = Column(SQLEnum(AttackVector), nullable=False,
                          comment="Attack access method: NETWORK, ADJACENT, LOCAL, PHYSICAL")
    attack_complexity = Column(SQLEnum(AttackComplexity), nullable=False,
                             comment="Attack execution difficulty: LOW, HIGH")
    
    # Attack path modeling per data-model.md lines 75-85
    attack_path = Column(JSON, nullable=True,
                        comment="Ordered list of attack steps from initial access to impact")
    prerequisites = Column(JSON, nullable=True,
                          comment="Required conditions for successful attack execution")
    entry_points = Column(JSON, nullable=True,
                         comment="System interfaces vulnerable to initial attack")
    
    # Threat intelligence integration
    cve_references = Column(JSON, nullable=True,
                           comment="Related CVE identifiers for known vulnerabilities")
    mitre_tactics = Column(JSON, nullable=True,
                          comment="MITRE ATT&CK tactics and techniques mapping")
    
    # AI analysis fields per FR-008, FR-010, FR-012
    confidence_score = Column(Float, nullable=True,
                            comment="AI threat identification confidence (0.0-1.0)")
    review_status = Column(SQLEnum(ReviewStatus), 
                          default=ReviewStatus.IDENTIFIED, nullable=False,
                          comment="Manual review state for uncertain threats per FR-011")
    detection_methods = Column(JSON, nullable=True,
                             comment="Automated detection capabilities")
    
    # Foreign key relationships
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False,
                     comment="Target asset for this threat scenario")
    analysis_id = Column(String(36), ForeignKey("tara_analyses.id"), nullable=False,
                        comment="Parent TARA analysis session")
    
    # Relationships per data-model.md relationship specifications
    asset = relationship("Asset", back_populates="threat_scenarios")
    analysis = relationship("TaraAnalysis", back_populates="threat_scenarios")
    impact_ratings = relationship("ImpactRating", back_populates="threat_scenario", cascade="all, delete-orphan")
    risk_values = relationship("RiskValue", back_populates="threat_scenario", cascade="all, delete-orphan")
    controls = relationship("SecurityControl", back_populates="threat_scenario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ThreatScenario(id={self.id}, name='{self.name}', category={self.threat_category}, asset_id={self.asset_id})>"
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate threat scenario per data-model.md validation rules.
        
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Threat name must be descriptive and non-empty
        if not self.name or not self.name.strip():
            errors.append("Threat scenario name must be non-empty")
        if self.name and len(self.name.strip()) < 10:
            errors.append("Threat scenario name should be descriptive (minimum 10 characters)")
            
        # Description must provide sufficient detail for analysis
        if not self.description or len(self.description.strip()) < 50:
            errors.append("Threat description must be detailed (minimum 50 characters)")
            
        # Attack path validation - must be logical sequence
        if self.attack_path:
            if not isinstance(self.attack_path, list) or len(self.attack_path) < 2:
                errors.append("Attack path must contain at least 2 sequential steps")
                
        # CVSS consistency validation
        if self.attack_vector == AttackVector.PHYSICAL and self.attack_complexity == AttackComplexity.LOW:
            # Physical attacks typically require higher complexity
            pass  # This is actually valid for some physical attacks
            
        # Confidence score validation per FR-012
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                errors.append("Confidence score must be between 0.0 and 1.0")
                
        # CVE reference format validation
        if self.cve_references:
            for cve in self.cve_references:
                if not cve.startswith('CVE-'):
                    errors.append(f"Invalid CVE format: {cve}")
                    
        return len(errors) == 0, errors
    
    def calculate_base_likelihood(self) -> float:
        """Calculate base likelihood score using CVSS-inspired methodology.
        
        Factors: Attack Vector (40%) + Attack Complexity (35%) + Prerequisites (25%)
        """
        # Attack Vector scoring (Network=1.0, Adjacent=0.8, Local=0.6, Physical=0.4)
        vector_scores = {
            AttackVector.NETWORK: 1.0,
            AttackVector.ADJACENT: 0.8,
            AttackVector.LOCAL: 0.6,
            AttackVector.PHYSICAL: 0.4
        }
        
        # Attack Complexity scoring (Low=1.0, High=0.4)
        complexity_scores = {
            AttackComplexity.LOW: 1.0,
            AttackComplexity.HIGH: 0.4
        }
        
        # Prerequisites factor (fewer prerequisites = higher likelihood)
        prereq_count = len(self.prerequisites) if self.prerequisites else 0
        prereq_factor = max(0.2, 1.0 - (prereq_count * 0.1))  # Minimum 0.2
        
        # Weighted calculation
        vector_score = vector_scores.get(self.attack_vector, 0.5) * 0.40
        complexity_score = complexity_scores.get(self.attack_complexity, 0.5) * 0.35
        prereq_score = prereq_factor * 0.25
        
        return min(1.0, vector_score + complexity_score + prereq_score)
    
    def transition_review_status(self, new_status: ReviewStatus, reason: str = None) -> bool:
        """Handle state transitions per data-model.md state transition rules."""
        valid_transitions = {
            ReviewStatus.IDENTIFIED: [ReviewStatus.UNDER_REVIEW, ReviewStatus.APPROVED],
            ReviewStatus.UNDER_REVIEW: [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.NEEDS_CLARIFICATION],
            ReviewStatus.APPROVED: [],  # Terminal state for threat scenarios
            ReviewStatus.REJECTED: [ReviewStatus.UNDER_REVIEW],
            ReviewStatus.NEEDS_CLARIFICATION: [ReviewStatus.UNDER_REVIEW]
        }
        
        if new_status in valid_transitions.get(self.review_status, []):
            self.review_status = new_status
            return True
        return False
    
    def generate_attack_graph(self) -> Dict[str, Any]:
        """Generate attack graph representation for visualization.
        
        Returns structured data for attack path visualization tools.
        """
        if not self.attack_path:
            return {}
            
        nodes = []
        edges = []
        
        # Create nodes for each attack step
        for i, step in enumerate(self.attack_path):
            nodes.append({
                'id': f'step_{i}',
                'label': step.get('name', f'Step {i+1}'),
                'description': step.get('description', ''),
                'techniques': step.get('mitre_techniques', [])
            })
            
        # Create edges between sequential steps
        for i in range(len(nodes) - 1):
            edges.append({
                'from': f'step_{i}',
                'to': f'step_{i+1}',
                'conditions': self.attack_path[i].get('success_conditions', [])
            })
            
        return {
            'nodes': nodes,
            'edges': edges,
            'entry_points': self.entry_points or [],
            'prerequisites': self.prerequisites or []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling."""
        result = super().to_dict()
        
        # Convert enums to string values
        if self.threat_category:
            result['threat_category'] = self.threat_category.value
        if self.attack_vector:
            result['attack_vector'] = self.attack_vector.value
        if self.attack_complexity:
            result['attack_complexity'] = self.attack_complexity.value
        if self.review_status:
            result['review_status'] = self.review_status.value
            
        # Include calculated fields
        result['base_likelihood'] = self.calculate_base_likelihood()
        
        return result
    
    @classmethod
    def from_stride_analysis(cls, stride_data: Dict[str, Any], asset_id: str, analysis_id: str) -> 'ThreatScenario':
        """Create ThreatScenario from STRIDE threat analysis results.
        
        Args:
            stride_data: STRIDE analysis output containing threat details
            asset_id: Target asset ID
            analysis_id: Parent analysis ID
        """
        return cls(
            name=stride_data.get('name'),
            description=stride_data.get('description'),
            threat_category=ThreatCategory(stride_data.get('stride_category')),
            attack_vector=AttackVector(stride_data.get('attack_vector', 'NETWORK')),
            attack_complexity=AttackComplexity(stride_data.get('attack_complexity', 'LOW')),
            attack_path=stride_data.get('attack_path', []),
            prerequisites=stride_data.get('prerequisites', []),
            entry_points=stride_data.get('entry_points', []),
            cve_references=stride_data.get('cve_references', []),
            mitre_tactics=stride_data.get('mitre_tactics', []),
            confidence_score=stride_data.get('confidence_score', 0.7),
            detection_methods=stride_data.get('detection_methods', []),
            asset_id=asset_id,
            analysis_id=analysis_id,
            iso_section='6.4.2'  # ISO/SAE 21434 threat analysis section
        )