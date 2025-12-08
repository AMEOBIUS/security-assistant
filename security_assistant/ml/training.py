"""
ML Model Training Pipeline

Trains ML models for vulnerability scoring using historical scan data.

Version: 1.0.0
"""

import logging
import pickle
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from ..orchestrator import UnifiedFinding
from .features import FeatureExtractor, FeatureVector
from .epss import EPSSClient


logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training metrics for model evaluation."""
    mse: float  # Mean Squared Error
    mae: float  # Mean Absolute Error
    r2: float  # R² Score
    cv_scores: List[float]  # Cross-validation scores
    feature_importance: Dict[str, float]
    
    @property
    def rmse(self) -> float:
        """Root Mean Squared Error."""
        return np.sqrt(self.mse)


class ModelTrainer:
    """
    Train ML models for vulnerability scoring.
    
    Supports:
    - Baseline (Logistic Regression)
    - Random Forest
    - XGBoost (optional)
    - LightGBM (optional)
    """
    
    def __init__(
        self,
        epss_client: Optional[EPSSClient] = None,
        random_state: int = 42,
    ):
        """
        Initialize model trainer.
        
        Args:
            epss_client: EPSS client for feature extraction
            random_state: Random seed for reproducibility
        """
        self.epss_client = epss_client
        self.random_state = random_state
        self.feature_extractor = FeatureExtractor(epss_client=epss_client)
        
        logger.info(f"Initialized ModelTrainer (random_state={random_state})")
    
    def prepare_dataset(
        self,
        findings: List[UnifiedFinding],
        labels: List[float],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare dataset for training.
        
        Args:
            findings: List of UnifiedFinding objects
            labels: List of ground truth scores (0-100)
        
        Returns:
            Tuple of (X, y) where X is feature matrix, y is labels
        """
        if len(findings) != len(labels):
            raise ValueError(f"Findings ({len(findings)}) and labels ({len(labels)}) must have same length")
        
        # Extract features
        feature_vectors = self.feature_extractor.extract_batch(findings)
        
        # Build feature matrix
        X = np.array([fv.to_array() for fv in feature_vectors])
        y = np.array(labels)
        
        logger.info(f"Prepared dataset: X shape={X.shape}, y shape={y.shape}")
        
        return X, y
    
    def train_baseline(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> Tuple[Any, TrainingMetrics]:
        """
        Train baseline model (Logistic Regression for classification).
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
        
        Returns:
            Tuple of (model, metrics)
        """
        logger.info("Training baseline model (Logistic Regression)...")
        
        # Convert to classification (bins: 0-25, 25-50, 50-75, 75-100)
        y_train_class = np.digitize(y_train, bins=[25, 50, 75])
        y_test_class = np.digitize(y_test, bins=[25, 50, 75])
        
        model = LogisticRegression(
            random_state=self.random_state,
            max_iter=1000,
            multi_class='multinomial',
        )
        
        model.fit(X_train, y_train_class)
        
        # Predict and convert back to scores
        y_pred_class = model.predict(X_test)
        y_pred = self._class_to_score(y_pred_class)
        
        # Calculate metrics
        metrics = self._calculate_metrics(model, X_train, y_train_class, X_test, y_test, y_pred)
        
        logger.info(f"Baseline trained: RMSE={metrics.rmse:.2f}, R²={metrics.r2:.3f}")
        
        return model, metrics
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
    ) -> Tuple[Any, TrainingMetrics]:
        """
        Train Random Forest model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            n_estimators: Number of trees
            max_depth: Maximum tree depth
        
        Returns:
            Tuple of (model, metrics)
        """
        logger.info(f"Training Random Forest (n_estimators={n_estimators})...")
        
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=self.random_state,
            n_jobs=-1,
        )
        
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred = np.clip(y_pred, 0, 100)  # Clip to valid range
        
        # Calculate metrics
        metrics = self._calculate_metrics(model, X_train, y_train, X_test, y_test, y_pred)
        
        logger.info(f"Random Forest trained: RMSE={metrics.rmse:.2f}, R²={metrics.r2:.3f}")
        
        return model, metrics
    
    def _class_to_score(self, y_class: np.ndarray) -> np.ndarray:
        """Convert class labels to scores."""
        # Map classes to midpoint scores
        class_to_score = {0: 12.5, 1: 37.5, 2: 62.5, 3: 87.5}
        return np.array([class_to_score[c] for c in y_class])
    
    def _calculate_metrics(
        self,
        model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        y_pred: np.ndarray,
    ) -> TrainingMetrics:
        """Calculate training metrics."""
        # Regression metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation (on training set)
        try:
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=5, scoring='neg_mean_squared_error'
            )
            cv_scores = np.sqrt(-cv_scores)  # Convert to RMSE
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
            cv_scores = []
        
        # Feature importance
        feature_importance = self._get_feature_importance(model)
        
        return TrainingMetrics(
            mse=mse,
            mae=mae,
            r2=r2,
            cv_scores=cv_scores.tolist() if len(cv_scores) > 0 else [],
            feature_importance=feature_importance,
        )
    
    def _get_feature_importance(self, model: Any) -> Dict[str, float]:
        """Get feature importance from model."""
        feature_names = FeatureVector.feature_names()
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            return dict(zip(feature_names, importances))
        elif hasattr(model, 'coef_'):
            # For logistic regression, use mean absolute coefficient
            importances = np.abs(model.coef_).mean(axis=0)
            return dict(zip(feature_names, importances))
        else:
            return {}
    
    def save_model(
        self,
        model: Any,
        model_path: str,
        model_type: str,
        version: str,
        metrics: Optional[TrainingMetrics] = None,
    ) -> None:
        """
        Save trained model to file.
        
        Args:
            model: Trained model
            model_path: Path to save model
            model_type: Model type (e.g., "baseline", "random_forest")
            version: Model version
            metrics: Training metrics
        """
        model_data = {
            "model": model,
            "type": model_type,
            "version": version,
            "trained_at": datetime.now().isoformat(),
            "feature_names": FeatureVector.feature_names(),
        }
        
        if metrics:
            model_data["metrics"] = {
                "mse": metrics.mse,
                "mae": metrics.mae,
                "r2": metrics.r2,
                "rmse": metrics.rmse,
                "cv_scores": metrics.cv_scores,
            }
        
        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Saved model to {model_path}")
    
    def generate_synthetic_data(
        self,
        n_samples: int = 1000,
    ) -> Tuple[List[UnifiedFinding], List[float]]:
        """
        Generate synthetic training data.
        
        Args:
            n_samples: Number of samples to generate
        
        Returns:
            Tuple of (findings, labels)
        """
        from ..orchestrator import FindingSeverity, ScannerType
        
        findings = []
        labels = []
        
        severities = [
            FindingSeverity.CRITICAL,
            FindingSeverity.HIGH,
            FindingSeverity.MEDIUM,
            FindingSeverity.LOW,
            FindingSeverity.INFO,
        ]
        
        scanners = [ScannerType.BANDIT, ScannerType.SEMGREP, ScannerType.TRIVY]
        categories = ["security", "secret", "misconfig", "vulnerability"]
        file_types = [".py", ".js", ".java", ".go", "Dockerfile"]
        
        for i in range(n_samples):
            severity = severities[np.random.randint(0, len(severities))]
            scanner = scanners[np.random.randint(0, len(scanners))]
            category = categories[np.random.randint(0, len(categories))]
            file_type = file_types[np.random.randint(0, len(file_types))]
            
            finding = UnifiedFinding(
                finding_id=f"synthetic-{i}",
                scanner=scanner,
                severity=severity,
                category=category,
                file_path=f"src/file{i}{file_type}",
                line_start=i,
                line_end=i,
                title=f"Issue {i}",
                description=f"Description {i}",
                code_snippet=f"code {i}",
                cwe_ids=["CWE-89"] if np.random.random() > 0.5 else [],
                owasp_categories=["A03:2021"] if np.random.random() > 0.5 else [],
                references=[f"https://example.com/{i}"],
                fix_available=np.random.random() > 0.5,
                confidence=np.random.choice(["HIGH", "MEDIUM", "LOW"]),
            )
            
            # Generate label based on severity + randomness
            base_score = {
                FindingSeverity.CRITICAL: 90,
                FindingSeverity.HIGH: 70,
                FindingSeverity.MEDIUM: 50,
                FindingSeverity.LOW: 30,
                FindingSeverity.INFO: 10,
            }[severity]
            
            # Add noise
            label = base_score + np.random.normal(0, 10)
            label = np.clip(label, 0, 100)
            
            findings.append(finding)
            labels.append(label)
        
        logger.info(f"Generated {n_samples} synthetic samples")
        
        return findings, labels
