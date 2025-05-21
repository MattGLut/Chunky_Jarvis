from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.tools.dfp_db_tool import DFPDatabaseTool
from backend.utils.dfp_schema import DFP_SCHEMA, DFP_ENUMS, DFP_RELATIONSHIPS, DFP_FEWSHOT_EXAMPLES

def dfp_db_node(state: SupervisorState, db_agent: FakeBindToolsWrapper, db_tool: DFPDatabaseTool) -> SupervisorState:
    current_task = state["task_queue"][0]
    print(f"[DFP DB Node Task]: {current_task}")

    try:
        prompt = (
            "You are a SQL assistant with read-only access to a MySQL database for an automotive finance company.\n\n"
            "The backend app is called 'DFP' and users may refer to it as such.\n\n"
            "Your job is to write safe, minimal SELECT queries based on user requests.\n\n"
            "Do NOT include DELETE, UPDATE, INSERT, or DDL statements. Only SELECT queries.\n\n"
            "Do not include any other text or comments in your response. Just the SQL query.\n\n"
            "The query you return will be executed against the database, so it must be syntactically correct and valid.\n\n"
            "The possibly relevant database schema is as follows. Please assume these are the only tables and columns available to you when writing queries:\n"
            f"Schema:\n{DFP_SCHEMA}\n\n"
            "The following are enums and relationships that you can use to help you write your query:\n"
            f"Enums:\n{DFP_ENUMS}\n\n"
            f"Relationships:\n{DFP_RELATIONSHIPS}\n\n"
            f"Here are some examples:\n{DFP_FEWSHOT_EXAMPLES}\n\n"
            f"User request: {current_task}\n"
            "SQL:"
        )
        llm_response = db_agent.llm.invoke(prompt)
        sql_query = llm_response.content.strip() if hasattr(llm_response, "content") else str(llm_response).strip()

        print(f"[DFP DB Node SQL Generated]: {sql_query}")

        result = db_tool.invoke(sql_query)
    except Exception as e:
        result = f"❌ Failed to process query: {e}"

    print(f"[DFP DB Node Result]: {result}")

    new_queue = state["task_queue"][1:]  # Pop task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": result,
        "next_agent": "",
        "done": not new_queue
    }
