import re
from difflib import get_close_matches
from backend.utils.dealer_risk_store import dealer_risk_cache

class DealerIdentificationTool:
    name = "DealerIdentificationTool"

    def __init__(self, llm=None):
        self.llm = llm  # Optional for LLM-assisted fallback

    def identify_dealer(self, user_input: str) -> str | None:
        print(f"[DealerIdentifier] Analyzing input: {user_input}")

        # 1. Direct ID match (4-8 digit numbers)
        id_candidates = re.findall(r'\b\d{4,8}\b', user_input)
        print(f"[DealerIdentifier] ID Candidates: {id_candidates}")

        known_ids = dealer_risk_cache.keys()
        for candidate in id_candidates:
            if candidate in known_ids:
                print(f"[DealerIdentifier] Found exact dealer_id: {candidate}")
                return candidate

        # 2. Fuzzy lotname match
        lotnames = {v.get("lotname", "").lower(): k for k, v in dealer_risk_cache.items()}
        close_matches = get_close_matches(user_input.lower(), lotnames.keys(), n=1, cutoff=0.6)
        if close_matches:
            matched_name = close_matches[0]
            dealer_id = lotnames[matched_name]
            print(f"[DealerIdentifier] Soft matched lotname '{matched_name}' to dealer_id: {dealer_id}")
            return dealer_id

        # 3. Optional LLM-assisted extraction
        if self.llm:
            prompt = (
                "You are tasked with identifying an automobile dealership from user input. Your job is to return either the dealer_id (as a number) "
                "or the exact name (as string). Only respond with a single dealer_id or dealershipname.\n\n"
                "Guidelines:\n"
                "- Prefer dealer_id if explicitly mentioned.\n"
                "- If dealer_id is missing but dealership name is referenced, match it as best you can.\n"
                "- If uncertain, reply exactly with 'No match found'.\n"
                "- Do not explain yourself. Only return the ID or name.\n"
                "- Do not make up a dealer_id or name if you cannot find one.\n"
                "- If you can identify a dealership name, return the dealership name. If you can identify a dealer_id, return the dealer_id.\n"
                "- Dealership names may be lowercase, have spaces or special characters, or include business tags like LLC, Inc, or Corp.\n"
                "- Important: Return only the dealer_id number or dealership name text. Do NOT add assumptions, explanations, or extra formatting.\n\n"
                "Examples:\n"
                "Input: 'What's the risk for dealer_id 12345?'\n"
                "Output: 12345\n\n"
                "Input: 'Tell me about Sunset Motors'\n"
                "Output: Sunset Motors\n\n"
                "Input: 'How risky is ABC Auto World?'\n"
                "Output: ABC Auto World\n\n"
                "Input: 'Can you analyze 98765 for me?'\n"
                "Output: 98765\n\n"
                "Input: 'What's going on with that small lot in Tulsa?'\n"
                "Output: No match found\n\n"
                "Input: 'I'm looking for a dealer in San Francisco'\n"
                "Output: No match found\n\n"
                "Input: 'Tell me about Acura autos'\n"
                "Output: Acura autos\n\n"
                "Input: 'Help me out, I'm needing analysis on dealer id 800765, champions auto'\n"
                "Output: 800765\n\n"
                "Input: 'Can you get me risk analysis for Tom's Motors LLC?'\n"
                "Output: Tom's Motors LLC\n\n"
                "Input: 'What's the risk for dealer_id Wisconsin auto sales?'\n"
                "Output: Wisconsin Auto Sales\n\n"
                "Input: 'Give me a risk report for dealer Tacos LLC'\n"
                "Output: Tacos LLC\n\n"
                f"User Input: '{user_input}'\n"
                "Output:"
            )

            response = self.llm.invoke(prompt)
            result = response.content.strip() if hasattr(response, "content") else str(response).strip()
            print(f"[DealerIdentifier] LLM Fallback Result: {result}")

            if result.isdigit() and result in known_ids:
                return result, result
            close_matches = get_close_matches(result.lower(), lotnames.keys(), n=1, cutoff=0.6)
            if close_matches:
                matched_name = close_matches[0]
                dealer_id = lotnames[matched_name]
                print(f"[DealerIdentifier] LLM soft matched lotname '{matched_name}' to dealer_id: {dealer_id}")
                return dealer_id, result

            print("[DealerIdentifier] LLM result did not match known dealers.")
            return None, result  # LLM found something, but no match

        print("[DealerIdentifier] No dealer match found.")
        return None, None
