from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper

def llm_agent_node(state: SupervisorState, llm_agent: FakeBindToolsWrapper) -> SupervisorState:
    current_task = state["task_queue"][0]
    chat_history = state.get("chat_history", [])

    print(f"[LLM Agent Chat History]: {chat_history}")
    # Build context string from chat history
    history_context = ""
    if chat_history:
        history_context = "Conversation so far:\n"
        for entry in chat_history:
            history_context += f"User: {entry['user']}\n"
            history_context += f"Assistant: {entry['assistant']}\n"
        history_context += "\n"

    # Combine context with current task
    prompt = (
        f"{history_context}"
        f"Current Task: {current_task}\n"
        "Answer concisely and helpfully."
    )

    print(f"[LLM Agent Task]: {prompt}")

    result = llm_agent.run(prompt)
    print(f"[LLM Agent Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop the current task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }
