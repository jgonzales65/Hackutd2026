import numpy as np

class CompositeRiskScoringEngine:
    def __init__(self):
        # Weights across four core domain vectors (Sum = 1.0)
        self.category_weights = {
            'environmental': 0.35,
            'title': 0.25,
            'permit': 0.20,
            'zoning': 0.20
        }
        
    def normalize_severity(self, raw_score: float) -> float:
        """Normalizes any score to a 0.0 - 1.0 scale."""
        return max(0.0, min(1.0, raw_score / 100.0))

    def compute_composite_score(self, domain_scores: dict) -> dict:
        """
        domain_scores sample:
        {
            'environmental': 80.0, # e.g. FEMA Flood Zone + Soil Hazard
            'title': 30.0,         # e.g. Single Tax Lien
            'permit': 90.0,        # e.g. Unpermitted construction
            'zoning': 10.0         # e.g. Minor setback variance
        }
        """
        weighted_sum = 0.0
        high_severity_count = 0
        
        for category, score in domain_scores.items():
            normalized = self.normalize_severity(score)
            weighted_sum += normalized * self.category_weights.get(category, 0.0)
            
            # Track compounding risks (scores >= 70)
            if score >= 70.0:
                high_severity_count += 1
        
        # Apply compounding multiplier if multiple severe vectors exist simultaneously
        multiplier = 1.0 + (0.15 * max(0, high_severity_count - 1))
        final_score = min(100.0, weighted_sum * 100.0 * multiplier)
        
        # Assign Risk Rating
        if final_score < 30:
            rating = 'LOW'
        elif final_score < 60:
            rating = 'MEDIUM'
        elif final_score < 80:
            rating = 'HIGH'
        else:
            rating = 'CRITICAL'

        return {
            "composite_risk_score": round(final_score, 2),
            "risk_rating": rating,
            "compounding_applied": multiplier > 1.0
        }

# Usage Example
if __name__ == "__main__":
    engine = CompositeRiskScoringEngine()
    scores = {'environmental': 85.0, 'title': 20.0, 'permit': 75.0, 'zoning': 10.0}
    print("Risk Assessment:", engine.compute_composite_score(scores))