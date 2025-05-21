import requests
import os
from backend.utils.dealer_risk_store import (
    dealer_risk_cache,
    dealer_risk_feature_importance,
    dealer_risk_classification_report,
)

def load_risk_index(self):
    print("[DealerRiskTool] Loading dealer risk index from API...")
    headers = {"x-api-key": self.api_key}
    url = f"{self.api_url}/dealer_risk_index"
    print(f"[DealerRiskTool] Fetching: {url}")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[DealerRiskTool] Failed to load dealer risk index: {response.status_code}")
        print(f"Response content: {response.text}")
        return

    data = response.json()

    if not isinstance(data.get("results"), list):
        print("[DealerRiskTool] Unexpected response format: 'results' is missing or not a list.")
        return

    dealer_risk_cache.clear()
    dealer_risk_cache.update({str(d["id"]): d for d in data["results"]})

    dealer_risk_feature_importance.clear()
    dealer_risk_feature_importance.update(data.get("feature_importance", {}))

    dealer_risk_classification_report.clear()
    dealer_risk_classification_report.update(data.get("classification_report", {}))

    print(f"[DealerRiskTool] Loaded {len(dealer_risk_cache)} dealers into cache.")
    print(f"[DealerRiskTool] Stored {len(dealer_risk_feature_importance)} feature importance weights.")

def invoke(self, dealer_identifier: str) -> str:
    print(f"[DealerRiskTool] Searching risk data for: {dealer_identifier}")

    match = None
    dealer_id_match = None

    # Search by dealer_id or lotname (case-insensitive)
    for dealer_id, dealer_data in dealer_risk_cache.items():
        if dealer_identifier.lower() in dealer_id.lower() or dealer_identifier.lower() in dealer_data.get("lotname", "").lower():
            match = dealer_data
            dealer_id_match = dealer_id
            break

    if not match:
        return f"No dealer risk data found for identifier '{dealer_identifier}'."

    # Extract only relevant features from match
    selected_features = {
        k: match.get(k, None) for k in dealer_risk_feature_importance.keys()
    }

    # Format the selected features for prompt
    formatted_features = "\n".join(
        f"- {k}: {v if v is not None else 'null'}"
        for k, v in selected_features.items()
    )

    # Optionally include the global importance values
    importance_summary = "\n".join(
        f"- {k}: {round(weight * 100, 2)}%"
        for k, weight in sorted(dealer_risk_feature_importance.items(), key=lambda x: x[1], reverse=True)
    )

    prompt = (
        f"Dealer Risk Analysis Input:\n"
        f"Dealer Lotname: {match.get('lotname', 'N/A')}\n"
        f"Dealer ID: {dealer_id_match}\n"
        f"Repo Probability: {match.get('repo_probability', 'N/A'):.6f}\n\n"
        f"Selected Features:\n{formatted_features}\n\n"
        f"Model Feature Importances:\n{importance_summary}\n\n"
        "Task:\n"
        "- Explain what the repo risk means for this dealer\n"
        "- Identify the 3 most concerning features\n"
        "- Recommend actions to mitigate risk\n"
        "Be concise, accurate, and avoid repeating feature names unnecessarily."
    )

    result = self.llm.invoke(prompt)
    return result
