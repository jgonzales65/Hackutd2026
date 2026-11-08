class FinancialImpactCalculator:
    def __init__(self, base_land_value: float, holding_cost_per_month: float = 2500.0):
        self.base_land_value = base_land_value
        self.holding_cost_per_month = holding_cost_per_month
        
        # Standard baseline mitigation cost estimates per issue type
        self.cost_benchmarks = {
            'FEMA_FLOOD_PLAIN': 45000.0,
            'UNPERMITTED_UTILITY': 18000.0,
            'SOIL_SUBSIDENCE': 35000.0,
            'TITLE_LIEN_CLEARANCE': 12000.0,
            'ZONING_VARIANCE_DELAY': 6.0 # Months of delay
        }

    def calculate_adjusted_land_value(self, active_risks: list) -> dict:
        """
        Formula: 
        Adjusted Value = Base Value - Sum(Direct CapEx) - (Holding Delay Costs)
        """
        total_capex = 0.0
        total_delay_months = 0.0
        risk_breakdown = []

        for risk_key in active_risks:
            if risk_key in self.cost_benchmarks:
                cost = self.cost_benchmarks[risk_key]
                if 'DELAY' in risk_key:
                    total_delay_months += cost
                else:
                    total_capex += cost
                    risk_breakdown.append({"risk": risk_key, "estimated_capex": cost})

        total_holding_cost = total_delay_months * self.holding_cost_per_month
        total_impact = total_capex + total_holding_cost
        adjusted_value = max(0.0, self.base_land_value - total_impact)

        return {
            "base_land_value": self.base_land_value,
            "total_capex_mitigation": total_capex,
            "estimated_holding_delay_months": total_delay_months,
            "total_holding_cost": total_holding_cost,
            "total_financial_impact": total_impact,
            "adjusted_land_value": adjusted_value,
            "value_discount_percent": round((total_impact / self.base_land_value) * 100, 2),
            "itemized_breakdown": risk_breakdown
        }

# Usage Example
if __name__ == "__main__":
    calc = FinancialImpactCalculator(base_land_value=320000.00)
    risks = ['FEMA_FLOOD_PLAIN', 'UNPERMITTED_UTILITY', 'ZONING_VARIANCE_DELAY']
    result = calc.calculate_adjusted_land_value(risks)
    print("Financial Impact Breakdown:", result)