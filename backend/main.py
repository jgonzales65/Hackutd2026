from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analytics.risk_engine import CompositeRiskScoringEngine
from analytics.capex_calculator import FinancialImpactCalculator
from ml.failure_model import PermitFailurePredictor

app = FastAPI(title="TerraIntel Risk Intelligence API", version="1.0")

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
risk_engine = CompositeRiskScoringEngine()
failure_predictor = PermitFailurePredictor()
# Train model on startup for demo/MVP purposes
failure_predictor.train()

class ParcelEvaluationRequest(BaseModel):
    parcel_id: str
    base_land_value: float
    domain_scores: dict  # e.g., {"environmental": 85, "title": 20, "permit": 75, "zoning": 10}
    property_features: dict # e.g., building age, violations count, etc.
    active_risks: list # e.g., ["FEMA_FLOOD_PLAIN", "UNPERMITTED_UTILITY"]

@app.post("/api/evaluate-parcel")
def evaluate_parcel(req: ParcelEvaluationRequest):
    try:
        # 1. Compute Composite Risk Score
        risk_result = risk_engine.compute_composite_score(req.domain_scores)
        
        # 2. Predict Failure Probability
        failure_prob = failure_predictor.predict_failure_probability(req.property_features)
        
        # 3. Calculate Financial CapEx & Adjusted Value
        capex_calc = FinancialImpactCalculator(base_land_value=req.base_land_value)
        financial_result = capex_calc.calculate_adjusted_land_value(req.active_risks)
        
        return {
            "parcel_id": req.parcel_id,
            "risk_assessment": risk_result,
            "failure_probability_percent": round(failure_prob * 100, 2),
            "financial_impact": financial_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)