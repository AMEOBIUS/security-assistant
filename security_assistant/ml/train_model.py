"""
Train and save baseline ML model for vulnerability scoring.

Usage:
    python -m security_assistant.ml.train_model
"""

import logging
from pathlib import Path

from security_assistant.ml.epss import EPSSClient
from security_assistant.ml.training import ModelTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Train and save baseline model."""
    logger.info("Starting model training...")

    # Initialize trainer
    epss_client = EPSSClient(cache_enabled=True)
    trainer = ModelTrainer(epss_client=epss_client, random_state=42)

    # Generate synthetic training data
    logger.info("Generating synthetic training data...")
    findings, labels = trainer.generate_synthetic_data(n_samples=1000)

    # Prepare dataset
    logger.info("Preparing dataset...")
    X, y = trainer.prepare_dataset(findings, labels)

    # Split train/test
    split_idx = int(0.8 * len(X))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Train baseline model
    logger.info("Training baseline model...")
    baseline_model, baseline_metrics = trainer.train_baseline(
        X_train, y_train, X_test, y_test
    )

    # Save baseline model
    models_dir = Path("security_assistant/ml/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = models_dir / "baseline_v1.pkl"
    trainer.save_model(
        model=baseline_model,
        model_path=str(baseline_path),
        model_type="logistic_regression",
        version="1.0.0",
        metrics=baseline_metrics,
    )

    logger.info(f"✅ Baseline model saved to {baseline_path}")
    logger.info(f"   RMSE: {baseline_metrics.rmse:.2f}")
    logger.info(f"   MAE: {baseline_metrics.mae:.2f}")
    logger.info(f"   R²: {baseline_metrics.r2:.3f}")

    # Train Random Forest model
    logger.info("Training Random Forest model...")
    rf_model, rf_metrics = trainer.train_random_forest(
        X_train,
        y_train,
        X_test,
        y_test,
        n_estimators=100,
        max_depth=10,
    )

    # Save Random Forest model
    rf_path = models_dir / "random_forest_v1.pkl"
    trainer.save_model(
        model=rf_model,
        model_path=str(rf_path),
        model_type="random_forest",
        version="1.0.0",
        metrics=rf_metrics,
    )

    logger.info(f"✅ Random Forest model saved to {rf_path}")
    logger.info(f"   RMSE: {rf_metrics.rmse:.2f}")
    logger.info(f"   MAE: {rf_metrics.mae:.2f}")
    logger.info(f"   R²: {rf_metrics.r2:.3f}")

    # Compare models
    logger.info("\n📊 Model Comparison:")
    logger.info(f"Baseline RMSE: {baseline_metrics.rmse:.2f}")
    logger.info(f"Random Forest RMSE: {rf_metrics.rmse:.2f}")

    if rf_metrics.rmse < baseline_metrics.rmse:
        improvement = (
            (baseline_metrics.rmse - rf_metrics.rmse) / baseline_metrics.rmse * 100
        )
        logger.info(f"✅ Random Forest is {improvement:.1f}% better!")
    else:
        logger.info("⚠️  Baseline performs better (use more training data)")

    logger.info("\n🎉 Training complete!")


if __name__ == "__main__":
    main()
