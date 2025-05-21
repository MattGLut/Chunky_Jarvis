from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper

def dfp_db_node(state: SupervisorState, db_agent: FakeBindToolsWrapper) -> SupervisorState:
    current_task = state["task_queue"][0]
    print(f"[DFP DB Node Task]: {current_task}")

    result = db_agent.run(current_task)
    print(f"[DFP DB Node Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }
