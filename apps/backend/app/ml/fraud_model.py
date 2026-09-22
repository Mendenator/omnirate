"""LightGBM fraud classifier (P2-08): trainable end-to-end today against
synthetic data (app/ml/fraud_synthetic_data.py). Retraining against real
production data — the only way to actually claim the AUC>=0.93 / precision>=0.90
@0.7 acceptance — is future work once there's enough real fraud/normal signal
to label (see docs/PROGRESS.md).
"""

from pathlib import Path

import lightgbm as lgb
import numpy as np

from app.ml.fraud_features import FEATURE_NAMES, FraudFeatures

DEFAULT_MODEL_PATH = Path(__file__).parent / "artifacts" / "fraud_model.txt"

TRAIN_PARAMS = {
    "objective": "binary",
    "metric": "auc",
    "num_leaves": 15,
    "learning_rate": 0.05,
    "min_data_in_leaf": 10,
    "verbosity": -1,
}


def train_fraud_model(rows: list[list[float]], labels: list[int], *, num_boost_round: int = 200) -> lgb.Booster:
    dataset = lgb.Dataset(np.array(rows), label=np.array(labels), feature_name=list(FEATURE_NAMES))
    return lgb.train(TRAIN_PARAMS, dataset, num_boost_round=num_boost_round)


def save_model(model: lgb.Booster, path: Path = DEFAULT_MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(path))


def load_model(path: Path = DEFAULT_MODEL_PATH) -> lgb.Booster:
    return lgb.Booster(model_file=str(path))


def predict_fraud_score(model: lgb.Booster, features: FraudFeatures) -> float:
    vector = np.array([features.to_vector()])
    return float(model.predict(vector)[0])
