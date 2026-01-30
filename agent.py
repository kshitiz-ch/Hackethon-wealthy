import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('AIzaSyA44KTejygzE3PCYhvXEe_2ZUJ0ibd38Hg'))

# --- CONFIGURATION ---
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

SYSTEM_PROMPT = """
You are a **Senior Wealth Intelligence Engine**. Your goal is to analyze raw financial datasets and synthesize a "High-Impact Advisor Dashboard" json.

### INPUT DATA STREAMS:
1. **Portfolio Review:** Clients with underperforming schemes (Negative Alpha/XIRR Gap).
2. **Stagnant SIPs:** SIPs running >2 years with 0% step-up.
3. **Stopped SIPs:** Active SIPs with no payments in >2 months.
4. **Insurance Gaps:** High-net-worth clients with low/no coverage.

### YOUR TASKS:

#### 1. CALCULATE "TOTAL OPPORTUNITY VALUE" (The Hero Metric)
Normalize and sum these figures to get one "Wealth Impact" score:
- **Stopped SIPs:** Annualized Value (Monthly Amount * 12).
- **Stagnant SIPs:** Potential Step-up Value (Assume 10% of current SIP * 12).
- **Insurance:** The `premium_gap` provided directly.
- **Portfolio:** 1% of the `current_value` of underperforming funds (Assumed advisory fee impact).

#### 2. IDENTIFY "TOP 10 FOCUS CLIENTS"
- Group all data by `client_id`.
- Score clients based on complexity and value. A client with *multiple* issues (e.g., Stopped SIP + Insurance Gap) ranks higher.
- Select the top 10 highest-value clients.

#### 3. GENERATE THE "WHY" (The Pitch)
- **Dashboard Header:** 1-sentence executive summary (e.g., "Identified ₹12.5L in potential value across 45 clients...").
- **Client Hook:** A short context string for the list view (e.g., "High Churn Risk: Stopped SIP of ₹10k/mo + ₹2Cr Insurance Gap.").

---

### STRICT JSON OUTPUT SCHEMA:
{
  "dashboard_hero": {
    "total_opportunity_value": "Float (The calculated sum)",
    "formatted_value": "String (e.g., '₹15.2 Lakhs')",
    "executive_summary": "String",
    "opportunity_breakdown": {
      "insurance": "String (e.g. '₹10L')",
      "sip_recovery": "String (e.g. '₹5L')",
      "portfolio_rebalancing": "String (e.g. '₹20K')"
    }
  },
  "top_focus_clients": [
    {
      "user_id": "String",
      "client_name": "String",
      "total_impact_value": "String (e.g. '₹1.5 L')",
      "tags": ["Array of Strings", e.g., "Risk: Stopped SIP", "Opp: Insurance"],
      "pitch_hook": "String (Max 2 lines)",
      "drill_down_details": {
        "portfolio_review": {
           "has_issue": "Boolean",
           "schemes": [ { "name": "String", "xirr_lag": "Float" } ]
        },
        "sip_health": {
           "stopped_sips": [ { "scheme": "String", "days_stopped": "Int", "amount": "Float" } ],
           "stagnant_sips": [ { "scheme": "String", "years_running": "Float" } ]
        },
        "insurance": {
           "has_gap": "Boolean",
           "gap_amount": "Float",
           "wealth_band": "String"
        }
      }
    }
  ]
}
"""

def generate_dashboard_insight(portfolio_data, stagnant_data, stopped_data, insurance_data):
    """
    Aggregates the 4 data streams and calls Gemini to build the Dashboard JSON.
    """
    try:
        # Construct the context payload
        input_payload = f"""
        ### RAW DATASETS FOR ANALYSIS:
        
        1. PORTFOLIO REVIEW (Underperforming Funds):
        {json.dumps(portfolio_data, default=str)}

        2. STAGNANT SIP DATA (Growth Opps):
        {json.dumps(stagnant_data, default=str)}

        3. STOPPED SIP DATA (Risk Alerts):
        {json.dumps(stopped_data, default=str)}

        4. INSURANCE OPPORTUNITY DATA (Protection Gaps):
        {json.dumps(insurance_data, default=str)}
        """

        response = model.generate_content(SYSTEM_PROMPT + input_payload)
        return json.loads(response.text)

    except Exception as e:
        print(f"AI Agent Error: {e}")
        # Return a safe fallback so the UI doesn't crash
        return {
            "dashboard_hero": {
                "total_opportunity_value": 0,
                "formatted_value": "Calculating...",
                "executive_summary": "AI is analyzing your client data. Please refresh shortly.",
                "opportunity_breakdown": {"insurance": "0", "sip_recovery": "0", "portfolio_rebalancing": "0"}
            },
            "top_focus_clients": []
        }