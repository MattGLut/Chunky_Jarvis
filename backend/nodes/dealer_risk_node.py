from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.tools.dealer_identification_tool import DealerIdentificationTool
from backend.tools.dealer_risk_tool import DealerRiskTool
from backend.utils.dealer_risk_store import dealer_risk_cache
import re
from difflib import get_close_matches

def dealer_risk_node(state: SupervisorState, dealer_risk_agent: FakeBindToolsWrapper, identifier_tool: DealerIdentificationTool, dealer_risk_tool: DealerRiskTool) -> SupervisorState:
    current_task = state["task_queue"][0]

    print(f"[DealerRiskNode Task]: {current_task}")

    dealer_id, llm_guess = identifier_tool.identify_dealer(current_task)

    if dealer_id:
        result = dealer_risk_tool.invoke(dealer_id)
    else:
        if llm_guess and llm_guess != "No match found":
            result = f"I interpreted your input as referring to '{llm_guess}', but could not find this dealer in my records."
        else:
            result = "No matching dealer found. Please specify a dealer_id or lotname."

    print(f"[DealerRiskNode Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop the task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }

