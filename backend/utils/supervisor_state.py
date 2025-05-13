from typing import TypedDict, Any, Dict, List

class SupervisorState(TypedDict):
    task_queue: List[str]
    last_result: str
    next_agent: str
    done: bool
    task_attempts: Dict[str, int]
    chat_history: List[Dict[str, str]] = []