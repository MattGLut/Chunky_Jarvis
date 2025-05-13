class MathTool:
    name = "Calculator"

    def invoke(self, input_text: str) -> str:
        try:
            result = eval(input_text, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            return f"Error: {e}"
