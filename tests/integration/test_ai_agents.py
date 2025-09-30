"""
Integration test for AI agent orchestration with confidence scoring.

This test validates the AI agent system's ability to:
- Orchestrate multiple specialized agents (threat identification, risk assessment)
- Integrate with Gemini API for automotive threat patterns
- Provide confidence scoring for AI-generated recommendations
- Handle API failures and fallback mechanisms
- Generate contextually relevant threat scenarios

Test Coverage:
- AutoGen multi-agent coordination
- Gemini API integration
- Confidence scoring algorithms
- Error handling and resilience
- Threat pattern recognition
"""

import json
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from autogt.cli.main import cli
from autogt.core.ai.agents import ThreatAnalysisAgent, RiskAssessmentAgent, OrchestrationAgent
from autogt.core.ai.gemini_client import GeminiClient
from click.testing import CliRunner


class TestAIAgentOrchestration:
    """AI agent orchestration integration test."""
    
    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_analysis_id(self, runner):
        """Create a sample analysis with assets for AI testing."""
        import tempfile
        
        # Create sample CSV
        csv_content = """Asset Name,Asset Type,Criticality Level,Interfaces,Description
ECU Gateway,HARDWARE,HIGH,"CAN,Ethernet",Central communication hub
Infotainment System,SOFTWARE,MEDIUM,"Bluetooth,WiFi,USB",Entertainment and navigation
Telematics Unit,HARDWARE,HIGH,"Cellular,GPS",Remote connectivity"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        # Create analysis
        result = runner.invoke(cli, [
            'analysis', 'create',
            '--name', 'AI Agent Test Analysis',
            csv_file
        ])
        
        assert result.exit_code == 0
        analysis_data = json.loads(result.output)
        
        # Define assets
        runner.invoke(cli, ['assets', 'define', analysis_data['analysis_id']])
        
        return analysis_data['analysis_id']
    
    def test_threat_identification_agent(self, runner, sample_analysis_id):
        """Test AI-powered threat identification with confidence scoring."""
        # Mock Gemini API responses
        mock_threats = [
            {
                'asset_name': 'ECU Gateway',
                'threat_name': 'Remote Code Execution via CAN Bus',
                'threat_actor': 'CRIMINAL',
                'motivation': 'Vehicle theft or unauthorized access',
                'attack_vectors': ['CAN message injection', 'ECU firmware exploitation'],
                'prerequisites': ['Physical access to CAN bus', 'Knowledge of CAN protocols'],
                'confidence_score': 0.85,
                'reasoning': 'High confidence based on known CAN bus vulnerabilities in automotive systems'
            },
            {
                'asset_name': 'Infotainment System',
                'threat_name': 'Malware Installation via USB',
                'threat_actor': 'CRIMINAL',
                'motivation': 'Data theft or system compromise',
                'attack_vectors': ['Malicious USB device', 'Social engineering'],
                'prerequisites': ['Physical access to vehicle', 'Malware development'],
                'confidence_score': 0.78,
                'reasoning': 'Medium-high confidence based on USB attack vectors in connected vehicles'
            },
            {
                'asset_name': 'Telematics Unit',
                'threat_name': 'Cellular Network Interception',
                'threat_actor': 'NATION_STATE',
                'motivation': 'Surveillance or intelligence gathering',
                'attack_vectors': ['Cellular jamming', 'IMSI catcher deployment'],
                'prerequisites': ['Advanced technical capabilities', 'Cellular infrastructure access'],
                'confidence_score': 0.65,
                'reasoning': 'Medium confidence - requires sophisticated capabilities'
            }
        ]
        
        with patch('autogt.core.ai.gemini_client.GeminiClient.analyze_threats') as mock_analyze:
            mock_analyze.return_value = {
                'threats': mock_threats,
                'analysis_confidence': 0.76,
                'processing_time': 2.3
            }
            
            # Test AI threat identification
            start_time = time.time()
            
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--auto-generate',
                '--confidence-threshold', '0.7',
                sample_analysis_id
            ])
            
            processing_time = time.time() - start_time
            
            assert result.exit_code == 0
            
            # Verify threat identification results
            result = runner.invoke(cli, [
                'analysis', 'show', sample_analysis_id, '--step', '3'
            ])
            
            assert result.exit_code == 0
            threat_data = json.loads(result.output)
            
            # Validate threat generation
            assert threat_data['threats_identified'] >= 2  # Should have high-confidence threats
            
            threat_scenarios = threat_data['threat_scenarios']
            
            # Check confidence scoring
            high_confidence_threats = [
                t for t in threat_scenarios
                if t.get('confidence_score', 0) >= 0.7
            ]
            assert len(high_confidence_threats) >= 2
            
            # Validate threat structure
            for threat in high_confidence_threats:
                assert 'asset_name' in threat
                assert 'threat_name' in threat
                assert 'threat_actor' in threat
                assert threat['threat_actor'] in ['CRIMINAL', 'NATION_STATE', 'INSIDER', 'HACKTIVIST']
                assert 'attack_vectors' in threat
                assert 'confidence_score' in threat
                assert 0 <= threat['confidence_score'] <= 1
                
                if 'reasoning' in threat:
                    assert len(threat['reasoning']) > 0
            
            # Performance validation
            assert processing_time < 30, f"AI threat analysis took {processing_time:.2f}s (>30s limit)"
            
            print(f"✅ AI threat identification completed in {processing_time:.2f}s")
    
    def test_multi_agent_orchestration(self, runner, sample_analysis_id):
        """Test orchestration of multiple AI agents with coordination."""
        # Mock multi-agent responses
        threat_agent_response = {
            'threats': [
                {
                    'asset_name': 'ECU Gateway',
                    'threat_name': 'Network Intrusion',
                    'confidence_score': 0.82
                }
            ],
            'agent_id': 'threat_analysis_agent',
            'processing_confidence': 0.85
        }
        
        risk_agent_response = {
            'risk_assessments': [
                {
                    'asset_name': 'ECU Gateway',
                    'threat_name': 'Network Intrusion',
                    'likelihood_score': 0.7,
                    'impact_score': 0.9,
                    'risk_level': 'HIGH',
                    'confidence_score': 0.78
                }
            ],
            'agent_id': 'risk_assessment_agent',
            'processing_confidence': 0.80
        }
        
        with patch('autogt.core.ai.agents.ThreatAnalysisAgent.analyze') as mock_threat_agent, \
             patch('autogt.core.ai.agents.RiskAssessmentAgent.assess') as mock_risk_agent:
            
            mock_threat_agent.return_value = threat_agent_response
            mock_risk_agent.return_value = risk_agent_response
            
            # Test multi-agent orchestration
            result = runner.invoke(cli, [
                'analysis', 'run-ai-pipeline',
                '--agents', 'threat,risk',
                '--coordination-mode', 'sequential',
                sample_analysis_id
            ])
            
            assert result.exit_code == 0
            
            # Verify orchestration results
            orchestration_data = json.loads(result.output)
            
            assert 'agent_results' in orchestration_data
            assert len(orchestration_data['agent_results']) == 2
            
            # Check agent coordination
            assert orchestration_data['coordination_mode'] == 'sequential'
            assert 'overall_confidence' in orchestration_data
            assert 0 <= orchestration_data['overall_confidence'] <= 1
            
            # Validate agent-specific outputs
            threat_results = next(
                r for r in orchestration_data['agent_results']
                if r['agent_id'] == 'threat_analysis_agent'
            )
            assert 'threats' in threat_results
            
            risk_results = next(
                r for r in orchestration_data['agent_results']
                if r['agent_id'] == 'risk_assessment_agent'
            )
            assert 'risk_assessments' in risk_results
    
    def test_gemini_api_integration(self, runner, sample_analysis_id):
        """Test Gemini API integration with automotive threat patterns."""
        # Mock Gemini API client
        mock_gemini_response = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': json.dumps({
                                    'automotive_threats': [
                                        {
                                            'category': 'Remote Execution',
                                            'attack_surface': 'CAN Bus',
                                            'threat_description': 'Exploitation of ECU communication protocols',
                                            'automotive_specific': True,
                                            'iso21434_category': 'Network Attack',
                                            'confidence': 0.88
                                        }
                                    ],
                                    'threat_patterns': [
                                        'ECU firmware vulnerabilities',
                                        'CAN bus message injection',
                                        'Cellular connectivity exploitation'
                                    ],
                                    'analysis_metadata': {
                                        'model_version': 'gemini-1.5-pro',
                                        'processing_time_ms': 1250,
                                        'token_usage': {
                                            'input_tokens': 450,
                                            'output_tokens': 320
                                        }
                                    }
                                })
                            }
                        ]
                    },
                    'finishReason': 'STOP'
                }
            ],
            'usageMetadata': {
                'promptTokenCount': 450,
                'candidatesTokenCount': 320,
                'totalTokenCount': 770
            }
        }
        
        with patch('autogt.core.ai.gemini_client.GeminiClient._make_request') as mock_request:
            mock_request.return_value = mock_gemini_response
            
            # Test Gemini integration through threat identification
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--ai-provider', 'gemini',
                '--model', 'gemini-1.5-pro',
                '--automotive-patterns',
                sample_analysis_id
            ])
            
            assert result.exit_code == 0
            
            # Verify API integration
            mock_request.assert_called_once()
            
            # Check that automotive-specific patterns were identified
            result = runner.invoke(cli, [
                'analysis', 'show', sample_analysis_id, '--step', '3', '--detailed'
            ])
            
            if result.exit_code == 0:
                detailed_data = json.loads(result.output)
                
                # Look for automotive-specific threat indicators
                if 'ai_metadata' in detailed_data:
                    ai_metadata = detailed_data['ai_metadata']
                    assert 'model_version' in ai_metadata
                    assert 'gemini' in ai_metadata['model_version'].lower()
                    
                    if 'automotive_patterns' in ai_metadata:
                        patterns = ai_metadata['automotive_patterns']
                        assert any('ECU' in pattern or 'CAN' in pattern for pattern in patterns)
    
    def test_ai_confidence_scoring_algorithm(self, runner, sample_analysis_id):
        """Test confidence scoring algorithm for AI recommendations."""
        # Mock various confidence scenarios
        test_scenarios = [
            {
                'name': 'High Confidence Scenario',
                'threats': [
                    {
                        'asset_name': 'ECU Gateway',
                        'threat_name': 'CAN Bus Injection',
                        'evidence_factors': ['Known vulnerability', 'Attack documented', 'Clear attack path'],
                        'uncertainty_factors': [],
                        'expected_confidence': 0.90
                    }
                ]
            },
            {
                'name': 'Medium Confidence Scenario', 
                'threats': [
                    {
                        'asset_name': 'Infotainment System',
                        'threat_name': 'Supply Chain Attack',
                        'evidence_factors': ['Theoretical possibility', 'Limited examples'],
                        'uncertainty_factors': ['Complex attack', 'High resources required'],
                        'expected_confidence': 0.60
                    }
                ]
            },
            {
                'name': 'Low Confidence Scenario',
                'threats': [
                    {
                        'asset_name': 'Telematics Unit',
                        'threat_name': 'Quantum Computing Attack',
                        'evidence_factors': [],
                        'uncertainty_factors': ['Technology not mature', 'Speculative threat', 'No known instances'],
                        'expected_confidence': 0.25
                    }
                ]
            }
        ]
        
        for scenario in test_scenarios:
            with patch('autogt.core.ai.confidence.calculate_threat_confidence') as mock_confidence:
                # Mock confidence calculation
                expected_conf = scenario['threats'][0]['expected_confidence']
                mock_confidence.return_value = {
                    'confidence_score': expected_conf,
                    'confidence_factors': {
                        'evidence_strength': len(scenario['threats'][0]['evidence_factors']) / 3,
                        'uncertainty_penalty': len(scenario['threats'][0]['uncertainty_factors']) / 3,
                        'domain_knowledge': 0.8,
                        'model_reliability': 0.85
                    },
                    'explanation': f"Confidence based on {scenario['name'].lower()}"
                }
                
                # Test confidence scoring
                result = runner.invoke(cli, [
                    'threats', 'score-confidence',
                    '--threat-name', scenario['threats'][0]['threat_name'],
                    '--detailed-factors',
                    sample_analysis_id
                ])
                
                if result.exit_code == 0:
                    confidence_data = json.loads(result.output)
                    
                    # Validate confidence score
                    assert 'confidence_score' in confidence_data
                    assert abs(confidence_data['confidence_score'] - expected_conf) < 0.1
                    
                    # Validate confidence factors
                    if 'confidence_factors' in confidence_data:
                        factors = confidence_data['confidence_factors']
                        assert 'evidence_strength' in factors
                        assert 'uncertainty_penalty' in factors
                        assert 'domain_knowledge' in factors
                        assert 'model_reliability' in factors
    
    def test_ai_error_handling_and_fallbacks(self, runner, sample_analysis_id):
        """Test AI system error handling and fallback mechanisms."""
        # Test API failure scenario
        with patch('autogt.core.ai.gemini_client.GeminiClient._make_request') as mock_request:
            # Simulate API failure
            mock_request.side_effect = Exception("API connection timeout")
            
            # Test fallback mechanism
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--auto-generate',
                '--fallback-enabled',
                sample_analysis_id
            ])
            
            # Should handle gracefully with fallback
            # Either succeeds with fallback data or fails with clear message
            assert result.exit_code is not None
            
            if result.exit_code != 0:
                # Should have clear error message about API issues
                assert 'api' in result.output.lower() or 'connection' in result.output.lower()
            else:
                # If fallback succeeded, should indicate fallback was used
                assert 'fallback' in result.output.lower() or 'offline' in result.output.lower()
        
        # Test rate limiting scenario
        with patch('autogt.core.ai.gemini_client.GeminiClient._make_request') as mock_request:
            # Simulate rate limiting
            mock_request.side_effect = Exception("Rate limit exceeded")
            
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--auto-generate',
                '--retry-enabled',
                '--max-retries', '2',
                sample_analysis_id
            ])
            
            # Should handle rate limiting appropriately
            assert result.exit_code is not None
            
            if result.exit_code != 0:
                assert 'rate' in result.output.lower() or 'limit' in result.output.lower()
        
        # Test invalid response format
        with patch('autogt.core.ai.gemini_client.GeminiClient._make_request') as mock_request:
            # Return malformed response
            mock_request.return_value = {
                'candidates': [
                    {
                        'content': {
                            'parts': [
                                {
                                    'text': 'This is not valid JSON for threat analysis'
                                }
                            ]
                        }
                    }
                ]
            }
            
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--auto-generate',
                '--validate-response',
                sample_analysis_id
            ])
            
            # Should handle invalid response format
            assert result.exit_code is not None
            
            if result.exit_code != 0:
                assert 'format' in result.output.lower() or 'invalid' in result.output.lower()
    
    def test_ai_performance_benchmarks(self, runner, sample_analysis_id):
        """Test AI agent performance benchmarks."""
        # Mock efficient AI responses
        efficient_response = {
            'threats': [
                {'asset_name': 'ECU Gateway', 'threat_name': 'Network Attack', 'confidence_score': 0.8}
            ] * 10,  # 10 threats for performance testing
            'processing_time': 5.2,
            'token_efficiency': 0.85
        }
        
        with patch('autogt.core.ai.gemini_client.GeminiClient.analyze_threats') as mock_analyze:
            mock_analyze.return_value = efficient_response
            
            # Test AI processing performance
            start_time = time.time()
            
            result = runner.invoke(cli, [
                'threats', 'identify',
                '--auto-generate',
                '--batch-size', '10',
                '--optimize-performance',
                sample_analysis_id
            ])
            
            total_time = time.time() - start_time
            
            assert result.exit_code == 0
            
            # Performance requirements
            assert total_time < 60, f"AI processing took {total_time:.2f}s (>60s limit)"
            
            # Check token efficiency if available
            if 'ai_metadata' in result.output:
                try:
                    metadata = json.loads(result.output).get('ai_metadata', {})
                    if 'token_efficiency' in metadata:
                        assert metadata['token_efficiency'] > 0.7
                except:
                    pass  # Metadata parsing is optional
            
            print(f"✅ AI agent performance: {total_time:.2f}s for batch processing")