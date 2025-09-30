"""
Integration test for complete TARA workflow (8 steps) per quickstart.md.

This test validates the end-to-end TARA process from asset definition
through cybersecurity goals generation using the quickstart scenario.

Test Scenario: Sample Vehicle TARA from quickstart.md lines 50-250
- 5 automotive assets (ECU Gateway, Infotainment, etc.)
- Complete 8-step ISO/SAE 21434 workflow
- Performance requirements validation
"""

import json
import pytest
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any

from autogt.cli.main import cli
from autogt.core.models import Analysis, Asset, ThreatScenario, RiskValue
from autogt.core.services.analysis_service import AnalysisService
from click.testing import CliRunner


class TestTARAWorkflow:
    """Complete TARA workflow integration test."""
    
    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_vehicle_csv(self):
        """Sample vehicle system CSV from quickstart.md."""
        csv_content = """Asset Name,Asset Type,Criticality Level,Interfaces,Description
ECU Gateway,HARDWARE,HIGH,"CAN,Ethernet",Central communication hub
Infotainment System,SOFTWARE,MEDIUM,"Bluetooth,WiFi,USB",Entertainment and navigation
Telematics Unit,HARDWARE,HIGH,"Cellular,GPS",Remote connectivity
Engine Control Module,HARDWARE,VERY_HIGH,CAN,Engine management system
OBD-II Port,HARDWARE,MEDIUM,OBD,Diagnostic interface"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            return f.name
    
    def test_complete_tara_workflow(self, runner, sample_vehicle_csv):
        """
        Test complete 8-step TARA workflow per quickstart.md.
        
        Performance Requirements (per FR-020):
        - Single asset calculation: <10 seconds
        - Full analysis (5 assets): <5 minutes
        - Batch processing: >100 analyses/minute
        """
        import time
        workflow_start = time.time()
        
        # Step 1: Create Analysis (quickstart.md lines 62-77)
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Sample Vehicle TARA',
            '--vehicle-model', 'Test Vehicle 2025',
            sample_vehicle_csv
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        analysis_id = analysis_data['analysis_id']
        
        # Validate analysis creation
        assert analysis_data['analysis_name'] == 'Sample Vehicle TARA'
        assert analysis_data['status'] == 'in_progress'
        assert analysis_data['current_step'] == 1
        assert 'created_at' in analysis_data
        
        # Step 2: Define Assets - TARA Step 1 (quickstart.md lines 79-119)
        step1_start = time.time()
        result = runner.invoke(cli, ['assets', 'define', analysis_id])
        
        assert result.exit_code == 0
        
        # Verify assets created
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_id, '--step', '1'
        ])
        assert result.exit_code == 0
        
        step1_data = json.loads(result.output)
        assert step1_data['step'] == 1
        assert step1_data['name'] == 'Asset Definition'
        assert step1_data['status'] == 'completed'
        assert step1_data['assets_count'] == 5
        
        # Validate ECU Gateway asset
        ecu_gateway = next(
            asset for asset in step1_data['assets']
            if asset['name'] == 'ECU Gateway'
        )
        assert ecu_gateway['asset_type'] == 'HARDWARE'
        assert ecu_gateway['criticality_level'] == 'HIGH'
        assert 'CAN' in ecu_gateway['interfaces']
        assert 'Ethernet' in ecu_gateway['interfaces']
        
        step1_duration = time.time() - step1_start
        assert step1_duration < 10, f"Asset definition took {step1_duration:.2f}s (>10s limit)"
        
        # Step 3: Rate Impact Levels - TARA Step 2 (quickstart.md lines 121-138)
        result = runner.invoke(cli, ['impact', 'rate', analysis_id])
        assert result.exit_code == 0
        
        # Step 4: Identify Threat Scenarios - TARA Step 3 (quickstart.md lines 140-175)
        result = runner.invoke(cli, [
            'threats', 'identify', '--auto-generate', analysis_id
        ])
        assert result.exit_code == 0
        
        # Verify threats generated
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_id, '--step', '3'
        ])
        assert result.exit_code == 0
        
        step3_data = json.loads(result.output)
        assert step3_data['threats_identified'] >= 5  # At least one per asset
        
        # Validate sample threat scenario
        threat_scenarios = step3_data['threat_scenarios']
        ecu_threats = [
            t for t in threat_scenarios
            if t['asset_name'] == 'ECU Gateway'
        ]
        assert len(ecu_threats) > 0
        
        sample_threat = ecu_threats[0]
        assert 'threat_name' in sample_threat
        assert sample_threat['threat_actor'] in ['CRIMINAL', 'NATION_STATE', 'INSIDER']
        assert 'attack_vectors' in sample_threat
        assert 'prerequisites' in sample_threat
        
        # Step 5: Analyze Attack Paths - TARA Step 4 (quickstart.md lines 177-189)
        result = runner.invoke(cli, ['attacks', 'analyze', analysis_id])
        assert result.exit_code == 0
        
        # Step 6: Rate Attack Feasibility - TARA Step 5 (quickstart.md lines 191-207)
        result = runner.invoke(cli, ['feasibility', 'rate', analysis_id])
        assert result.exit_code == 0
        
        # Step 7: Calculate Risk Values - TARA Step 6 (quickstart.md lines 209-245)
        risk_start = time.time()
        result = runner.invoke(cli, [
            'risks', 'calculate', '--method', 'iso21434', analysis_id
        ])
        assert result.exit_code == 0
        
        # Verify risk calculation performance
        risk_duration = time.time() - risk_start
        assert risk_duration < 60, f"Risk calculation took {risk_duration:.2f}s (>1min limit)"
        
        # Verify risk results
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_id, '--step', '6'
        ])
        assert result.exit_code == 0
        
        risk_data = json.loads(result.output)
        assert risk_data['risks_calculated'] > 0
        
        risk_summary = risk_data['risk_summary']
        total_risks = sum(risk_summary.values())
        assert total_risks > 0
        
        # Validate risk levels
        for level in ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']:
            assert level in risk_summary
        
        # Check highest risk entry
        highest_risks = risk_data['highest_risks']
        assert len(highest_risks) > 0
        
        top_risk = highest_risks[0]
        assert 'asset_name' in top_risk
        assert 'threat_name' in top_risk
        assert top_risk['risk_level'] in ['HIGH', 'VERY_HIGH']
        assert 0 <= top_risk['risk_score'] <= 1
        
        # Step 8: Make Treatment Decisions - TARA Step 7 (quickstart.md lines 247-266)
        result = runner.invoke(cli, ['treatments', 'decide', analysis_id])
        assert result.exit_code == 0
        
        # Step 9: Set Cybersecurity Goals - TARA Step 8 (quickstart.md lines 268-284)
        result = runner.invoke(cli, ['goals', 'generate', analysis_id])
        assert result.exit_code == 0
        
        # Verify final analysis completion
        result = runner.invoke(cli, [
            'analysis', 'show', analysis_id, '--step', '8'
        ])
        assert result.exit_code == 0
        
        final_data = json.loads(result.output)
        assert final_data['step'] == 8
        assert final_data['status'] == 'completed'
        
        # Validate overall workflow performance
        workflow_duration = time.time() - workflow_start
        assert workflow_duration < 300, f"Full workflow took {workflow_duration:.2f}s (>5min limit)"
        
        print(f"✅ Complete TARA workflow completed in {workflow_duration:.2f}s")
        
        # Cleanup
        Path(sample_vehicle_csv).unlink()
    
    def test_workflow_step_validation(self, runner, sample_vehicle_csv):
        """Test that workflow steps must be completed in order."""
        # Create analysis
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Step Validation Test',
            sample_vehicle_csv
        ])
        assert result.exit_code == 0
        
        analysis_data = json.loads(result.output)
        analysis_id = analysis_data['analysis_id']
        
        # Try to skip step 1 (assets) and go directly to step 3 (threats)
        result = runner.invoke(cli, [
            'threats', 'identify', analysis_id
        ])
        
        # Should fail due to missing prerequisite
        assert result.exit_code != 0
        assert 'prerequisite' in result.output.lower() or 'step' in result.output.lower()
        
        # Cleanup
        Path(sample_vehicle_csv).unlink()
    
    def test_workflow_data_persistence(self, runner, sample_vehicle_csv):
        """Test that workflow data persists across steps."""
        # Create and complete first few steps
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Persistence Test',
            sample_vehicle_csv
        ])
        assert result.exit_code == 0
        
        analysis_data = json.loads(result.output)
        analysis_id = analysis_data['analysis_id']
        
        # Complete asset definition
        result = runner.invoke(cli, ['assets', 'define', analysis_id])
        assert result.exit_code == 0
        
        # Verify data persists when querying later
        result = runner.invoke(cli, ['analysis', 'show', analysis_id])
        assert result.exit_code == 0
        
        analysis_state = json.loads(result.output)
        assert len(analysis_state['assets']) == 5
        assert analysis_state['current_step'] >= 1
        
        # Cleanup
        Path(sample_vehicle_csv).unlink()
    
    def test_performance_benchmarks(self, runner, sample_vehicle_csv):
        """Test performance requirements per FR-020."""
        import time
        
        # Test single asset calculation performance
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'Performance Test',
            sample_vehicle_csv
        ])
        assert result.exit_code == 0
        
        analysis_data = json.loads(result.output)
        analysis_id = analysis_data['analysis_id']
        
        # Complete setup steps
        runner.invoke(cli, ['assets', 'define', analysis_id])
        runner.invoke(cli, ['impact', 'rate', analysis_id])
        runner.invoke(cli, ['threats', 'identify', '--auto-generate', analysis_id])
        runner.invoke(cli, ['attacks', 'analyze', analysis_id])
        runner.invoke(cli, ['feasibility', 'rate', analysis_id])
        
        # Test single asset risk calculation
        single_start = time.time()
        result = runner.invoke(cli, [
            'risks', 'calculate',
            '--asset-name', 'ECU Gateway',
            analysis_id
        ])
        single_duration = time.time() - single_start
        
        assert result.exit_code == 0
        assert single_duration < 10, f"Single asset calculation: {single_duration:.2f}s (>10s limit)"
        
        # Test full analysis performance (already tested in main workflow)
        full_start = time.time()
        result = runner.invoke(cli, [
            'risks', 'calculate', '--method', 'iso21434', analysis_id
        ])
        full_duration = time.time() - full_start
        
        assert result.exit_code == 0
        assert full_duration < 60, f"Full analysis calculation: {full_duration:.2f}s (>1min limit)"
        
        print(f"✅ Performance benchmarks: Single={single_duration:.2f}s, Full={full_duration:.2f}s")
        
        # Cleanup
        Path(sample_vehicle_csv).unlink()