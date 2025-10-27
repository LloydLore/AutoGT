import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.orm import Session

from autogt.cli.commands.threats import _ai_threat_identification
from autogt.models.analysis import TaraAnalysis, AnalysisPhase, CompletionStatus
from autogt.models.asset import Asset, AssetType, CriticalityLevel
from autogt.lib.config import Config
from autogt.lib.exceptions import AutoGTError

class TestAIThreatIdentification:
    """Test suit for AI-powered threat identification."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        return session
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config with Gemini settings."""
        from collections import namedtuple
        
        GeminiConfig = namedtuple('GeminiConfig', ['api_key', 'model_name', 'base_url'])
        
        config = Mock(spec=Config)
        config.get_gemini_config.return_value = GeminiConfig(
            api_key=os.getenv('AUTOGT_GEMINI_API_KEY', 'test_mock_api_key'),
            model_name="gemini-2.5-flash",
            base_url="https://generativelanguage.googleapis.com"
        )
        return config

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample TARA analysis."""
        return TaraAnalysis(
            id=uuid4(),
            analysis_name="Test Manual Analysis",
            vehicle_model="Test Manual Model",
            analysis_phase=AnalysisPhase.DESIGN,
            completion_status=CompletionStatus.IN_PROGRESS,
            iso_section="ISO 21434:2021"
        )

    @pytest.fixture
    def sample_assets(self):
        """Create sample assets."""
        analysis_id = uuid4()
        return [
            Asset(
                id=uuid4(),
                name="ECU Gateway",
                asset_type=AssetType.HARDWARE,
                criticality_level=CriticalityLevel.HIGH,
                analysis_id=analysis_id,
                iso_section="ISO 21434:2021 Section 8",
                interfaces=["CAN", "Ethernet"],
                data_flows=["sensor_data", "control_commands"],
                security_properties={"description": "Gateway ECU"}
            ),
            Asset(
                id=uuid4(),
                name="Infotainment System",
                asset_type=AssetType.SOFTWARE,
                criticality_level=CriticalityLevel.MEDIUM,
                analysis_id=analysis_id,
                iso_section="ISO 21434:2021 Section 9",
                interfaces=["Bluetooth", "WiFi"],
                data_flows=["media_stream", "user_data"],
                security_properties={"description": "Infotainment software"}
            )
        ]
    
    @patch('autogt.cli.commands.threats.AutoGenTaraAgent')
    def test_sucessful_threat_identification(
        self, mock_agent_class, mock_session: Mock, mock_config: Mock, 
        sample_analysis: TaraAnalysis, sample_assets: list[Asset]
    ):
        """Test successful AI threat identification with multiple threats.
        
        This verifies:
        1. AI agent is initialized correctly
        2. Each asset is analyzed
        3. Threats are created and added to the session
        4. Correct count is returned
        """
        # Arrange: Setup mock AI agent response
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock AI response with threats
        mock_agent.identify_threats.return_value = {
            "threats": [
                {
                    "name": "Unauthorized CAN Bus Access",
                    "category": "Spoofing",
                    "severity": "High",
                    "description": "An attacker could gain unauthorized access to the CAN bus...",
                    "actor": "CRIMINAL",
                    "motivation": "Unauthorized vehicle control",
                    "attack_vectors": ["OBD-II port", "CAN bus injection"],
                    "prerequisites": ["Physical access", "CAN tools"]
                },
                {
                    "name": "Infotainment System Vulnerability",
                    "category": "Information Disclosure",
                    "severity": "Medium",
                    "description": "The infotainment system may leak sensitive user data...",
                    "actor": "SCRIPT_KIDDIE",
                    "motivation": "Data theft",
                    "attack_vectors": ["Bluetooth", "WiFi"],
                    "prerequisites": ["Network proximity"]
                }
            ]
        }

        # Act: Call the function
        result = _ai_threat_identification(
            mock_session, sample_analysis, sample_assets, mock_config
        )

        # Assert: Verify behavior
        assert result == 4 # 2 threats x 2 assets
        assert mock_session.add.call_count == 4  
        mock_agent_class.assert_called_once_with(mock_config.get_gemini_config())
        assert mock_agent.identify_threats.call_count == 2  # Once per asset

    @patch('autogt.cli.commands.threats.AutoGenTaraAgent')
    def test_no_threats_identified(
        self, mock_agent_class, mock_session, mock_config, 
        sample_analysis, sample_assets
    ):
        """Test when AI returns no threats.
        
        Verifies that function handles empty results gracefully.
        """
        # Arrange: AI returns no threats
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.identify_threats.return_value = {"threats": []}
        
        # Act
        result = _ai_threat_identification(
            mock_session, sample_analysis, sample_assets, mock_config
        )
        
        # Assert 
        assert result == 0
        mock_session.add.assert_not_called()

    @patch('autogt.cli.commands.threats.AutoGenTaraAgent')
    @patch('autogt.cli.commands.threats._rule_based_threat_identification')
    def test_fall_back_to_rule_based_on_exception(
        self, mock_rule_based, mock_agent_class, mock_session, 
        mock_config, sample_analysis, sample_assets
    ):
        """
        Test fallback mechanism when AI fails. 
        
        Critical test: Ensures system degrades gracefully when AI is unavailable.
        """

        # Arrange: AI agent raises exception
        mock_agent_class.side_effect = Exception("API quota exceeded")
        mock_rule_based.return_value = 5 # Mock rule-based to return 5 threats
        
        # Act
        result = _ai_threat_identification(
            mock_session, sample_analysis, sample_assets, mock_config
        )

        # Assert: Falls back to rule-based 
        assert result == 5
        mock_rule_based.assert_called_once_with(mock_session, sample_analysis, sample_assets)

    @patch('autogt.cli.commands.threats.AutoGenTaraAgent')
    def test_context_passed_correctly_to_ai(
        self, mock_agent_class, mock_session, mock_config, 
        sample_analysis, sample_assets
    ):
        """
        Test that correct context is passed to AI agent.
        
        Verifies all necessary assert information is included in the context.
        """

        # Arrange
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.identify_threats.return_value = {"threats": []}
        
        # Act
        _ai_threat_identification(
            mock_session, sample_analysis, sample_assets[:1], mock_config
        )
        
        # Assert: Check context structure
        call_args = mock_agent.identify_threats.call_args[0][0]
        
        assert call_args["analysis_name"] == "Test Manual Analysis"
        assert call_args["vehicle_model"] == "Test Manual Model"
    
    @patch('autogt.services.autogen_agent.AutoGenTaraAgent')
    def test_empty_assets_list(
        self, mock_agent_class, mock_session, mock_config, 
        sample_analysis
    ):
        """
        Test behavior with no assets to analyze.
        
        Should return 0 without attempting AI analysis.
        """

        # Arrange
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Act
        result = _ai_threat_identification(
            mock_session, sample_analysis, [], mock_config
        )
        
        # Assert 
        assert result == 0
        mock_agent.identify_threats.assert_not_called()