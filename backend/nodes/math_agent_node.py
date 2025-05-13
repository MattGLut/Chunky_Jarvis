from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper

def math_agent_node(state: SupervisorState, math_agent: FakeBindToolsWrapper) -> SupervisorState:
    current_task = state["task_queue"][0]
    result = math_agent.run(current_task)
    print(f"[Math Agent Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop the first task

    return {
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": True
    }