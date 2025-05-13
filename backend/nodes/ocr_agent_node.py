from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.utils.ocr_store import ocr_cache

# Simple memory of last referenced OCR file
last_referenced_file = {"filename": None}

def ocr_agent_node(state: SupervisorState, ocr_agent: FakeBindToolsWrapper) -> SupervisorState:
    current_task = state["task_queue"][0]
    chat_history = state.get("chat_history", [])

    print(f"[OCR Agent Chat History]: {chat_history}")

    # Search current task for file references
    referenced_file = None
    for filename in ocr_cache:
        if filename.lower() in current_task.lower():
            referenced_file = filename
            break

    # Fallback: try to infer from chat history ("that file", etc.)
    if not referenced_file and chat_history:
        for entry in reversed(chat_history):
            if 'file' in entry['user'].lower() or 'image' in entry['user'].lower():
                for filename in ocr_cache:
                    if filename.lower() in entry['user'].lower():
                        referenced_file = filename
                        break
            if referenced_file:
                break

    # Fallback: reuse last referenced file if no new reference found
    if not referenced_file and last_referenced_file["filename"]:
        referenced_file = last_referenced_file["filename"]
        print(f"[OCR Agent]: Falling back to last used file '{referenced_file}'")

    if referenced_file:
        ocr_data = ocr_cache.get(referenced_file, None)
        last_referenced_file["filename"] = referenced_file  # Update memory
        print(f"[OCR Agent]: Using OCR data for '{referenced_file}'")
    else:
        ocr_data = None
        print("[OCR Agent]: No matching OCR file referenced in task or chat history.")

    # Prepare prompt with context if OCR data found
    if not ocr_data:
        result = "No OCR data available to answer this question."
    else:
        # Build context from chat history
        history_context = ""
        if chat_history:
            history_context = "Conversation so far:\n"
            for entry in chat_history:
                history_context += f"User: {entry['user']}\n"
                history_context += f"Assistant: {entry['assistant']}\n"
            history_context += "\n"

        context_prompt = (
            f"{history_context}"
            f"Document Text (from OCR scan of '{referenced_file}'):\n{ocr_data}\n\n"
            f"Task: {current_task}\n"
            "Based on the OCR'd document text, answer the user's question as best as possible."
        )
        result = ocr_agent.run(context_prompt)

    print(f"[OCR Agent Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }
