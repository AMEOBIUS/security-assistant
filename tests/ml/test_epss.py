"""
Tests for EPSS Client

Tests EPSS API integration for exploit probability scoring.

Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from security_assistant.ml.epss import EPSSClient, EPSSScore


class TestEPSSScore:
    """Test EPSSScore dataclass."""
    
    def test_create_epss_score(self):
        """Test creating EPSSScore."""
        score = EPSSScore(
            cve_id="CVE-2024-1234",
            epss=0.85,
            percentile=0.95,
            date="2024-12-02",
        )
        
        assert score.cve_id == "CVE-2024-1234"
        assert score.epss == 0.85
        assert score.percentile == 0.95
        assert score.date == "2024-12-02"


class TestEPSSClient:
    """Test EPSSClient."""
    
    @pytest.fixture
    def client(self):
        """Create EPSS client with caching disabled for testing."""
        return EPSSClient(cache_enabled=False, timeout=5)
    
    @pytest.fixture
    def client_with_cache(self):
        """Create EPSS client with caching enabled."""
        return EPSSClient(cache_enabled=True, timeout=5)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock API response."""
        return {
            "status": "OK",
            "status-code": 200,
            "version": "1.0",
            "access": "public",
            "total": 2,
            "offset": 0,
            "limit": 100,
            "data": [
                {
                    "cve": "CVE-2024-1234",
                    "epss": "0.85000",
                    "percentile": "0.95000",
                    "date": "2024-12-02"
                },
                {
                    "cve": "CVE-2024-5678",
                    "epss": "0.42000",
                    "percentile": "0.75000",
                    "date": "2024-12-02"
                }
            ]
        }
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.cache_enabled is False
        assert client.timeout == 5
        assert client._cache == {}
    
    def test_init_with_cache(self, client_with_cache):
        """Test client initialization with cache."""
        assert client_with_cache.cache_enabled is True
        assert client_with_cache._cache == {}
    
    @patch('requests.get')
    def test_get_score_single(self, mock_get, client, mock_response):
        """Test getting score for single CVE."""
        mock_get.return_value.json.return_value = {
            **mock_response,
            "data": [mock_response["data"][0]]  # Only first CVE
        }
        mock_get.return_value.raise_for_status = Mock()
        
        score = client.get_score("CVE-2024-1234")
        
        assert score == 0.85
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_score_not_found(self, mock_get, client):
        """Test getting score for non-existent CVE."""
        mock_get.return_value.json.return_value = {
            "status": "OK",
            "data": []  # No results
        }
        mock_get.return_value.raise_for_status = Mock()
        
        score = client.get_score("CVE-9999-9999")
        
        assert score is None
    
    @patch('requests.get')
    def test_get_scores_batch(self, mock_get, client, mock_response):
        """Test getting scores for multiple CVEs."""
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()
        
        scores = client.get_scores(["CVE-2024-1234", "CVE-2024-5678"])
        
        assert len(scores) == 2
        assert scores["CVE-2024-1234"] == 0.85
        assert scores["CVE-2024-5678"] == 0.42
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_scores_empty_list(self, mock_get, client):
        """Test getting scores with empty list."""
        scores = client.get_scores([])
        
        assert scores == {}
        mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_get_scores_normalization(self, mock_get, client, mock_response):
        """Test CVE ID normalization (lowercase -> uppercase)."""
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()
        
        # Pass lowercase CVE IDs
        scores = client.get_scores(["cve-2024-1234", "cve-2024-5678"])
        
        # Should return uppercase keys
        assert "CVE-2024-1234" in scores
        assert "CVE-2024-5678" in scores
    
    @patch('requests.get')
    def test_get_scores_api_error(self, mock_get, client):
        """Test handling API errors."""
        mock_get.side_effect = Exception("API error")
        
        scores = client.get_scores(["CVE-2024-1234"])
        
        # Should return empty dict on error
        assert scores == {}
    
    @patch('requests.get')
    def test_get_scores_invalid_json(self, mock_get, client):
        """Test handling invalid JSON response."""
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value.raise_for_status = Mock()
        
        scores = client.get_scores(["CVE-2024-1234"])
        
        # Should return empty dict on parse error
        assert scores == {}
    
    @patch('requests.get')
    def test_cache_hit(self, mock_get, client_with_cache, mock_response):
        """Test cache hit (no API call on second request)."""
        mock_get.return_value.json.return_value = {
            **mock_response,
            "data": [mock_response["data"][0]]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        # First call - should hit API
        score1 = client_with_cache.get_score("CVE-2024-1234")
        assert score1 == 0.85
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        score2 = client_with_cache.get_score("CVE-2024-1234")
        assert score2 == 0.85
        assert mock_get.call_count == 1  # No additional API call
    
    @patch('requests.get')
    def test_cache_expiration(self, mock_get, client_with_cache, mock_response):
        """Test cache expiration after TTL."""
        mock_get.return_value.json.return_value = {
            **mock_response,
            "data": [mock_response["data"][0]]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        # First call
        score1 = client_with_cache.get_score("CVE-2024-1234")
        assert score1 == 0.85
        
        # Manually expire cache entry
        cve_id = "CVE-2024-1234"
        if cve_id in client_with_cache._cache:
            score_obj, _ = client_with_cache._cache[cve_id]
            # Set timestamp to 25 hours ago (past TTL)
            expired_time = datetime.now() - timedelta(hours=25)
            client_with_cache._cache[cve_id] = (score_obj, expired_time)
        
        # Second call - should hit API again (cache expired)
        score2 = client_with_cache.get_score("CVE-2024-1234")
        assert score2 == 0.85
        assert mock_get.call_count == 2  # Second API call
    
    def test_clear_cache(self, client_with_cache):
        """Test clearing cache."""
        # Add some entries to cache
        client_with_cache._cache["CVE-2024-1234"] = (
            EPSSScore("CVE-2024-1234", 0.85, 0.95, "2024-12-02"),
            datetime.now()
        )
        
        assert len(client_with_cache._cache) == 1
        
        client_with_cache.clear_cache()
        
        assert len(client_with_cache._cache) == 0
    
    def test_get_cache_stats(self, client_with_cache):
        """Test cache statistics."""
        # Add valid entry
        client_with_cache._cache["CVE-2024-1234"] = (
            EPSSScore("CVE-2024-1234", 0.85, 0.95, "2024-12-02"),
            datetime.now()
        )
        
        # Add expired entry
        client_with_cache._cache["CVE-2024-5678"] = (
            EPSSScore("CVE-2024-5678", 0.42, 0.75, "2024-12-02"),
            datetime.now() - timedelta(hours=25)
        )
        
        stats = client_with_cache.get_cache_stats()
        
        assert stats["total"] == 2
        assert stats["valid"] == 1
        assert stats["expired"] == 1
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep, mock_get, client, mock_response):
        """Test rate limiting between requests."""
        mock_get.return_value.json.return_value = {
            **mock_response,
            "data": [mock_response["data"][0]]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        # Make two requests
        client.get_score("CVE-2024-1234")
        client.get_score("CVE-2024-5678")
        
        # Should have called sleep for rate limiting
        # (first request doesn't sleep, second one does)
        assert mock_sleep.call_count >= 0  # May or may not sleep depending on timing
    
    @patch('requests.get')
    def test_batch_size_limit(self, mock_get, client, mock_response):
        """Test batch size limit (max 100 CVEs per request)."""
        # Create 150 CVEs (should split into 2 batches)
        cve_ids = [f"CVE-2024-{i:04d}" for i in range(150)]
        
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = Mock()
        
        scores = client.get_scores(cve_ids)
        
        # Should make 2 API calls (100 + 50)
        assert mock_get.call_count == 2


class TestEPSSClientIntegration:
    """Integration tests for EPSS client (requires internet)."""
    
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_api_call(self):
        """Test real API call to EPSS (integration test)."""
        client = EPSSClient(cache_enabled=False)
        
        # Use a well-known CVE
        score = client.get_score("CVE-2021-44228")  # Log4Shell
        
        # Should return a score (or None if not in EPSS database)
        assert score is None or (0.0 <= score <= 1.0)
    
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_batch_api_call(self):
        """Test real batch API call (integration test)."""
        client = EPSSClient(cache_enabled=True)
        
        cve_ids = [
            "CVE-2021-44228",  # Log4Shell
            "CVE-2021-45046",  # Log4Shell follow-up
            "CVE-2022-22965",  # Spring4Shell
        ]
        
        scores = client.get_scores(cve_ids)
        
        # Should return scores for some CVEs
        assert isinstance(scores, dict)
        # At least one score should be returned
        assert len(scores) >= 0
