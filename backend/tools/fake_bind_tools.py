import re

class FakeBindToolsWrapper:
    def __init__(self, llm, tools):
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
                return f"[Tool Result from {tool_name}]: {self.tool_dict[tool_name].invoke(tool_input)}"
            else:
                return f"Unknown tool: {tool_name}"

        return llm_response
