"""
Tests for Vulnerability Enricher

Tests EPSS + KEV integration for smart prioritization.

Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, MagicMock

from security_assistant.enrichment.enricher import VulnerabilityEnricher, EnrichedVulnerability
from security_assistant.enrichment.kev import KEVEntry
from security_assistant.ml.epss import EPSSClient
from security_assistant.enrichment.kev import KEVClient


class TestEnrichedVulnerability:
    """Test EnrichedVulnerability dataclass."""
    
    def test_create_enriched_vulnerability(self):
        """Test creating EnrichedVulnerability."""
        enriched = EnrichedVulnerability(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            epss_percentile=0.99,
            is_exploited=True,
            kev_entry=None,
            priority="CRITICAL",
            priority_reason="Actively exploited",
        )
        
        assert enriched.cve_id == "CVE-2021-44228"
        assert enriched.epss_score == 0.95
        assert enriched.is_exploited is True
        assert enriched.priority == "CRITICAL"


class TestVulnerabilityEnricher:
    """Test VulnerabilityEnricher."""
    
    @pytest.fixture
    def mock_epss_client(self):
        """Create mock EPSS client."""
        client = MagicMock(spec=EPSSClient)
        return client
    
    @pytest.fixture
    def mock_kev_client(self):
        """Create mock KEV client."""
        client = MagicMock(spec=KEVClient)
        return client
    
    @pytest.fixture
    def enricher(self, mock_epss_client, mock_kev_client):
        """Create enricher with mocked clients."""
        return VulnerabilityEnricher(
            epss_client=mock_epss_client,
            kev_client=mock_kev_client,
        )
    
    def test_init(self, enricher, mock_epss_client, mock_kev_client):
        """Test enricher initialization."""
        assert enricher.epss_client == mock_epss_client
        assert enricher.kev_client == mock_kev_client
    
    def test_init_default_clients(self):
        """Test enricher initialization with default clients."""
        enricher = VulnerabilityEnricher()
        
        assert enricher.epss_client is not None
        assert enricher.kev_client is not None
    
    def test_enrich_kev_critical(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE that is in KEV (CRITICAL)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = 0.85
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = True
        mock_kev_client.get_entry.return_value = KEVEntry(
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
        
        enriched = enricher.enrich("CVE-2021-44228")
        
        assert enriched.cve_id == "CVE-2021-44228"
        assert enriched.epss_score == 0.85
        assert enriched.is_exploited is True
        assert enriched.kev_entry is not None
        assert enriched.priority == "CRITICAL"
        assert "actively exploited" in enriched.priority_reason.lower()
        assert "ransomware" in enriched.priority_reason.lower()
    
    def test_enrich_epss_critical(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE with EPSS ≥ 70% (CRITICAL)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = 0.85
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = False
        mock_kev_client.get_entry.return_value = None
        
        enriched = enricher.enrich("CVE-2024-1234")
        
        assert enriched.priority == "CRITICAL"
        assert "85.0%" in enriched.priority_reason
    
    def test_enrich_epss_high(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE with EPSS 30-70% (HIGH)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = 0.50
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = False
        
        enriched = enricher.enrich("CVE-2024-1234")
        
        assert enriched.priority == "HIGH"
        assert "50.0%" in enriched.priority_reason
    
    def test_enrich_epss_medium(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE with EPSS 10-30% (MEDIUM)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = 0.20
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = False
        
        enriched = enricher.enrich("CVE-2024-1234")
        
        assert enriched.priority == "MEDIUM"
        assert "20.0%" in enriched.priority_reason
    
    def test_enrich_epss_low(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE with EPSS < 10% (LOW)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = 0.05
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = False
        
        enriched = enricher.enrich("CVE-2024-1234")
        
        assert enriched.priority == "LOW"
        assert "5.0%" in enriched.priority_reason
    
    def test_enrich_no_epss_data(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching CVE with no EPSS data (INFO)."""
        # Mock EPSS
        mock_epss_client.get_score.return_value = None
        
        # Mock KEV
        mock_kev_client.is_exploited.return_value = False
        
        enriched = enricher.enrich("CVE-2024-1234")
        
        assert enriched.priority == "INFO"
        assert "no epss data" in enriched.priority_reason.lower()
    
    def test_enrich_batch(self, enricher, mock_epss_client, mock_kev_client):
        """Test enriching multiple CVEs in batch."""
        # Mock EPSS
        mock_epss_client.get_scores.return_value = {
            "CVE-2021-44228": 0.95,
            "CVE-2024-1234": 0.50,
            "CVE-2024-5678": 0.05,
        }
        
        # Mock KEV
        mock_kev_client.get_entries.return_value = {
            "CVE-2021-44228": KEVEntry(
                cve_id="CVE-2021-44228",
                vendor_project="Apache",
                product="Log4j",
                vulnerability_name="Log4Shell",
                date_added="2021-12-10",
                short_description="Test",
                required_action="Test",
                due_date="2021-12-24",
                known_ransomware_campaign_use=False,
                notes="",
            )
        }
        
        enriched = enricher.enrich_batch([
            "CVE-2021-44228",
            "CVE-2024-1234",
            "CVE-2024-5678",
        ])
        
        assert len(enriched) == 3
        
        # CVE-2021-44228: KEV → CRITICAL
        assert enriched["CVE-2021-44228"].priority == "CRITICAL"
        assert enriched["CVE-2021-44228"].is_exploited is True
        
        # CVE-2024-1234: EPSS 50% → HIGH
        assert enriched["CVE-2024-1234"].priority == "HIGH"
        assert enriched["CVE-2024-1234"].is_exploited is False
        
        # CVE-2024-5678: EPSS 5% → LOW
        assert enriched["CVE-2024-5678"].priority == "LOW"
    
    def test_enrich_batch_empty(self, enricher):
        """Test enriching empty list."""
        enriched = enricher.enrich_batch([])
        
        assert enriched == {}
    
    def test_enrich_batch_normalization(self, enricher, mock_epss_client, mock_kev_client):
        """Test CVE ID normalization in batch."""
        # Mock EPSS
        mock_epss_client.get_scores.return_value = {
            "CVE-2024-1234": 0.50,
        }
        
        # Mock KEV
        mock_kev_client.get_entries.return_value = {}
        
        # Pass lowercase CVE ID
        enriched = enricher.enrich_batch(["cve-2024-1234"])
        
        # Should return uppercase key
        assert "CVE-2024-1234" in enriched
    
    def test_get_critical_cves(self, enricher, mock_epss_client, mock_kev_client):
        """Test getting CRITICAL CVEs from list."""
        # Mock EPSS
        mock_epss_client.get_scores.return_value = {
            "CVE-2021-44228": 0.95,  # CRITICAL (KEV)
            "CVE-2024-1234": 0.85,   # CRITICAL (EPSS)
            "CVE-2024-5678": 0.50,   # HIGH
            "CVE-2024-9999": 0.05,   # LOW
        }
        
        # Mock KEV
        mock_kev_client.get_entries.return_value = {
            "CVE-2021-44228": KEVEntry(
                cve_id="CVE-2021-44228",
                vendor_project="Apache",
                product="Log4j",
                vulnerability_name="Log4Shell",
                date_added="2021-12-10",
                short_description="Test",
                required_action="Test",
                due_date="2021-12-24",
                known_ransomware_campaign_use=False,
                notes="",
            )
        }
        
        critical = enricher.get_critical_cves([
            "CVE-2021-44228",
            "CVE-2024-1234",
            "CVE-2024-5678",
            "CVE-2024-9999",
        ])
        
        assert len(critical) == 2
        assert "CVE-2021-44228" in critical
        assert "CVE-2024-1234" in critical
    
    def test_get_exploited_cves(self, enricher, mock_epss_client, mock_kev_client):
        """Test getting exploited CVEs from list."""
        # Mock EPSS
        mock_epss_client.get_scores.return_value = {
            "CVE-2021-44228": 0.95,
            "CVE-2024-1234": 0.50,
        }
        
        # Mock KEV
        mock_kev_client.get_entries.return_value = {
            "CVE-2021-44228": KEVEntry(
                cve_id="CVE-2021-44228",
                vendor_project="Apache",
                product="Log4j",
                vulnerability_name="Log4Shell",
                date_added="2021-12-10",
                short_description="Test",
                required_action="Test",
                due_date="2021-12-24",
                known_ransomware_campaign_use=False,
                notes="",
            )
        }
        
        exploited = enricher.get_exploited_cves([
            "CVE-2021-44228",
            "CVE-2024-1234",
        ])
        
        assert len(exploited) == 1
        assert "CVE-2021-44228" in exploited


class TestVulnerabilityEnricherIntegration:
    """Integration tests for enricher (requires internet)."""
    
    @pytest.mark.integration
    def test_real_enrich_log4shell(self):
        """Test real enrichment of Log4Shell (integration test)."""
        enricher = VulnerabilityEnricher()
        
        enriched = enricher.enrich("CVE-2021-44228")
        
        # Log4Shell should be CRITICAL (KEV)
        assert enriched.priority == "CRITICAL"
        assert enriched.is_exploited is True
        assert enriched.epss_score is not None
    
    @pytest.mark.integration
    def test_real_enrich_batch(self):
        """Test real batch enrichment (integration test)."""
        enricher = VulnerabilityEnricher()
        
        enriched = enricher.enrich_batch([
            "CVE-2021-44228",  # Log4Shell (KEV)
            "CVE-2022-22965",  # Spring4Shell (KEV)
        ])
        
        assert len(enriched) == 2
        
        # Both should be CRITICAL (KEV)
        for cve_id, data in enriched.items():
            assert data.priority == "CRITICAL"
            assert data.is_exploited is True
