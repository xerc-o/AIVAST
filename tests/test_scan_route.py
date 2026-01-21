import pytest
import json
from unittest.mock import patch, mock_open
from app import create_app
from models import db, User # Import User model
from unittest.mock import MagicMock

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

            # Create a test user
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("password")
            db.session.add(test_user)
            db.session.commit()

            # Mock current_user for Flask-Login
            mock_user = MagicMock()
            mock_user.id = test_user.id
            mock_user.is_authenticated = True
            mock_user.is_active = True
            mock_user.is_anonymous = False
            mock_user.get_id.return_value = str(test_user.id)

            # Patch current_user during the test client's context
            with patch('flask_login.utils._get_user', return_value=mock_user):
                yield client
        # Teardown is handled by the with statements


def test_scan_endpoint_success(client):
    """
    Tests the /api/v1/scans endpoint for a successful asynchronous workflow.
    It mocks the entire `Plan -> Execute -> Analyze` pipeline.
    """
    # 1. Define mock data that our patched functions will return
    mock_plan = {
        "tool": "nmap",
        "command": ["nmap", "-F", "example.com"],
        "reason": "Mocked plan"
    }
    mock_stdout_content = "Nmap scan complete: Host is up."
    mock_stderr_content = ""
    
    mock_analysis_result = {
        "risk": "medium",
        "summary": "Mocked analysis found one open port.",
        "findings": [{"port": "80", "service": "http", "note": "Open port"}]
    }

    # Prepare mock for temporary files
    mock_stdout_file_path = '/tmp/test_stdout.log'
    mock_stderr_file_path = '/tmp/test_stderr.log'

    # 2. Use `patch` to intercept function calls and replace them with mocks
    with patch('routes.scan.plan_scan', return_value=mock_plan) as mock_plan_scan, \
         patch('routes.scan.run_command_async') as mock_run_command_async, \
         patch('routes.scan.analyze_output', return_value=mock_analysis_result) as mock_analyze, \
         patch('builtins.open', new_callable=mock_open) as mock_file_open, \
         patch('os.remove') as mock_os_remove, \
         patch('psutil.pid_exists', side_effect=[True, True, False]), \
         patch('psutil.Process') as mock_process, \
         patch('os.path.exists', return_value=True) as mock_path_exists: # Add this patch

        
        # Configure mock_run_command_async
        mock_run_command_async.return_value = {
            "ok": True,
            "pid": 12345,
            "stdout_path": mock_stdout_file_path,
            "stderr_path": mock_stderr_file_path,
            "tool": mock_plan["tool"],
        }

        # Configure mock_file_open to simulate reading from temp files
        mock_file_open.side_effect = [
            mock_open(read_data=mock_stdout_content).return_value, # For stdout
            mock_open(read_data=mock_stderr_content).return_value  # For stderr
        ]

        # Configure mock_process instance
        mock_proc_instance = mock_process.return_value
        mock_proc_instance.is_running.side_effect = [True, False] # Simulate running then stopped
        mock_proc_instance.status.return_value = 'running' # Not a zombie

        # 3. Make the request to the endpoint using the test client
        response = client.post('/api/v1/scans',
                               data=json.dumps({'target': 'example.com'}),
                               content_type='application/json')
        
        assert response.status_code == 202
        json_data = response.get_json()
        scan_id = json_data['scan_id']
        assert scan_id is not None

        # Verify plan_scan and run_command_async were called
        mock_plan_scan.assert_called_once_with('example.com', use_ai=True, tool=None, history='', deep_scan=False)
        mock_run_command_async.assert_called_once_with(mock_plan["command"])

        # 4. Poll the status endpoint until completed
        status_response = {}
        max_polls = 5
        for _ in range(max_polls):
            status_res = client.get(f'/api/v1/scans/{scan_id}/status')
            status_response = status_res.get_json()
            if status_response['status'] != 'running':
                break
            # In a real test, you might add a short sleep here
            # but for mocks, we control the side_effect sequence.

        assert status_response['status'] == 'completed'
        assert status_response['analysis'] == mock_analysis_result

        # Verify analyze_output was called
        mock_analyze.assert_called_once()
        
        # Verify temporary files were removed
        mock_os_remove.assert_any_call(mock_stdout_file_path)
        mock_os_remove.assert_any_call(mock_stderr_file_path)

        # Ensure process was queried
        mock_process.assert_called_with(12345)
        mock_proc_instance.is_running.assert_called()


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
         patch('routes.scan.run_command_async', return_value=mock_failed_execution) as mock_run_cmd, \
         patch('routes.scan.analyze_output') as mock_analyze: # We also mock analyze

        # 3. Make the request
        response = client.post('/api/v1/scans',
                               data=json.dumps({'target': 'example.com'}),
                               content_type='application/json')

        # 4. Assert the results
        assert response.status_code == 500  # The endpoint should return a server error
        json_data = response.get_json()

        # Verify the error message and details
        assert json_data['error'] == 'Failed to start scan: command failed'

        # Ensure the analysis function was NOT called because execution failed
        mock_analyze.assert_not_called()

def test_scan_endpoint_missing_target(client):
    """
    Tests that the /scan endpoint returns a 400 Bad Request if 'target' is missing.
    """
    # Make a request with no data
    response = client.post('/api/v1/scans',
                           data=json.dumps({}),
                           content_type='application/json')

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'missing target'