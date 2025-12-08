"""
Tests for KEV Client

Tests CISA KEV catalog integration for actively exploited vulnerabilities.

Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from security_assistant.enrichment.kev import KEVClient, KEVEntry


class TestKEVEntry:
    """Test KEVEntry dataclass."""
    
    def test_create_kev_entry(self):
        """Test creating KEVEntry."""
        entry = KEVEntry(
            cve_id="CVE-2021-44228",
            vendor_project="Apache",
            product="Log4j",
            vulnerability_name="Log4Shell",
            date_added="2021-12-10",
            short_description="Apache Log4j2 JNDI features do not protect against attacker controlled LDAP",
            required_action="Apply updates per vendor instructions",
            due_date="2021-12-24",
            known_ransomware_campaign_use=True,
            notes="",
        )
        
        assert entry.cve_id == "CVE-2021-44228"
        assert entry.vendor_project == "Apache"
        assert entry.product == "Log4j"
        assert entry.vulnerability_name == "Log4Shell"
        assert entry.known_ransomware_campaign_use is True


class TestKEVClient:
    """Test KEVClient."""
    
    @pytest.fixture
    def client(self):
        """Create KEV client with caching disabled for testing."""
        return KEVClient(cache_enabled=False, offline_fallback=False)
    
    @pytest.fixture
    def client_with_cache(self):
        """Create KEV client with caching enabled."""
        return KEVClient(cache_enabled=True, offline_fallback=True)
    
    @pytest.fixture
    def mock_catalog(self):
        """Create mock KEV catalog response."""
        return {
            "title": "CISA Catalog of Known Exploited Vulnerabilities",
            "catalogVersion": "2024.12.06",
            "dateReleased": "2024-12-06",
            "count": 2,
            "vulnerabilities": [
                {
                    "cveID": "CVE-2021-44228",
                    "vendorProject": "Apache",
                    "product": "Log4j",
                    "vulnerabilityName": "Log4Shell",
                    "dateAdded": "2021-12-10",
                    "shortDescription": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP",
                    "requiredAction": "Apply updates per vendor instructions",
                    "dueDate": "2021-12-24",
                    "knownRansomwareCampaignUse": "Known",
                    "notes": ""
                },
                {
                    "cveID": "CVE-2022-22965",
                    "vendorProject": "VMware",
                    "product": "Spring Framework",
                    "vulnerabilityName": "Spring4Shell",
                    "dateAdded": "2022-04-01",
                    "shortDescription": "Spring Framework RCE via Data Binding on JDK 9+",
                    "requiredAction": "Apply updates per vendor instructions",
                    "dueDate": "2022-04-21",
                    "knownRansomwareCampaignUse": "Unknown",
                    "notes": ""
                }
            ]
        }
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.cache_enabled is False
        assert client.offline_fallback is False
        assert client._cache == {}
        assert client._cache_timestamp is None
    
    def test_init_with_cache(self, client_with_cache):
        """Test client initialization with cache."""
        assert client_with_cache.cache_enabled is True
        assert client_with_cache.offline_fallback is True
    
    @patch('requests.get')
    def test_is_exploited_true(self, mock_get, client, mock_catalog):
        """Test checking if CVE is exploited (true case)."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        is_exploited = client.is_exploited("CVE-2021-44228")
        
        assert is_exploited is True
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_is_exploited_false(self, mock_get, client, mock_catalog):
        """Test checking if CVE is exploited (false case)."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        is_exploited = client.is_exploited("CVE-9999-9999")
        
        assert is_exploited is False
    
    @patch('requests.get')
    def test_is_exploited_normalization(self, mock_get, client, mock_catalog):
        """Test CVE ID normalization (lowercase -> uppercase)."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        # Pass lowercase CVE ID
        is_exploited = client.is_exploited("cve-2021-44228")
        
        assert is_exploited is True
    
    @patch('requests.get')
    def test_get_entry(self, mock_get, client, mock_catalog):
        """Test getting KEV entry."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        entry = client.get_entry("CVE-2021-44228")
        
        assert entry is not None
        assert entry.cve_id == "CVE-2021-44228"
        assert entry.vendor_project == "Apache"
        assert entry.product == "Log4j"
        assert entry.vulnerability_name == "Log4Shell"
        assert entry.known_ransomware_campaign_use is True
    
    @patch('requests.get')
    def test_get_entry_not_found(self, mock_get, client, mock_catalog):
        """Test getting entry for non-exploited CVE."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        entry = client.get_entry("CVE-9999-9999")
        
        assert entry is None
    
    @patch('requests.get')
    def test_get_entries_batch(self, mock_get, client, mock_catalog):
        """Test getting entries for multiple CVEs."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        entries = client.get_entries([
            "CVE-2021-44228",
            "CVE-2022-22965",
            "CVE-9999-9999"  # Not exploited
        ])
        
        assert len(entries) == 2
        assert "CVE-2021-44228" in entries
        assert "CVE-2022-22965" in entries
        assert "CVE-9999-9999" not in entries
    
    @patch('requests.get')
    def test_get_all_exploited_cves(self, mock_get, client, mock_catalog):
        """Test getting all exploited CVE IDs."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        exploited = client.get_all_exploited_cves()
        
        assert len(exploited) == 2
        assert "CVE-2021-44228" in exploited
        assert "CVE-2022-22965" in exploited
    
    @patch('requests.get')
    def test_get_catalog_metadata(self, mock_get, client, mock_catalog):
        """Test getting catalog metadata."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        metadata = client.get_catalog_metadata()
        
        assert metadata["version"] == "2024.12.06"
        assert metadata["date"] == "2024-12-06"
        assert metadata["count"] == 2
        assert metadata["cache_age_hours"] is not None
    
    @patch('requests.get')
    def test_cache_hit(self, mock_get, client_with_cache, mock_catalog):
        """Test cache hit (no API call on second request)."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        # First call - should hit API
        is_exploited1 = client_with_cache.is_exploited("CVE-2021-44228")
        assert is_exploited1 is True
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        is_exploited2 = client_with_cache.is_exploited("CVE-2021-44228")
        assert is_exploited2 is True
        assert mock_get.call_count == 1  # No additional API call
    
    @patch('requests.get')
    def test_cache_expiration(self, mock_get, client_with_cache, mock_catalog):
        """Test cache expiration after TTL."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        # First call
        is_exploited1 = client_with_cache.is_exploited("CVE-2021-44228")
        assert is_exploited1 is True
        
        # Manually expire cache
        client_with_cache._cache_timestamp = datetime.now() - timedelta(hours=25)
        
        # Second call - should hit API again (cache expired)
        is_exploited2 = client_with_cache.is_exploited("CVE-2021-44228")
        assert is_exploited2 is True
        assert mock_get.call_count == 2  # Second API call
    
    @patch('requests.get')
    def test_refresh_catalog(self, mock_get, client, mock_catalog):
        """Test forcing catalog refresh."""
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        
        success = client.refresh_catalog()
        
        assert success is True
        assert mock_get.call_count == 1
    
    @patch('requests.get')
    def test_api_error_no_fallback(self, mock_get, client):
        """Test handling API errors without fallback."""
        mock_get.side_effect = Exception("API error")
        
        # Should not raise, but log error
        is_exploited = client.is_exploited("CVE-2021-44228")
        
        # Should return False (no cache, no fallback)
        assert is_exploited is False
    
    @patch('requests.get')
    def test_api_error_with_fallback(self, mock_get, client_with_cache, mock_catalog):
        """Test handling API errors with offline fallback."""
        # First call - populate cache
        mock_get.return_value.json.return_value = mock_catalog
        mock_get.return_value.raise_for_status = Mock()
        client_with_cache.is_exploited("CVE-2021-44228")
        
        # Expire cache
        client_with_cache._cache_timestamp = datetime.now() - timedelta(hours=25)
        
        # Second call - API fails, should use stale cache
        mock_get.side_effect = Exception("API error")
        is_exploited = client_with_cache.is_exploited("CVE-2021-44228")
        
        # Should still return True (using stale cache)
        assert is_exploited is True
    
    @patch('requests.get')
    def test_invalid_json(self, mock_get, client):
        """Test handling invalid JSON response."""
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value.raise_for_status = Mock()
        
        success = client.refresh_catalog()
        
        assert success is False
    
    def test_clear_cache(self, client_with_cache):
        """Test clearing cache."""
        # Add some entries to cache
        client_with_cache._cache["CVE-2021-44228"] = KEVEntry(
            cve_id="CVE-2021-44228",
            vendor_project="Apache",
            product="Log4j",
            vulnerability_name="Log4Shell",
            date_added="2021-12-10",
            short_description="Test",
            required_action="Test",
            due_date="2021-12-24",
            known_ransomware_campaign_use=True,
            notes="",
        )
        client_with_cache._cache_timestamp = datetime.now()
        client_with_cache._catalog_version = "2024.12.06"
        
        assert len(client_with_cache._cache) == 1
        
        client_with_cache.clear_cache()
        
        assert len(client_with_cache._cache) == 0
        assert client_with_cache._cache_timestamp is None
        assert client_with_cache._catalog_version is None


class TestKEVClientIntegration:
    """Integration tests for KEV client (requires internet)."""
    
    @pytest.mark.integration
    def test_real_api_call(self):
        """Test real API call to CISA KEV (integration test)."""
        client = KEVClient(cache_enabled=False)
        
        # Log4Shell should be in KEV catalog
        is_exploited = client.is_exploited("CVE-2021-44228")
        
        assert is_exploited is True
    
    @pytest.mark.integration
    def test_real_catalog_metadata(self):
        """Test real catalog metadata (integration test)."""
        client = KEVClient(cache_enabled=True)
        
        metadata = client.get_catalog_metadata()
        
        assert metadata["version"] is not None
        assert metadata["date"] is not None
        assert metadata["count"] > 0
    
    @pytest.mark.integration
    def test_real_get_entry(self):
        """Test real KEV entry retrieval (integration test)."""
        client = KEVClient(cache_enabled=True)
        
        entry = client.get_entry("CVE-2021-44228")
        
        assert entry is not None
        assert entry.cve_id == "CVE-2021-44228"
        assert "Log4j" in entry.product or "log4j" in entry.product.lower()
