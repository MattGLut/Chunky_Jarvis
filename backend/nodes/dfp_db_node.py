from backend.utils.supervisor_state import SupervisorState
from backend.tools.fake_bind_tools import FakeBindToolsWrapper
from backend.utils.dfp_schema import DFP_SCHEMA, DFP_FEWSHOT_EXAMPLES
from backend.tools.dfp_db_tool import DFPDatabaseTool
import time
from datetime import datetime
import pytz

def dfp_db_node(state: SupervisorState, db_agent: FakeBindToolsWrapper, db_tool: DFPDatabaseTool) -> SupervisorState:
    current_task = state["task_queue"][0]
    print(f"[DFP DB Node Task]: {current_task}")

    attempt = 0
    max_attempts = 3
    sql_query = ""
    raw_result = ""

    while attempt < max_attempts:
        try:
            # Step 1: Generate SQL using LLM with schema and few-shot context
            prompt = (
                "You are a SQL generation assistant for an internal analytics tool.\n\n"
                "Strict rules you MUST follow:\n"
                "- ONLY generate a single SELECT query.\n"
                "- NEVER include comments, notes, or explanations in the query.\n"
                "- DO NOT reference columns that do not exist in the provided schema.\n"
                "- If a request is unclear or references unknown columns, return: SELECT 'Unclear request — cannot generate safe query';\n\n"
                "DFP stands for Direct Floor Plan, the internal backend for an automotive flooring company. Units with a non-null 'reverse_on' field are considered reversed and should be excluded by default.\n\n"
                f"Today's date and time is {datetime.now(pytz.timezone('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Schema:\n{DFP_SCHEMA}\n\n"
                f"Here are some valid query examples:\n{DFP_FEWSHOT_EXAMPLES}\n\n"
                f"User request: {current_task}\nSQL query:"
            )

            llm_response = db_agent.llm.invoke(prompt)
            sql_query = llm_response.content.strip() if hasattr(llm_response, "content") else str(llm_response).strip()
            print(f"[DFP DB Node SQL Generated]: {sql_query}")

            if not sql_query.lower().startswith("select"):
                raise ValueError("Generated SQL does not appear valid or safe.")

            # Step 2: Run the query
            raw_result = db_tool.invoke(sql_query)
            break  # Exit loop on success

        except Exception as e:
            print(f"[DFP DB Node Error - Attempt {attempt+1}]: {e}")
            attempt += 1
            time.sleep(0.5)  # Small delay before retry

    if not raw_result:
        final_result = (
            "🤖 I'm not confident in how to query that. Try rephrasing or being more specific. "
            "You can ask about dealers and units in DFP."
        )
    else:
        # Step 3: Ask the LLM to contextualize the SQL result
        explain_prompt = (
            f"User request: {current_task}\n\n"
            f"SQL query executed:\n{sql_query}\n\n"
            f"Query result:\n{raw_result}\n\n"
            f"Please explain the result above in plain language.\n\n"
            f"Do not truncate the result of the query in your response. A user may need to see the entire result.\n\n"
            f"DFP stands for Direct Floor Plan, and is a backend software for our automotive flooring company. User requests may reference DFP.\n\n"
            f"Always show the SQL query executed in your response."
        )
        explanation_response = db_agent.llm.invoke(explain_prompt)
        final_result = explanation_response.content.strip() if hasattr(explanation_response, "content") else str(explanation_response).strip()

    print(f"[DFP DB Node Result]: {final_result}")

    new_queue = state["task_queue"][1:]  # Pop task

    return {
        **state,
        "task_queue": new_queue,
        "last_result": final_result,
        "next_agent": "",
        "done": not new_queue
    }
