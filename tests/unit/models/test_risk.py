"""
Unit tests for RiskValue calculation per data-model.md risk calculation rules.

This test validates all RiskValue model functionality including:
- Risk calculation algorithms per ISO/SAE 21434
- Impact and likelihood assessment
- Risk level determination and thresholds
- Risk aggregation and scoring methods
- Treatment recommendation logic

Test Coverage:
- Risk calculation methodology validation
- ISO/SAE 21434 compliance verification
- Risk level threshold management
- Impact and likelihood combination rules
- Edge cases and boundary conditions
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal

from autogt.core.models.risk import (
    RiskValue, RiskLevel, ImpactLevel, LikelihoodLevel,
    RiskCalculationMethod, RiskMatrix, TreatmentRecommendation
)
from autogt.core.models.threat import ThreatScenario, ThreatActor, ThreatCategory, ThreatMotivation
from autogt.core.models.asset import Asset, AssetType, CriticalityLevel
from autogt.core.models.analysis import Analysis


class TestRiskValueModel:
    """RiskValue calculation validation unit tests."""
    
    def test_risk_value_creation_with_valid_data(self):
        """Test RiskValue creation with all valid data."""
        analysis = Analysis(
            id=uuid4(),
            name="Risk Test Analysis",
            vehicle_model="Test Vehicle",
            current_step=6,
            created_at=datetime.utcnow()
        )
        
        asset = Asset(
            id=uuid4(),
            analysis_id=analysis.id,
            name="ECU Gateway",
            asset_type=AssetType.HARDWARE,
            criticality_level=CriticalityLevel.HIGH
        )
        
        threat = ThreatScenario(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_name="Remote Code Execution",
            threat_category=ThreatCategory.REMOTE_EXECUTION,
            threat_actor=ThreatActor.CRIMINAL,
            motivation=ThreatMotivation.FINANCIAL_GAIN
        )
        
        risk = RiskValue(
            id=uuid4(),
            analysis_id=analysis.id,
            asset_id=asset.id,
            threat_id=threat.id,
            impact_level=ImpactLevel.HIGH,
            likelihood_level=LikelihoodLevel.MEDIUM,
            risk_level=RiskLevel.HIGH,
            risk_score=Decimal('0.75'),
            calculation_method=RiskCalculationMethod.ISO21434,
            created_at=datetime.utcnow()
        )
        
        # Validate all fields are set correctly
        assert risk.impact_level == ImpactLevel.HIGH
        assert risk.likelihood_level == LikelihoodLevel.MEDIUM
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.risk_score == Decimal('0.75')
        assert risk.calculation_method == RiskCalculationMethod.ISO21434
        assert isinstance(risk.id, UUID)
        assert isinstance(risk.analysis_id, UUID)
        assert isinstance(risk.asset_id, UUID)
        assert isinstance(risk.threat_id, UUID)
        assert isinstance(risk.created_at, datetime)
    
    def test_iso21434_risk_calculation(self):
        """Test ISO/SAE 21434 compliant risk calculation."""
        # Test all combinations of impact and likelihood per ISO/SAE 21434
        iso_test_cases = [
            # (impact, likelihood, expected_risk_level, min_score, max_score)
            (ImpactLevel.NEGLIGIBLE, LikelihoodLevel.VERY_LOW, RiskLevel.LOW, 0.0, 0.2),
            (ImpactLevel.NEGLIGIBLE, LikelihoodLevel.LOW, RiskLevel.LOW, 0.0, 0.3),
            (ImpactLevel.NEGLIGIBLE, LikelihoodLevel.MEDIUM, RiskLevel.MEDIUM, 0.2, 0.5),
            (ImpactLevel.NEGLIGIBLE, LikelihoodLevel.HIGH, RiskLevel.MEDIUM, 0.3, 0.6),
            (ImpactLevel.NEGLIGIBLE, LikelihoodLevel.VERY_HIGH, RiskLevel.HIGH, 0.4, 0.7),
            
            (ImpactLevel.MODERATE, LikelihoodLevel.VERY_LOW, RiskLevel.LOW, 0.1, 0.3),
            (ImpactLevel.MODERATE, LikelihoodLevel.LOW, RiskLevel.MEDIUM, 0.2, 0.4),
            (ImpactLevel.MODERATE, LikelihoodLevel.MEDIUM, RiskLevel.MEDIUM, 0.3, 0.6),
            (ImpactLevel.MODERATE, LikelihoodLevel.HIGH, RiskLevel.HIGH, 0.5, 0.8),
            (ImpactLevel.MODERATE, LikelihoodLevel.VERY_HIGH, RiskLevel.HIGH, 0.6, 0.9),
            
            (ImpactLevel.MAJOR, LikelihoodLevel.VERY_LOW, RiskLevel.MEDIUM, 0.2, 0.4),
            (ImpactLevel.MAJOR, LikelihoodLevel.LOW, RiskLevel.MEDIUM, 0.3, 0.5),
            (ImpactLevel.MAJOR, LikelihoodLevel.MEDIUM, RiskLevel.HIGH, 0.5, 0.7),
            (ImpactLevel.MAJOR, LikelihoodLevel.HIGH, RiskLevel.HIGH, 0.6, 0.9),
            (ImpactLevel.MAJOR, LikelihoodLevel.VERY_HIGH, RiskLevel.VERY_HIGH, 0.7, 1.0),
            
            (ImpactLevel.SEVERE, LikelihoodLevel.VERY_LOW, RiskLevel.MEDIUM, 0.3, 0.5),
            (ImpactLevel.SEVERE, LikelihoodLevel.LOW, RiskLevel.HIGH, 0.4, 0.6),
            (ImpactLevel.SEVERE, LikelihoodLevel.MEDIUM, RiskLevel.HIGH, 0.6, 0.8),
            (ImpactLevel.SEVERE, LikelihoodLevel.HIGH, RiskLevel.VERY_HIGH, 0.7, 0.9),
            (ImpactLevel.SEVERE, LikelihoodLevel.VERY_HIGH, RiskLevel.VERY_HIGH, 0.8, 1.0)
        ]
        
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        for impact, likelihood, expected_level, min_score, max_score in iso_test_cases:
            risk = RiskValue.calculate_iso21434_risk(
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=threat_id,
                impact_level=impact,
                likelihood_level=likelihood
            )
            
            # Validate calculated risk level
            assert risk.risk_level == expected_level, \
                f"Impact {impact} + Likelihood {likelihood} should yield {expected_level}, got {risk.risk_level}"
            
            # Validate risk score is within expected range
            score_float = float(risk.risk_score)
            assert min_score <= score_float <= max_score, \
                f"Risk score {score_float} outside range [{min_score}, {max_score}] for {impact}/{likelihood}"
            
            # Validate calculation method
            assert risk.calculation_method == RiskCalculationMethod.ISO21434
    
    def test_risk_level_thresholds(self):
        """Test risk level threshold validation per data-model.md."""
        # Default ISO/SAE 21434 thresholds
        default_thresholds = {
            RiskLevel.LOW: (0.0, 0.3),
            RiskLevel.MEDIUM: (0.3, 0.6),
            RiskLevel.HIGH: (0.6, 0.8),
            RiskLevel.VERY_HIGH: (0.8, 1.0)
        }
        
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test each threshold boundary
        for risk_level, (min_threshold, max_threshold) in default_thresholds.items():
            # Test minimum boundary
            min_risk = RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=threat_id,
                impact_level=ImpactLevel.MODERATE,
                likelihood_level=LikelihoodLevel.LOW,
                risk_level=risk_level,
                risk_score=Decimal(str(min_threshold)),
                calculation_method=RiskCalculationMethod.ISO21434
            )
            
            assert min_risk.is_within_threshold()
            
            # Test maximum boundary
            max_risk = RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=threat_id,
                impact_level=ImpactLevel.MODERATE,
                likelihood_level=LikelihoodLevel.LOW,
                risk_level=risk_level,
                risk_score=Decimal(str(max_threshold)),
                calculation_method=RiskCalculationMethod.ISO21434
            )
            
            assert max_risk.is_within_threshold()
    
    def test_custom_risk_thresholds(self):
        """Test custom risk threshold configuration."""
        # Custom thresholds for specific use case
        custom_thresholds = {
            'low_max': 0.2,
            'medium_max': 0.5,
            'high_max': 0.75,
            'very_high_min': 0.75
        }
        
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test risk calculation with custom thresholds
        risk = RiskValue.calculate_with_custom_thresholds(
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.MEDIUM,
            thresholds=custom_thresholds
        )
        
        # Score should be calculated and level assigned based on custom thresholds
        score_float = float(risk.risk_score)
        
        if score_float <= 0.2:
            assert risk.risk_level == RiskLevel.LOW
        elif score_float <= 0.5:
            assert risk.risk_level == RiskLevel.MEDIUM
        elif score_float <= 0.75:
            assert risk.risk_level == RiskLevel.HIGH
        else:
            assert risk.risk_level == RiskLevel.VERY_HIGH
    
    def test_impact_level_assessment(self):
        """Test impact level assessment logic."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test impact levels with different asset criticalities
        criticality_impact_mapping = [
            (CriticalityLevel.LOW, ImpactLevel.NEGLIGIBLE, ImpactLevel.MODERATE),
            (CriticalityLevel.MEDIUM, ImpactLevel.MODERATE, ImpactLevel.MAJOR),
            (CriticalityLevel.HIGH, ImpactLevel.MAJOR, ImpactLevel.SEVERE),
            (CriticalityLevel.VERY_HIGH, ImpactLevel.SEVERE, ImpactLevel.SEVERE)
        ]
        
        for criticality, min_impact, max_impact in criticality_impact_mapping:
            # Create asset with specific criticality
            asset = Asset(
                id=asset_id,
                analysis_id=analysis_id,
                name="Test Asset",
                asset_type=AssetType.HARDWARE,
                criticality_level=criticality
            )
            
            # Test impact assessment
            assessed_impact = RiskValue.assess_impact_for_asset(
                asset=asset,
                threat_category=ThreatCategory.REMOTE_EXECUTION
            )
            
            # Impact should be within expected range for asset criticality
            impact_values = [ImpactLevel.NEGLIGIBLE, ImpactLevel.MODERATE, ImpactLevel.MAJOR, ImpactLevel.SEVERE]
            min_index = impact_values.index(min_impact)
            max_index = impact_values.index(max_impact)
            assessed_index = impact_values.index(assessed_impact)
            
            assert min_index <= assessed_index <= max_index, \
                f"Impact {assessed_impact} outside expected range [{min_impact}, {max_impact}] for criticality {criticality}"
    
    def test_likelihood_assessment(self):
        """Test likelihood assessment based on threat characteristics."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test likelihood assessment for different threat actors
        actor_likelihood_mapping = [
            (ThreatActor.SCRIPT_KIDDIE, LikelihoodLevel.LOW, LikelihoodLevel.MEDIUM),
            (ThreatActor.CRIMINAL, LikelihoodLevel.MEDIUM, LikelihoodLevel.HIGH),
            (ThreatActor.INSIDER, LikelihoodLevel.MEDIUM, LikelihoodLevel.HIGH),
            (ThreatActor.NATION_STATE, LikelihoodLevel.LOW, LikelihoodLevel.MEDIUM),  # High capability but targeted
            (ThreatActor.HACKTIVIST, LikelihoodLevel.LOW, LikelihoodLevel.MEDIUM)
        ]
        
        for actor, min_likelihood, max_likelihood in actor_likelihood_mapping:
            # Create threat with specific actor
            threat = ThreatScenario(
                id=threat_id,
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_name="Test Threat",
                threat_category=ThreatCategory.REMOTE_EXECUTION,
                threat_actor=actor,
                motivation=ThreatMotivation.FINANCIAL_GAIN,
                attack_vectors=["Network attack"],
                prerequisites=["Network access"]
            )
            
            # Assess likelihood
            assessed_likelihood = RiskValue.assess_likelihood_for_threat(threat)
            
            # Likelihood should be within expected range for threat actor
            likelihood_values = [LikelihoodLevel.VERY_LOW, LikelihoodLevel.LOW, LikelihoodLevel.MEDIUM, 
                               LikelihoodLevel.HIGH, LikelihoodLevel.VERY_HIGH]
            min_index = likelihood_values.index(min_likelihood)
            max_index = likelihood_values.index(max_likelihood)
            assessed_index = likelihood_values.index(assessed_likelihood)
            
            assert min_index <= assessed_index <= max_index, \
                f"Likelihood {assessed_likelihood} outside expected range [{min_likelihood}, {max_likelihood}] for actor {actor}"
    
    def test_risk_aggregation(self):
        """Test risk aggregation across multiple threats for an asset."""
        analysis_id = uuid4()
        asset_id = uuid4()
        
        # Create multiple risks for the same asset
        risks = [
            RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=uuid4(),
                impact_level=ImpactLevel.MAJOR,
                likelihood_level=LikelihoodLevel.HIGH,
                risk_level=RiskLevel.HIGH,
                risk_score=Decimal('0.7'),
                calculation_method=RiskCalculationMethod.ISO21434
            ),
            RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=uuid4(),
                impact_level=ImpactLevel.MODERATE,
                likelihood_level=LikelihoodLevel.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                risk_score=Decimal('0.4'),
                calculation_method=RiskCalculationMethod.ISO21434
            ),
            RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=uuid4(),
                impact_level=ImpactLevel.SEVERE,
                likelihood_level=LikelihoodLevel.LOW,
                risk_level=RiskLevel.MEDIUM,
                risk_score=Decimal('0.5'),
                calculation_method=RiskCalculationMethod.ISO21434
            )
        ]
        
        # Test aggregation methods
        
        # 1. Maximum risk (conservative approach)
        max_aggregated = RiskValue.aggregate_risks_maximum(risks)
        assert max_aggregated.risk_level == RiskLevel.HIGH
        assert max_aggregated.risk_score == Decimal('0.7')
        
        # 2. Average risk
        avg_aggregated = RiskValue.aggregate_risks_average(risks)
        expected_avg = (Decimal('0.7') + Decimal('0.4') + Decimal('0.5')) / 3
        assert abs(avg_aggregated.risk_score - expected_avg) < Decimal('0.01')
        
        # 3. Weighted average (by impact level)
        weighted_aggregated = RiskValue.aggregate_risks_weighted(risks)
        # Higher impact should have more weight in aggregation
        assert weighted_aggregated.risk_score > avg_aggregated.risk_score
    
    def test_treatment_recommendation_logic(self):
        """Test treatment recommendation based on risk level and characteristics."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test recommendations for different risk levels
        risk_treatment_mapping = [
            (RiskLevel.LOW, [TreatmentRecommendation.ACCEPT, TreatmentRecommendation.MONITOR]),
            (RiskLevel.MEDIUM, [TreatmentRecommendation.MITIGATE, TreatmentRecommendation.TRANSFER]),
            (RiskLevel.HIGH, [TreatmentRecommendation.MITIGATE, TreatmentRecommendation.AVOID]),
            (RiskLevel.VERY_HIGH, [TreatmentRecommendation.MITIGATE, TreatmentRecommendation.AVOID])
        ]
        
        for risk_level, expected_recommendations in risk_treatment_mapping:
            risk = RiskValue(
                id=uuid4(),
                analysis_id=analysis_id,
                asset_id=asset_id,
                threat_id=threat_id,
                impact_level=ImpactLevel.MODERATE,
                likelihood_level=LikelihoodLevel.MEDIUM,
                risk_level=risk_level,
                risk_score=Decimal('0.5'),
                calculation_method=RiskCalculationMethod.ISO21434
            )
            
            recommendations = risk.get_treatment_recommendations()
            
            # Should have at least one recommended treatment
            assert len(recommendations) > 0
            
            # All recommendations should be from expected list
            for rec in recommendations:
                assert rec in expected_recommendations
    
    def test_risk_matrix_validation(self):
        """Test risk matrix implementation per ISO/SAE 21434."""
        # Standard 5x5 risk matrix
        matrix = RiskMatrix.iso21434_standard()
        
        # Test all matrix positions
        impact_levels = [ImpactLevel.NEGLIGIBLE, ImpactLevel.MODERATE, ImpactLevel.MAJOR, ImpactLevel.SEVERE]
        likelihood_levels = [LikelihoodLevel.VERY_LOW, LikelihoodLevel.LOW, LikelihoodLevel.MEDIUM, 
                           LikelihoodLevel.HIGH, LikelihoodLevel.VERY_HIGH]
        
        for impact in impact_levels:
            for likelihood in likelihood_levels:
                risk_level = matrix.get_risk_level(impact, likelihood)
                risk_score = matrix.get_risk_score(impact, likelihood)
                
                # Risk level should be valid
                assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.VERY_HIGH]
                
                # Risk score should be between 0 and 1
                assert 0 <= risk_score <= 1
                
                # Higher impact/likelihood should generally yield higher risk
                # (with some exceptions due to discrete levels)
    
    def test_risk_score_precision(self):
        """Test risk score calculation precision and rounding."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test precision handling
        precise_risk = RiskValue(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.HIGH,
            risk_level=RiskLevel.HIGH,
            risk_score=Decimal('0.123456789'),  # High precision
            calculation_method=RiskCalculationMethod.ISO21434
        )
        
        # Score should be rounded to appropriate precision (2-3 decimal places)
        formatted_score = precise_risk.get_formatted_score()
        assert len(formatted_score.split('.')[-1]) <= 3  # Max 3 decimal places
        
        # Test score validation ranges
        assert 0 <= precise_risk.risk_score <= 1
    
    def test_risk_calculation_edge_cases(self):
        """Test risk calculation edge cases and boundary conditions."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        # Test minimum risk (negligible impact, very low likelihood)
        min_risk = RiskValue.calculate_iso21434_risk(
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.NEGLIGIBLE,
            likelihood_level=LikelihoodLevel.VERY_LOW
        )
        
        assert min_risk.risk_level == RiskLevel.LOW
        assert min_risk.risk_score <= Decimal('0.2')
        
        # Test maximum risk (severe impact, very high likelihood)
        max_risk = RiskValue.calculate_iso21434_risk(
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.SEVERE,
            likelihood_level=LikelihoodLevel.VERY_HIGH
        )
        
        assert max_risk.risk_level == RiskLevel.VERY_HIGH
        assert max_risk.risk_score >= Decimal('0.8')
        
        # Test risk calculation consistency
        # Same input should yield same output
        risk1 = RiskValue.calculate_iso21434_risk(
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.MEDIUM
        )
        
        risk2 = RiskValue.calculate_iso21434_risk(
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.MEDIUM
        )
        
        assert risk1.risk_score == risk2.risk_score
        assert risk1.risk_level == risk2.risk_level
    
    def test_risk_serialization(self):
        """Test risk model serialization and deserialization."""
        analysis_id = uuid4()
        asset_id = uuid4()
        threat_id = uuid4()
        
        original_risk = RiskValue(
            id=uuid4(),
            analysis_id=analysis_id,
            asset_id=asset_id,
            threat_id=threat_id,
            impact_level=ImpactLevel.MAJOR,
            likelihood_level=LikelihoodLevel.HIGH,
            risk_level=RiskLevel.HIGH,
            risk_score=Decimal('0.75'),
            calculation_method=RiskCalculationMethod.ISO21434,
            justification="High impact due to safety implications, high likelihood based on threat actor capabilities",
            created_at=datetime.utcnow()
        )
        
        # Test JSON serialization
        risk_dict = original_risk.to_dict()
        
        # Validate serialized structure
        assert risk_dict['id'] == str(original_risk.id)
        assert risk_dict['analysis_id'] == str(original_risk.analysis_id)
        assert risk_dict['asset_id'] == str(original_risk.asset_id)
        assert risk_dict['threat_id'] == str(original_risk.threat_id)
        assert risk_dict['impact_level'] == original_risk.impact_level.value
        assert risk_dict['likelihood_level'] == original_risk.likelihood_level.value
        assert risk_dict['risk_level'] == original_risk.risk_level.value
        assert risk_dict['risk_score'] == float(original_risk.risk_score)
        assert risk_dict['calculation_method'] == original_risk.calculation_method.value
        
        # Test deserialization
        reconstructed_risk = RiskValue.from_dict(risk_dict)
        
        assert reconstructed_risk.id == original_risk.id
        assert reconstructed_risk.analysis_id == original_risk.analysis_id
        assert reconstructed_risk.asset_id == original_risk.asset_id
        assert reconstructed_risk.threat_id == original_risk.threat_id
        assert reconstructed_risk.impact_level == original_risk.impact_level
        assert reconstructed_risk.likelihood_level == original_risk.likelihood_level
        assert reconstructed_risk.risk_level == original_risk.risk_level
        assert reconstructed_risk.risk_score == original_risk.risk_score
        assert reconstructed_risk.calculation_method == original_risk.calculation_method