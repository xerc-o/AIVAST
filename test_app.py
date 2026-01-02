import pytest
import json
from unittest.mock import patch
from app import create_app
from models import db

@pytest.fixture
def client():
    """
    Pytest fixture to set up a Flask test client and an in-memory database.
    This runs before each test function that uses it.
    """
    # Pass test config directly to the app factory
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Use in-memory DB for tests
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing forms if any
    })

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create all tables for the in-memory database
        yield client
        # Teardown is handled by the with statements


def test_scan_endpoint_success(client):
    """
    Tests the /scan endpoint for a successful workflow.
    It mocks the entire `Plan -> Execute -> Analyze` pipeline to isolate the endpoint logic.
    """
    # 1. Define mock data that our patched functions will return
    mock_plan = {
        "tool": "nmap",
        "command": "nmap -F example.com",
        "reason": "Mocked plan"
    }
    mock_execution_result = {
        "ok": True,
        "tool": "nmap",
        "returncode": 0,
        "stdout": "Starting Nmap... Host is up... 80/tcp open http",
        "stderr": ""
    }
    mock_analysis_result = {
        "risk": "medium",
        "summary": "Mocked analysis found one open port.",
        "findings": [{"port": "80", "service": "http", "note": "Open port"}]
    }

    # 2. Use `patch` to intercept function calls and replace them with mocks
    with patch('routes.scan.plan_scan', return_value=mock_plan) as mock_plan_scan, \
         patch('routes.scan.run_command', return_value=mock_execution_result) as mock_run_cmd, \
         patch('routes.scan.analyze_output', return_value=mock_analysis_result) as mock_analyze:

        # 3. Make the request to the endpoint using the test client
        response = client.post('/scan',
                               data=json.dumps({'target': 'example.com'}),
                               content_type='application/json')

        # 4. Assert the results to verify the endpoint's behavior
        assert response.status_code == 200
        json_data = response.get_json()

        # Verify that our mocked functions were called correctly
        mock_plan_scan.assert_called_once_with('example.com', use_ai=False)
        mock_run_cmd.assert_called_once_with(mock_plan["command"])
        mock_analyze.assert_called_once_with(mock_plan["tool"], mock_execution_result)

        # Verify the content of the JSON response
        assert json_data['target'] == 'example.com'
        assert json_data['tool'] == 'nmap'
        assert json_data['analysis']['risk'] == 'medium'
        assert len(json_data['analysis']['findings']) == 1


def test_scan_endpoint_execution_failure(client):
    """
    Tests the /scan endpoint for a scenario where the command execution fails.
    """
    # 1. Define mock data
    mock_plan = {
        "tool": "nmap",
        "command": "nmap -F example.com",
        "reason": "Mocked plan"
    }
    # This time, the execution result indicates failure
    mock_failed_execution = {
        "ok": False,
        "error": "command failed",
        "returncode": 1,
        "stdout": "",
        "stderr": "Some nmap error"
    }

    # 2. Patch the dependencies
    with patch('routes.scan.plan_scan', return_value=mock_plan), \
         patch('routes.scan.run_command', return_value=mock_failed_execution) as mock_run_cmd, \
         patch('routes.scan.analyze_output') as mock_analyze: # We also mock analyze

        # 3. Make the request
        response = client.post('/scan',
                               data=json.dumps({'target': 'example.com'}),
                               content_type='application/json')

        # 4. Assert the results
        assert response.status_code == 500  # The endpoint should return a server error
        json_data = response.get_json()

        # Verify the error message and details
        assert json_data['error'] == 'execution failed'
        assert json_data['details']['error'] == 'command failed'

        # Ensure the analysis function was NOT called because execution failed
        mock_analyze.assert_not_called()

def test_scan_endpoint_missing_target(client):
    """
    Tests that the /scan endpoint returns a 400 Bad Request if 'target' is missing.
    """
    # Make a request with no data
    response = client.post('/scan',
                           data=json.dumps({}),
                           content_type='application/json')

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'missing target'