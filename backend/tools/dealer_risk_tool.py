import requests
import os
from backend.utils.dealer_risk_store import dealer_risk_cache

class DealerRiskTool:
    name = "DealerRiskAnalyzer"

    def __init__(self, api_url: str, api_key: str, llm):
        self.api_url = api_url
        self.api_key = api_key
        self.llm = llm

    def load_risk_index(self):
        print("[DealerRiskTool] Loading dealer risk index from API...")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(f"{self.api_url}/dealer_risk_index", headers=headers)

        if response.status_code != 200:
            print(f"[DealerRiskTool] Failed to load dealer risk index: {response.status_code}")
            return

        dealer_risk_cache.update(response.json())
        print(f"[DealerRiskTool] Loaded {len(dealer_risk_cache)} dealers into cache.")

    def invoke(self, dealer_identifier: str) -> str:
        print(f"[DealerRiskTool] Searching risk data for: {dealer_identifier}")

        match = None
        for dealer_id, dealer_data in dealer_risk_cache.items():
            if dealer_identifier.lower() in dealer_id.lower() or dealer_identifier.lower() in dealer_data.get("name", "").lower():
                match = dealer_data
                break

        if not match:
            return f"No dealer risk data found for identifier '{dealer_identifier}'."

        prompt = (
            f"Dealer Risk Data:\n{match}\n\n"
            "Task: Provide an insightful dealer risk analysis in this format:\n"
            "- Repo Risk % and what it means\n"
            "- Top 3 risk factors\n"
            "- Recommendations for mitigation\n"
            "Be concise and insightful."
        )

        result = self.llm.invoke(prompt)
        return result
