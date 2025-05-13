from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.utils.ocr_store import ocr_cache

# Simple memory of last referenced OCR file
last_referenced_file = {"filename": None}

# Limit OCR context tokens (rough estimate: 4 tokens per word)
MAX_OCR_CONTEXT_TOKENS = 1500


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

    # Fallback: infer from chat history
    if not referenced_file and chat_history:
        for entry in reversed(chat_history):
            if 'file' in entry['user'].lower() or 'image' in entry['user'].lower():
                for filename in ocr_cache:
                    if filename.lower() in entry['user'].lower():
                        referenced_file = filename
                        break
            if referenced_file:
                break

    # Fallback: reuse last referenced file
    if not referenced_file and last_referenced_file["filename"]:
        referenced_file = last_referenced_file["filename"]
        print(f"[OCR Agent]: Falling back to last used file '{referenced_file}'")

    # No direct match found, try recent OCR files within context limit
    selected_files = []
    total_tokens = 0
    if not referenced_file:
        print("[OCR Agent]: No explicit file reference found. Attempting recent files fallback.")
        for filename in reversed(list(ocr_cache.keys())):
            ocr_text = ocr_cache[filename]
            estimated_tokens = len(ocr_text.split()) * 4  # Roughly 4 tokens per word
            if total_tokens + estimated_tokens > MAX_OCR_CONTEXT_TOKENS:
                break
            selected_files.append((filename, ocr_text))
            total_tokens += estimated_tokens

    # If we found a referenced file, prioritize it
    if referenced_file:
        ocr_data = ocr_cache.get(referenced_file)
        last_referenced_file["filename"] = referenced_file
        selected_files = [(referenced_file, ocr_data)]

    if not selected_files:
        result = "No OCR data available to answer this question."
    else:
        # Build chat history context
        history_context = ""
        if chat_history:
            history_context = "Conversation so far:\n"
            for entry in chat_history:
                history_context += f"User: {entry['user']}\n"
                history_context += f"Assistant: {entry['assistant']}\n"
            history_context += "\n"

        # Build document context
        document_context = ""
        for filename, ocr_text in selected_files:
            truncated_text = ocr_text[:2000] + ('...' if len(ocr_text) > 2000 else '')
            document_context += f"File: {filename}\nText: {truncated_text}\n\n"

        context_prompt = (
            f"{history_context}"
            f"Available OCR Documents:\n{document_context}"
            f"Task: {current_task}\n"
            "Based on these documents, answer the user's question as best as possible."
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
