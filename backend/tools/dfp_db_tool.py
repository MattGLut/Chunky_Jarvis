# dfp_db_tool.py
import os
import pymysql
import pandas as pd

from dotenv import load_dotenv  # Optional: for local dev or Docker testing
load_dotenv()

class DFPDatabaseTool:
    name = "DFPDatabaseQuery"

    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")

        # Debug: confirm values loaded
        print(f"[DBTool] Connecting to {self.user}@{self.host}:{self.port}/{self.database}")
        missing = [v for v in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'] if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def invoke(self, query: str) -> str:
        try:
            with pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    if not rows:
                        return "Query returned no results."
                    df = pd.DataFrame(rows)
                    return df.to_markdown(index=False)
        except Exception as e:
            return f"Database query failed: {e}"