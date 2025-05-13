from backend.utils.supervisor_state import SupervisorState
from backend.utils.session_store import session_state
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from langchain_ollama import ChatOllama
import os
import re

reflection_llm = ChatOllama(model=os.getenv("REFLECTION_MODEL", "phi"))

def research_agent_node(state: SupervisorState, agent: FakeBindToolsWrapper, reflection_llm) -> SupervisorState:
    current_task = state["task_queue"][0]

    tavily_query = current_task  # Use as-is
    tavily_result = agent.tool_dict["tavily_search"].invoke(tavily_query)

    # Extract best result from Tavily output (typically in 'results' field)
    if isinstance(tavily_result, dict) and 'results' in tavily_result and tavily_result['results']:
        best_result = tavily_result['results'][0]
        result = f"{best_result['content']} (Source: {best_result['url']})"
    else:
        result = "No relevant results found."

    print(f"[Research Agent Result]: {tavily_result}")

    reflection_prompt = (
        "Given the following examples, decide if the task is fully answered. Respond ONLY with 'yes' or 'no'.\n"
        "Only respond with 'yes' if the task is fully answered. If the task is not fully answered, respond with 'no'.\n"
        "Do not add any other context, explanation, or commentary to your response. Just respond with 'yes' or 'no'.\n"
        "Example 1:\n"
        "Task: 'What is the capital of France?'\n"
        "Result: 'The capital of France is Paris.'\n"
        "Answer: yes\n\n"
        "Example 2:\n"
        "Task: 'What is the tallest mountain in the world?'\n"
        "Result: 'Mount Everest is the tallest mountain in the world, standing at 8,848 meters above sea level.'\n"
        "Answer: yes\n\n"
        "Example 3:\n"
        "Task: 'List three uses of AI in healthcare.'\n"
        "Result: 'AI is used in healthcare for diagnostic imaging, personalized treatment plans, and predictive analytics.'\n"
        "Answer: yes\n\n"
        "Example 4:\n"
        "Task: 'What is the capital of Italy?'\n"
        "Result: 'Rome is the capital city of Italy.'\n"
        "Answer: yes\n\n"
        "Example 5:\n"
        "Task: 'Explain the theory of relativity.'\n"
        "Result: 'The theory of relativity is a fundamental principle in physics developed by Albert Einstein.'\n"
        "Answer: no\n\n"
        "Example 6:\n"
        "Task: 'What is the capital of Spain?'\n"
        "Result: 'Madrid is a major European city known for its cultural heritage.'\n"
        "Answer: no\n\n"
        "Example 7:\n"
        "Task: 'Pick a random color.'\n"
        "Result: 'Let's go with Teal.'\n"
        "Answer: yes\n\n"
        "Example 8:\n"
        "Task: 'Pick your favorite fruit.'\n"
        "Result: 'I like apples.'\n"
        "Answer: yes\n\n"
        "Example 9:\n"
        "Task: 'Suggest a weekend hobby.'\n"
        "Result: 'How about hiking?'\n"
        "Answer: yes\n\n"
        "Example 10:\n"
        "Task: 'Tell me about the iPhone 15.'\n"
        "Result: 'The iPhone 15 is Apple's latest smartphone, featuring a new titanium frame, improved cameras, and USB-C charging.'\n"
        "Answer: yes\n\n"
        "Example 11:\n"
        "Task: 'What is LangChain used for?'\n"
        "Result: 'LangChain is a framework for building applications with language models, focusing on composability and tool integrations.'\n"
        "Answer: yes\n\n"
        "Example 12:\n"
        "Task: 'Explain what Black Friday is.'\n"
        "Result: 'Black Friday is a major retail sales event that occurs the day after Thanksgiving in the United States, known for significant discounts and deals.'\n"
        "Answer: yes\n\n"
        "Now, for this task:\n"
        f"Task: '{current_task}'\n"
        f"Result: '{result}'\n"
        "Answer:"
    )

    completion_decision = reflection_llm.invoke(reflection_prompt).content.strip().lower()
    print(f"[Research Agent Reflection]: {completion_decision}")

    state["task_attempts"][current_task] = state["task_attempts"].get(current_task, 0) + 1

    def is_affirmative_response(text: str) -> bool:
        text = text.strip().lower()
        # Normalize typical yes-like starts
        if text.startswith("yes"):
            return True
        if re.match(r"^(yes|yep|correct|fully answered|complete)\b", text):
            return True
        return False

    is_done = is_affirmative_response(completion_decision) or state["task_attempts"][current_task] >= 3

    new_queue = state["task_queue"][1:] if is_done else state["task_queue"]

    return {
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }