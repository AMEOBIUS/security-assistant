"""
ML Scoring Service for Security Findings.

Provides ML-based vulnerability scoring with EPSS integration.
Handles model loading, scoring, and fallback to rule-based scoring.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MLScoringService:
    """
    ML-based vulnerability scoring service.

    Features:
    - Model loading and management
    - EPSS integration for exploit probability
    - Automatic fallback to rule-based scoring
    - Batch scoring support

    Example:
        >>> service = MLScoringService(enable_ml=True)
        >>> score = service.score(finding)
        >>> print(f"Score: {score.ml_score}/100")
    """

    def __init__(
        self,
        enable_ml: bool = False,
        model_path: Optional[str] = None,
        enable_epss: bool = True,
    ):
        """
        Initialize ML scoring service.

        Args:
            enable_ml: Enable ML-based scoring
            model_path: Path to trained model file
            enable_epss: Enable EPSS integration
        """
        self.enable_ml = enable_ml
        self._ml_scorer = None
        self._epss_client = None

        if enable_ml:
            self._initialize_ml(model_path, enable_epss)

    def _initialize_ml(self, model_path: Optional[str], enable_epss: bool) -> None:
        """Initialize ML components."""
        try:
            from ..ml.epss import EPSSClient
            from ..ml.scoring import MLScorer

            if enable_epss:
                cache_path = Path.cwd() / ".cache" / "epss_scores.json"
                self._epss_client = EPSSClient(
                    cache_enabled=True, cache_file=cache_path
                )

            default_model = "security_assistant/ml/models/random_forest_v1.pkl"
            self._ml_scorer = MLScorer(
                model_path=model_path or default_model,
                epss_client=self._epss_client,
                enable_epss=enable_epss,
            )
            logger.info("ML scoring enabled")

        except Exception as e:
            logger.warning(
                f"Failed to initialize ML scoring: {e}. Falling back to rule-based."
            )
            self._ml_scorer = None
            self.enable_ml = False

    @property
    def is_available(self) -> bool:
        """Check if ML scoring is available."""
        return self._ml_scorer is not None

    @property
    def ml_scorer(self) -> Optional[Any]:
        """Get ML scorer instance (for backward compatibility)."""
        return self._ml_scorer

    @property
    def epss_client(self) -> Optional[Any]:
        """Get EPSS client instance."""
        return self._epss_client

    def score(self, finding: Any) -> Optional[Any]:
        """
        Score a finding using ML model.

        Args:
            finding: UnifiedFinding to score

        Returns:
            MLScore object or None if ML not available
        """
        if not self._ml_scorer:
            return None

        try:
            return self._ml_scorer.score(finding)
        except Exception as e:
            logger.warning(f"ML scoring failed for {finding.finding_id}: {e}")
            return None

    def score_batch(self, findings: list) -> list:
        """
        Score multiple findings in batch.

        Args:
            findings: List of UnifiedFinding objects

        Returns:
            List of MLScore objects
        """
        if not self._ml_scorer:
            return []

        try:
            return self._ml_scorer.score_batch(findings)
        except Exception as e:
            logger.warning(f"Batch ML scoring failed: {e}")
            return []

    def explain_score(self, ml_score: Any, top_n: int = 5) -> str:
        """
        Generate explanation for ML score.

        Args:
            ml_score: MLScore to explain
            top_n: Number of top features to include

        Returns:
            Human-readable explanation
        """
        if not self._ml_scorer:
            return "ML scoring not available"

        return self._ml_scorer.explain_score(ml_score, top_n)
