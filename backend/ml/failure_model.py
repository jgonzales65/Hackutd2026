import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

class PermitFailurePredictor:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            eval_metric='logloss'
        )

    def generate_synthetic_training_data(self, samples=500):
        """Generates realistic sample municipal data for model training."""
        np.random.seed(42)
        data = {
            'building_age_years': np.random.randint(1, 80, samples),
            'open_violations_count': np.random.randint(0, 10, samples),
            'unpermitted_work_flags': np.random.choice([0, 1], samples, p=[0.7, 0.3]),
            'days_since_last_inspection': np.random.randint(30, 1800, samples),
            'historical_contractor_complaints': np.random.randint(0, 5, samples),
        }
        df = pd.DataFrame(data)
        # Synthetic ground truth for operational failure
        failure_prob = (
            (df['open_violations_count'] * 0.2) +
            (df['unpermitted_work_flags'] * 0.35) +
            (df['days_since_last_inspection'] / 3600)
        )
        df['failure_occurred'] = (failure_prob > 0.6).astype(int)
        return df

    def train(self):
        df = self.generate_synthetic_training_data()
        X = df.drop(columns=['failure_occurred'])
        y = df['failure_occurred']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        print("Model trained successfully.")

    def predict_failure_probability(self, property_features: dict) -> float:
        """Returns the probability (0.0 - 1.0) of an operational/permit failure."""
        df_input = pd.DataFrame([property_features])
        prob = self.model.predict_proba(df_input)[0][1]
        return round(float(prob), 4)

# Usage Example
if __name__ == "__main__":
    predictor = PermitFailurePredictor()
    predictor.train()
    
    sample_parcel = {
        'building_age_years': 45,
        'open_violations_count': 3,
        'unpermitted_work_flags': 1,
        'days_since_last_inspection': 720,
        'historical_contractor_complaints': 2
    }
    prob = predictor.predict_failure_probability(sample_parcel)
    print(f"Predicted Operational Failure Probability: {prob * 100}%")