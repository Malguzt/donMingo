import pytest
from unittest.mock import Mock, patch
from main import main


class TestMain:
    @patch('main.LocalGuanacosRepository')
    @patch('main.GuanacosSpits')
    def test_should_initialize_repository_and_use_case(self, mock_guanacos_spits_class, mock_repository_class):
        # Setup mocks
        mock_repository = Mock()
        mock_repository_class.return_value = mock_repository

        mock_guanacos_spits = Mock()
        mock_guanacos_spits_class.return_value = mock_guanacos_spits

        # Call main
        main()

        # Verify repository was created
        mock_repository_class.assert_called_once()

        # Verify GuanacosSpits was created with correct parameters
        mock_guanacos_spits_class.assert_called_once_with(mock_repository, sleep_time=10)

        # Verify run was called
        mock_guanacos_spits.run.assert_called_once()

    @patch('main.LocalGuanacosRepository')
    @patch('main.GuanacosSpits')
    def test_should_handle_exceptions_in_run(self, mock_guanacos_spits_class, mock_repository_class):
        # Setup mocks
        mock_repository = Mock()
        mock_repository_class.return_value = mock_repository

        mock_guanacos_spits = Mock()
        mock_guanacos_spits.run.side_effect = Exception("Test error")
        mock_guanacos_spits_class.return_value = mock_guanacos_spits

        # Should propagate exception
        with pytest.raises(Exception, match="Test error"):
            main()
