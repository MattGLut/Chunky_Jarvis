import os
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from backend.utils.supervisor_state import SupervisorState
from backend.nodes.supervisor_node import supervisor_node
from backend.nodes.math_agent_node import math_agent_node
from backend.nodes.research_agent_node import research_agent_node
from backend.nodes.llm_agent_node import llm_agent_node
from backend.nodes.ocr_agent_node import ocr_agent_node
from backend.nodes.dealer_risk_node import dealer_risk_node
from backend.tools.ocr_tool import OCRTool
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.tools.math_tool import MathTool
from backend.tools.dealer_risk_tool import DealerRiskTool
from backend.tools.dealer_identification_tool import DealerIdentificationTool

# Initialize LLM
supervisor_llm = ChatOllama(model=os.getenv("SUPERVISOR_MODEL", "llama3"), temperature=0.0)
ollama_model = ChatOllama(model=os.getenv("OLLAMA_MODEL", "mistral"))
reflection_llm = ChatOllama(model=os.getenv("REFLECTION_MODEL", "phi"))

# Agents
tavily_tool = TavilySearch(
    max_results=3,
    tavily_api_key="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"
)
ocr_tool = OCRTool()
dealer_risk_tool = DealerRiskTool(api_url=os.getenv("DORA_API_URL", ""), api_key=os.getenv("DORA_API_KEY", ""), llm=ollama_model)
dealer_identifier_tool = DealerIdentificationTool(llm=ollama_model)

ocr_agent = FakeBindToolsWrapper(ollama_model, [ocr_tool])
# research_agent = FakeBindToolsWrapper(ollama_model, [tavily_tool])
# math_agent = FakeBindToolsWrapper(ollama_model, [MathTool()])
llm_agent = FakeBindToolsWrapper(ollama_model, [])
dealer_risk_agent = FakeBindToolsWrapper(ollama_model, [dealer_risk_tool])

# print(f"Research agent tools: {[tool.name for tool in research_agent.tool_dict.values()]}")
# print(f"Math agent tools: {[tool.name for tool in math_agent.tool_dict.values()]}")
print(f"LLM agent tools: {[tool.name for tool in llm_agent.tool_dict.values()]}")
print(f"OCR agent tools: {[tool.name for tool in ocr_agent.tool_dict.values()]}")
print(f"Dealer risk agent tools: {[tool.name for tool in dealer_risk_agent.tool_dict.values()]}")

# Build Graph
graph = StateGraph(SupervisorState)
graph.add_node("supervisor", lambda state: supervisor_node(state, supervisor_llm))
# graph.add_node("math", lambda state: math_agent_node(state, math_agent))
# graph.add_node("research", lambda state: research_agent_node(state, research_agent, reflection_llm))
graph.add_node("llm", lambda state: llm_agent_node(state, llm_agent))
graph.add_node("ocr", lambda state: ocr_agent_node(state, ocr_agent))
graph.add_node("dealer_risk", lambda state: dealer_risk_node(state, dealer_risk_agent, dealer_identifier_tool))

# Entry
graph.set_entry_point("supervisor")

# Routing Edges
graph.add_conditional_edges(
    "supervisor",
    lambda s: END if s["done"] else s["next_agent"],
    {
        # "math": "math",
        # "research": "research",
        "llm": "llm",
        "ocr": "ocr",
        "dealer_risk": "dealer_risk"
    }
)

# After agent nodes, return to supervisor if tasks remain
# graph.add_conditional_edges("math", lambda s: END if s["done"] else "supervisor", {})
# graph.add_conditional_edges("research", lambda s: END if s["done"] else "supervisor", {})
graph.add_conditional_edges("llm", lambda s: END if s["done"] else "supervisor", {})
graph.add_conditional_edges("ocr", lambda s: END if s["done"] else "supervisor", {})
graph.add_conditional_edges("dealer_risk", lambda s: END if s["done"] else "supervisor", {})

app = graph.compile()
