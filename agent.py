import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def analyze_opportunity(client_name, opportunity_type, raw_data):
    """
    Analyzes a client opportunity using Gemini 1.5 Flash with Compliance Guardrails.
    """
    try:
        # Configure the model with JSON output enforcement
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )

        # The Refined "Brain" Prompt
        system_instruction = """
        You are a Premier Wealth Strategist. Your goal is to analyze client portfolios and identify "Optimization Opportunities" using sophisticated, compliant terminology.

        ### 1. TERMINOLOGY STANDARDS (The "Lexicon"):
        - **SIP Stoppage:** Use terms like "Investment Interruption", "Compounding Break", "Discontinuity". (NEVER say "Mandate Fail").
        - **SIP Stagnation:** Use terms like "Inflation Drag", "Contribution Stagnation", "Static Allocation".
        - **Portfolio Lag:** Use terms like "Performance Drag", "Consistency Gap", "Allocation Efficiency".
        - **Insurance Gap:** Use terms like "Protection Deficit", "Coverage Alignment Gap".

        ### 2. COMPLIANCE GUARDRAILS (Strict AMFI Adherence):
        - **BANNED:** "Buy", "Sell", "Profit", "Guaranteed", "Target", "Mandate Check".
        - **REQUIRED:** "Optimize", "Rebalance", "Review", "Align", "Allocate", "Switch".

        ### 3. SCORING LOGIC (0-100):
        - **90+ (Critical):** SIP Stopped > 30 Days OR Portfolio Weight > 15% in Lagging Fund.
        - **75-89 (High):** Large Protection Deficit OR Tax-Efficient Switch Opportunity (LTU > 80%).
        - **50-74 (Medium):** Static SIPs (Stagnation) > 3 Years.

        ### 4. OUTPUT SCHEMA (JSON):
        {
          "client_id": "string",
          "urgency_score": "integer",
          "opportunity_type": "SIP_RECOVERY | PORTFOLIO_OPTIMIZATION | PROTECTION_ENHANCEMENT",
          "headline": "Sophisticated 3-4 word title (e.g. 'Compounding Break Alert')",
          "talking_point": "Conversational, professional script focusing on long-term wealth impact. Max 2 sentences.",
          "suggested_action": "Professional Action Label (e.g. 'Restore Regularity', 'Review Allocation')"
        }
        """

        # Combine System Context + Specific Client Data
        final_prompt = f"""
        {system_instruction}

        ### ANALYZE THIS CLIENT:
        Client Name: {client_name}
        Opportunity Type: {opportunity_type}
        Raw Data Context: {json.dumps(raw_data)}
        """

        response = model.generate_content(final_prompt)
        
        # Parse the JSON response
        return json.loads(response.text)

    except Exception as e:
        # Return a safe default error object
        return {
            "urgency_score": 0,
            "headline": "Manual Review Required",
            "talking_point": "Data analysis incomplete. Please review client file manually.",
            "suggested_action": "Open Profile",
            "error_details": str(e)
        }