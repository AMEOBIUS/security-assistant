"""
Tests for ML Training Pipeline

Version: 1.0.0
"""

import tempfile
from pathlib import Path

import pytest

from security_assistant.ml.training import ModelTrainer, TrainingMetrics
from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding


class TestModelTrainer:
    """Test ModelTrainer."""
    
    @pytest.fixture
    def trainer(self):
        """Create model trainer."""
        return ModelTrainer(epss_client=None, random_state=42)
    
    @pytest.fixture
    def synthetic_data(self, trainer):
        """Generate synthetic training data."""
        return trainer.generate_synthetic_data(n_samples=100)
    
    def test_init(self, trainer):
        """Test trainer initialization."""
        assert trainer.random_state == 42
        assert trainer.feature_extractor is not None
    
    def test_generate_synthetic_data(self, trainer):
        """Test synthetic data generation."""
        findings, labels = trainer.generate_synthetic_data(n_samples=50)
        
        assert len(findings) == 50
        assert len(labels) == 50
        assert all(isinstance(f, UnifiedFinding) for f in findings)
        assert all(0 <= label <= 100 for label in labels)
    
    def test_prepare_dataset(self, trainer, synthetic_data):
        """Test dataset preparation."""
        findings, labels = synthetic_data
        
        X, y = trainer.prepare_dataset(findings, labels)
        
        assert X.shape[0] == 100  # n_samples
        assert X.shape[1] == 20  # n_features
        assert y.shape[0] == 100
    
    def test_prepare_dataset_mismatch(self, trainer):
        """Test dataset preparation with mismatched lengths."""
        findings = [
            UnifiedFinding(
                finding_id="test-1",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Test",
                description="Test",
                code_snippet="test",
            )
        ]
        labels = [50.0, 60.0]  # Mismatch
        
        with pytest.raises(ValueError, match="must have same length"):
            trainer.prepare_dataset(findings, labels)
    
    def test_train_baseline(self, trainer, synthetic_data):
        """Test baseline model training."""
        findings, labels = synthetic_data
        X, y = trainer.prepare_dataset(findings, labels)
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        model, metrics = trainer.train_baseline(X_train, y_train, X_test, y_test)
        
        assert model is not None
        assert isinstance(metrics, TrainingMetrics)
        assert metrics.mse >= 0
        assert metrics.mae >= 0
        assert -1 <= metrics.r2 <= 1
    
    def test_train_random_forest(self, trainer, synthetic_data):
        """Test Random Forest training."""
        findings, labels = synthetic_data
        X, y = trainer.prepare_dataset(findings, labels)
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        model, metrics = trainer.train_random_forest(
            X_train, y_train, X_test, y_test,
            n_estimators=10,  # Small for speed
        )
        
        assert model is not None
        assert isinstance(metrics, TrainingMetrics)
        assert metrics.mse >= 0
        assert metrics.mae >= 0
        assert -1 <= metrics.r2 <= 1
        assert len(metrics.feature_importance) > 0
    
    def test_save_model(self, trainer, synthetic_data):
        """Test model saving."""
        findings, labels = synthetic_data
        X, y = trainer.prepare_dataset(findings, labels)
        
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        model, metrics = trainer.train_random_forest(
            X_train, y_train, X_test, y_test,
            n_estimators=10,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"
            
            trainer.save_model(
                model=model,
                model_path=str(model_path),
                model_type="random_forest",
                version="test_v1",
                metrics=metrics,
            )
            
            assert model_path.exists()
    
    def test_training_metrics_rmse(self):
        """Test RMSE calculation."""
        metrics = TrainingMetrics(
            mse=100.0,
            mae=8.0,
            r2=0.85,
            cv_scores=[9.5, 10.2, 9.8],
            feature_importance={},
        )
        
        assert metrics.rmse == 10.0
