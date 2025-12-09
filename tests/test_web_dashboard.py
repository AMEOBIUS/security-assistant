import json
from unittest.mock import mock_open, patch

from fastapi.testclient import TestClient

from web_dashboard.backend.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Security Assistant Dashboard API"}

def test_list_scans_empty():
    with patch("pathlib.Path.exists", return_value=False):
        response = client.get("/api/v1/scans")
        assert response.status_code == 200
        assert response.json() == []

def test_list_scans_with_data():
    mock_data = {
        "metadata": {"generated_at": "2025-01-01", "target": "src/"},
        "summary": {"total_findings": 5}
    }
    # We mock Path.exists to return True for RESULTS_DIR and scan_file
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        
        response = client.get("/api/v1/scans")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["target"] == "src/"
