from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any, Dict, List
import os
import re
import easyocr

# -------------------------
# FakeBindToolsWrapper
# -------------------------
class FakeBindToolsWrapper:
    def __init__(self, llm, tools: List[Any]):
        self.llm = llm
        self.tool_dict = {tool.name: tool for tool in tools}

    def run(self, input_text: str) -> str:
        llm_response = self.llm.invoke(input_text).content
        print(f"[LLM Response]: {llm_response}")

        tool_call_match = re.search(r'@(\w+)\((.*?)\)', llm_response)
        if tool_call_match:
            tool_name = tool_call_match.group(1)
            tool_input = tool_call_match.group(2).strip(' "\'')

            if tool_name in self.tool_dict:
                print(f"[Tool Call Detected]: {tool_name}('{tool_input}')")
                tool_result = self.tool_dict[tool_name].invoke(tool_input)
                return f"[Tool Result from {tool_name}]: {tool_result}"

            else:
                return f"Unknown tool: {tool_name}"

        return llm_response

# -------------------------
# MathTool Class
# -------------------------
class MathTool:
    name = "Calculator"

    def invoke(self, input_text: str) -> str:
        try:
            result = eval(input_text, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            return f"Error: {e}"

# -------------------------
# OCRTool Class
# -------------------------
class OCRTool:
    name = "OCRDocument"

    def __init__(self):
        self.ocr_data = ""

    def load_document(self, image_path: str):
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path, detail=0)
        self.ocr_data = " ".join(result)
        print(f"[OCR Data Loaded]: {self.ocr_data}")

    def invoke(self, input_text: str) -> str:
        return self.ocr_data if self.ocr_data else "No OCR data loaded."

# -------------------------
# LangGraph State with Task Queue
# -------------------------
class SupervisorState(TypedDict):
    task_queue: List[str]
    last_result: str
    next_agent: str
    done: bool
    task_attempts: Dict[str, int]

# -------------------------
# Nodes
# -------------------------
def supervisor_node(state: SupervisorState, supervisor_llm: ChatOllama) -> SupervisorState:
    if not state["task_queue"]:
        print("[Supervisor Node]: Task queue empty, ending flow.")
        return {**state, "done": True}

    current_task = state["task_queue"][0]
    print(f"[Supervisor Task]: {current_task}")
    prompt = (
        "You are a supervisor managing four agents:\n"
        "- research agent (for web searches)\n"
        "- math agent (for calculations)\n"
        "- llm agent (for general knowledge)\n"
        "- ocr agent (for document scan questions)\n"
        "Use the research agent if the task requires up-to-date information, live data, current events, or anything that could have changed recently.\n"
        "Use the llm agent if the task involves general knowledge, definitions, or static facts that don't change often.\n"
        "Use the ocr agent if the task references scanned documents or extracted text.\n"
        "Respond ONLY with 'research', 'math', 'llm', or 'ocr'.\n"
        f"Task: {current_task}\n"
    )

    decision = supervisor_llm.invoke(prompt).content.strip().lower()
    print(f"[Supervisor Decision]: {decision}")

    if decision in ["math", "research", "llm", "ocr"]:
        return {
            "task_queue": state["task_queue"],
            "last_result": "",
            "next_agent": decision,
            "done": False
        }
    else:
        print("[Supervisor Node]: Invalid decision, ending flow.")
        return {**state, "done": True}

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

reflection_llm = ChatOllama(model="phi")

def research_agent_node(state: SupervisorState, agent: FakeBindToolsWrapper, reflection_llm) -> SupervisorState:
    current_task = state["task_queue"][0]

    tavily_query = f"Extract search query for Tavily based on this task: {current_task}"
    llm_response = agent.llm.invoke(tavily_query).content
    tavily_result = agent.tool_dict["tavily_search"].invoke(llm_response)


    # Extract best result from Tavily output (typically in 'results' field)
    if isinstance(tavily_result, dict) and 'results' in tavily_result and tavily_result['results']:
        best_result = tavily_result['results'][0]
        result = f"{best_result['content']} (Source: {best_result['url']})"
    else:
        result = "No relevant results found."

    print(f"[Research Agent Result]: {tavily_result}")

    reflection_prompt = (
        "Given the following examples, decide if the task is fully answered. Respond ONLY with 'yes' or 'no'.\n"
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
        f"Result: '{best_result}'\n"
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

def llm_agent_node(state: SupervisorState, llm_agent: FakeBindToolsWrapper) -> SupervisorState:
    current_task = state["task_queue"][0]

    # Inject OCR data as context if applicable
    ocr_context = ""
    if "OCRDocument" in llm_agent.tool_dict:
        ocr_data = llm_agent.tool_dict["OCRDocument"].ocr_data
        if ocr_data:
            ocr_context = f"Document Text (from OCR scan):\n{ocr_data}\n\n"

    # Combine context with task prompt
    result = llm_agent.run(ocr_context + current_task)
    print(f"[LLM Agent Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop the task

    return {
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }

# -------------------------
# Build LangGraph Flow
# -------------------------
if __name__ == "__main__":
    # Initialize LLM
    ollama_model = ChatOllama(model=os.getenv("OLLAMA_MODEL", "mistral"))
    reflection_llm = ChatOllama(model=os.getenv("REFLECTION_MODEL", "phi"))

    # Agents
    tavily_tool = TavilySearch(
        max_results=3,
        tavily_api_key="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"
    )
    ocr_tool = OCRTool()

    ocr_agent = FakeBindToolsWrapper(ollama_model, [ocr_tool])
    research_agent = FakeBindToolsWrapper(ollama_model, [tavily_tool])
    math_agent = FakeBindToolsWrapper(ollama_model, [MathTool()])
    llm_agent = FakeBindToolsWrapper(ollama_model, [])

    print(f"Research agent tools: {[tool.name for tool in research_agent.tool_dict.values()]}")
    print(f"Math agent tools: {[tool.name for tool in math_agent.tool_dict.values()]}")
    print(f"LLM agent tools: {[tool.name for tool in llm_agent.tool_dict.values()]}")
    print(f"OCR agent tools: {[tool.name for tool in ocr_agent.tool_dict.values()]}")

    # Build Graph
    graph = StateGraph(SupervisorState)
    graph.add_node("supervisor", lambda state: supervisor_node(state, ollama_model))
    graph.add_node("math", lambda state: math_agent_node(state, math_agent))
    graph.add_node("research", lambda state: research_agent_node(state, research_agent, reflection_llm))
    graph.add_node("llm", lambda state: llm_agent_node(state, llm_agent))
    graph.add_node("ocr", lambda state: llm_agent_node(state, ocr_agent))

    # Entry
    graph.set_entry_point("supervisor")

    # Routing Edges
    graph.add_conditional_edges(
        "supervisor",
        lambda s: END if s["done"] else s["next_agent"],
        {
            "math": "math",
            "research": "research",
            "llm": "llm",
            "ocr": "ocr"
        }
    )

    # After agent nodes, return to supervisor if tasks remain
    graph.add_conditional_edges("math", lambda s: END if s["done"] else "supervisor", {})
    graph.add_conditional_edges("research", lambda s: END if s["done"] else "supervisor", {})
    graph.add_conditional_edges("llm", lambda s: END if s["done"] else "supervisor", {})
    graph.add_conditional_edges("ocr", lambda s: END if s["done"] else "supervisor", {})

    app = graph.compile()

    # -------------------------
    # Example Run with Task Queue
    # -------------------------
    task_list = [
        "What is the capital of Japan?",
        "What is 99 * 3?",
        "Can you pick out a random color?",
        "Can you tell me about toyotathon?",
        "Can you describe making pottery?",
        "What Oauth version is used in ocr_test.png?",
        "Who is the current president of Italy?"
    ]

    ocr_tool.load_document('ocr_files/ocr_test.png')

    for task in task_list:
        task_result = app.invoke({
            "task_queue": [task],
            "last_result": "",
            "next_agent": "",
            "done": False,
            "task_attempts": {}
        })
        print(f"[Task Result]: {task_result['last_result']}")

