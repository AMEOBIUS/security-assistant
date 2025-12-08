"""
ML-Based Vulnerability Scoring Module

This module provides machine learning-based vulnerability prioritization
with EPSS integration, asset criticality, and threat intelligence context.

Features:
- Feature extraction from scan findings
- ML-based scoring (scikit-learn, XGBoost, LightGBM)
- EPSS integration (exploit probability)
- Model training and versioning
- FastAPI endpoints for scoring

Version: 1.0.0
"""

from .features import FeatureExtractor
from .scoring import MLScorer
from .epss import EPSSClient

__all__ = [
    "FeatureExtractor",
    "MLScorer",
    "EPSSClient",
]
