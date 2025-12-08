"""
ML-Based Vulnerability Scoring

Provides machine learning-based vulnerability prioritization using:
- Feature extraction from findings
- Trained ML models (scikit-learn, XGBoost, LightGBM)
- EPSS integration for exploit probability
- Confidence intervals and explainability

Version: 1.0.0
"""

import logging
import pickle
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import numpy as np

from ..orchestrator import UnifiedFinding
from .features import FeatureExtractor, FeatureVector
from .epss import EPSSClient


logger = logging.getLogger(__name__)


@dataclass
class MLScore:
    """
    ML-based vulnerability score.
    
    Contains:
    - ML score (0-100)
    - Confidence interval
    - Feature importance
    - EPSS contribution
    """
    finding_id: str
    ml_score: float  # 0-100
    confidence_lower: float  # Lower bound of 95% CI
    confidence_upper: float  # Upper bound of 95% CI
    epss_score: float  # EPSS contribution (0-1)
    feature_importance: Dict[str, float]  # Top features
    model_version: str  # Model version used
    
    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """Get confidence interval as tuple."""
        return (self.confidence_lower, self.confidence_upper)
    
    @property
    def top_features(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N features by importance."""
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return sorted_features[:n]


class MLScorer:
    """
    ML-based vulnerability scorer.
    
    Features:
    - Multiple model support (baseline, XGBoost, LightGBM)
    - EPSS integration
    - Feature importance for explainability
    - Confidence intervals
    - Model versioning
    
    Example:
        >>> scorer = MLScorer()
        >>> scorer.load_model("models/xgboost_v1.pkl")
        >>> score = scorer.score(finding)
        >>> print(f"ML Score: {score.ml_score:.1f}/100")
        >>> print(f"EPSS: {score.epss_score * 100:.1f}%")
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        epss_client: Optional[EPSSClient] = None,
        enable_epss: bool = True,
    ):
        """
        Initialize ML scorer.
        
        Args:
            model_path: Path to trained model file (.pkl)
            epss_client: EPSS client for exploit probability
            enable_epss: Enable EPSS integration (default: True)
        """
        self.model = None
        self.model_version = "unknown"
        self.model_type = "unknown"
        
        # Feature extractor
        self.epss_client = epss_client if enable_epss else None
        self.feature_extractor = FeatureExtractor(epss_client=self.epss_client)
        
        # Load model if provided
        if model_path:
            self.load_model(model_path)
        
        logger.info(f"Initialized MLScorer (EPSS={enable_epss})")
    
    def load_model(self, model_path: str) -> None:
        """
        Load trained model from file.
        
        Args:
            model_path: Path to model file (.pkl)
        
        Raises:
            FileNotFoundError: If model file not found
            ValueError: If model file is invalid
        """
        path = Path(model_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            with open(path, "rb") as f:
                model_data = pickle.load(f)
            
            # Extract model and metadata
            if isinstance(model_data, dict):
                self.model = model_data.get("model")
                self.model_version = model_data.get("version", "unknown")
                self.model_type = model_data.get("type", "unknown")
            else:
                # Legacy format (just the model)
                self.model = model_data
                self.model_version = "legacy"
                self.model_type = "unknown"
            
            logger.info(
                f"Loaded model: {self.model_type} v{self.model_version} "
                f"from {model_path}"
            )
        
        except Exception as e:
            raise ValueError(f"Failed to load model: {e}")
    
    def score(self, finding: UnifiedFinding) -> MLScore:
        """
        Score a single finding using ML model.
        
        Args:
            finding: UnifiedFinding to score
        
        Returns:
            MLScore with score and metadata
        
        Raises:
            ValueError: If model not loaded
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Extract features
        features = self.feature_extractor.extract(finding)
        
        # Get prediction
        X = features.to_array().reshape(1, -1)
        
        # Predict score (0-100)
        ml_score = float(self.model.predict(X)[0])
        
        # Get confidence interval (if model supports it)
        confidence_lower, confidence_upper = self._get_confidence_interval(X, ml_score)
        
        # Get feature importance
        feature_importance = self._get_feature_importance(features)
        
        return MLScore(
            finding_id=finding.finding_id,
            ml_score=ml_score,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            epss_score=features.epss_score,
            feature_importance=feature_importance,
            model_version=self.model_version,
        )
    
    def score_batch(self, findings: List[UnifiedFinding]) -> List[MLScore]:
        """
        Score multiple findings in batch.
        
        Args:
            findings: List of UnifiedFinding objects
        
        Returns:
            List of MLScore objects
        
        Example:
            >>> scores = scorer.score_batch(findings)
            >>> top_scores = sorted(scores, key=lambda s: s.ml_score, reverse=True)[:10]
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        if not findings:
            return []
        
        # Extract features for all findings
        feature_vectors = self.feature_extractor.extract_batch(findings)
        
        # Build feature matrix
        X = np.array([fv.to_array() for fv in feature_vectors])
        
        # Batch prediction
        ml_scores = self.model.predict(X)
        
        # Build MLScore objects
        results = []
        for i, finding in enumerate(findings):
            features = feature_vectors[i]
            ml_score = float(ml_scores[i])
            
            # Get confidence interval
            confidence_lower, confidence_upper = self._get_confidence_interval(
                X[i:i+1], ml_score
            )
            
            # Get feature importance
            feature_importance = self._get_feature_importance(features)
            
            results.append(MLScore(
                finding_id=finding.finding_id,
                ml_score=ml_score,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
                epss_score=features.epss_score,
                feature_importance=feature_importance,
                model_version=self.model_version,
            ))
        
        return results
    
    def _get_confidence_interval(
        self,
        X: np.ndarray,
        prediction: float,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Get confidence interval for prediction.
        
        For tree-based models (RandomForest, XGBoost), use prediction variance.
        For other models, use fixed interval based on model type.
        
        Args:
            X: Feature vector
            prediction: Model prediction
            confidence: Confidence level (default: 0.95)
        
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Check if model supports prediction intervals
        if hasattr(self.model, "estimators_"):
            # RandomForest: use prediction variance across trees
            try:
                predictions = np.array([
                    tree.predict(X)[0]
                    for tree in self.model.estimators_
                ])
                std = np.std(predictions)
                margin = 1.96 * std  # 95% CI
                
                lower = max(0.0, prediction - margin)
                upper = min(100.0, prediction + margin)
                
                return (lower, upper)
            except Exception as e:
                logger.debug(f"Failed to compute CI from trees: {e}")
        
        # Fallback: use fixed margin based on model type
        # Conservative estimate: ±10 points
        margin = 10.0
        lower = max(0.0, prediction - margin)
        upper = min(100.0, prediction + margin)
        
        return (lower, upper)
    
    def _get_feature_importance(self, features: FeatureVector) -> Dict[str, float]:
        """
        Get feature importance for a prediction.
        
        For tree-based models, use model's feature_importances_.
        For other models, use feature values as proxy.
        
        Args:
            features: FeatureVector
        
        Returns:
            Dictionary mapping feature name to importance
        """
        feature_names = FeatureVector.feature_names()
        feature_values = features.to_array()
        
        # Check if model has feature_importances_
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            
            # Multiply by feature values for instance-specific importance
            instance_importance = importances * np.abs(feature_values)
            
            # Normalize to sum to 1.0
            total = np.sum(instance_importance)
            if total > 0:
                instance_importance = instance_importance / total
            
            return dict(zip(feature_names, instance_importance))
        
        # Fallback: use normalized feature values
        total = np.sum(np.abs(feature_values))
        if total > 0:
            normalized = np.abs(feature_values) / total
        else:
            normalized = np.zeros_like(feature_values)
        
        return dict(zip(feature_names, normalized))
    
    def explain_score(self, ml_score: MLScore, top_n: int = 5) -> str:
        """
        Generate human-readable explanation of ML score.
        
        Args:
            ml_score: MLScore to explain
            top_n: Number of top features to include
        
        Returns:
            Explanation string
        
        Example:
            >>> score = scorer.score(finding)
            >>> explanation = scorer.explain_score(score)
            >>> print(explanation)
        """
        lines = [
            f"ML Score: {ml_score.ml_score:.1f}/100",
            f"Confidence Interval: [{ml_score.confidence_lower:.1f}, {ml_score.confidence_upper:.1f}]",
            f"EPSS Score: {ml_score.epss_score * 100:.1f}% (exploit probability)",
            f"Model: {self.model_type} v{ml_score.model_version}",
            "",
            f"Top {top_n} Contributing Factors:",
        ]
        
        # Get top features
        top_features = sorted(
            ml_score.feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:top_n]
        
        for i, (feature, importance) in enumerate(top_features, 1):
            # Format feature name (remove underscores, capitalize)
            feature_display = feature.replace("_", " ").title()
            lines.append(f"  {i}. {feature_display}: {importance * 100:.1f}%")
        
        return "\n".join(lines)
    
    def compare_with_baseline(
        self,
        finding: UnifiedFinding,
        baseline_score: float
    ) -> Dict[str, Any]:
        """
        Compare ML score with baseline (e.g., CVSS or rule-based).
        
        Args:
            finding: UnifiedFinding to score
            baseline_score: Baseline score (0-100)
        
        Returns:
            Comparison dictionary with metrics
        
        Example:
            >>> ml_score = scorer.score(finding)
            >>> comparison = scorer.compare_with_baseline(
            ...     finding,
            ...     baseline_score=finding.priority_score
            ... )
            >>> print(f"Improvement: {comparison['improvement']:.1f}%")
        """
        ml_score = self.score(finding)
        
        difference = ml_score.ml_score - baseline_score
        improvement = (difference / baseline_score * 100) if baseline_score > 0 else 0.0
        
        return {
            "ml_score": ml_score.ml_score,
            "baseline_score": baseline_score,
            "difference": difference,
            "improvement_percent": improvement,
            "epss_score": ml_score.epss_score,
            "confidence_interval": ml_score.confidence_interval,
            "recommendation": self._get_recommendation(ml_score, baseline_score),
        }
    
    def _get_recommendation(self, ml_score: MLScore, baseline_score: float) -> str:
        """
        Get recommendation based on ML vs baseline comparison.
        
        Args:
            ml_score: MLScore
            baseline_score: Baseline score
        
        Returns:
            Recommendation string
        """
        difference = ml_score.ml_score - baseline_score
        
        if difference > 20:
            return "ML score significantly higher - prioritize this finding"
        elif difference > 10:
            return "ML score moderately higher - consider prioritizing"
        elif difference < -20:
            return "ML score significantly lower - may be false positive"
        elif difference < -10:
            return "ML score moderately lower - review carefully"
        else:
            return "ML and baseline scores agree - confidence high"
