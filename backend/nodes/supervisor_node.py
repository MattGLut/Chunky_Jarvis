from backend.utils.supervisor_state import SupervisorState
from langchain_ollama import ChatOllama

def supervisor_node(state: SupervisorState, supervisor_llm: ChatOllama) -> SupervisorState:
    VALID_AGENTS = {"llm", "ocr", "dealer_risk", "dfp_db"}

    if not state["task_queue"]:
        print("[Supervisor Node]: Task queue empty, ending flow.")
        return {**state, "done": True}

    current_task = state["task_queue"][0]
    print(f"[Supervisor Task]: {current_task}")
    prompt = (
        "You are a supervisor managing four agents:\n"
        "- dealer_risk agent (for dealer risk analysis)\n"
        "- ocr agent (for document scan questions)\n"
        # "- research agent (for web searches)\n"
        # "- math agent (for calculations)\n"
        "- llm agent (for general knowledge)\n"
        "- dfp_db agent (for dfp database queries)\n"
        # "Use the research agent if the task requires up-to-date information, live data, current events, or anything that could have changed recently. Only use the research agent if the prompt explicitly asks for it.\n"
        "Use the llm agent if the task involves general knowledge, definitions, or static facts that don't change often.\n"
        "Use the ocr agent if the task references scanned documents or extracted text. Always use this if the task is about an uploaded file.\n"
        "Use the dealer_risk agent if the task is about analyzing dealer risk. Always use this if the task is about a dealer risk analysis. Users may specify this as a viper risk score.\n"
        "Use the dfp_db agent if the task is about querying the FloorplanXpress database. Always use this if the task is about a database query.\n"
        # "Do not use the research agent for dealer risk analysis.\n"
        # "Respond ONLY with 'research', 'math', 'llm', 'ocr', or 'dealer_risk'.\n"
        "Respond ONLY with 'llm', 'ocr', 'dealer_risk', or 'dfp_db'.\n\n"
        "Do not add any other text to your response. Just respond with the agent name. Do no embelish the agent name, or give reasoning for your choice.\n"
        "Examples:\n"
        "Task: 'What is the risk score for dealer_id 12345?'\n"
        "Answer: dealer_risk\n\n"
        "Task: 'Can you analyze the text in invoice.png?'\n"
        "Answer: ocr\n\n"
        "Task: 'Define what a floorplan loan is.'\n"
        "Answer: llm\n\n"
        "Task: 'What does the OCR scan of contract.pdf say about payment terms?'\n"
        "Answer: ocr\n\n"
        "Task: 'Give me the viper score for ABC Auto World.'\n"
        "Answer: dealer_risk\n\n"
        "Task: 'Explain the difference between recourse and non-recourse lending.'\n"
        "Answer: llm\n\n"
        "Task: 'What is the total amount of active dealers in the database?'\n"
        "Answer: dfp_db\n\n"
        "Task: 'What is the total amount of current units?'\n"
        f"Task: {current_task}\n"
        "Answer:"
    )

    decision = supervisor_llm.invoke(prompt).content.strip().lower()
    print(f"[Supervisor Decision]: {decision}")

    # Post-process: Extract valid decision keyword
    for valid in VALID_AGENTS:
        if valid in decision:
            print(f"[Sanitized Supervisor Decision]: {valid}")
            next_agent = valid
            break
    else:
        print("[Supervisor Node]: Invalid decision, ending flow.")
        return {**state, "done": True}

    # if next_agent in ["math", "research", "llm", "ocr", "dealer_risk"]:
    if next_agent in ["llm", "ocr", "dealer_risk", "dfp_db"]:
        return {
            "task_queue": state["task_queue"],
            "last_result": "",
            "next_agent": next_agent,
            "done": False
        }
    else:
        print("[Supervisor Node]: Invalid decision, defaulting to llm.")
        return {
            "task_queue": state["task_queue"],
            "last_result": "",
            "next_agent": "llm",
            "done": False
        }
