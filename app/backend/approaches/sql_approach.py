from typing import Any

import pyodbc
from openai import AsyncOpenAI

from approaches.approach import Approach


class SqlApproach(Approach):
    """Simple approach that converts a natural language question into SQL."""

    def __init__(self, *, openai_client: AsyncOpenAI):
        self.openai_client = openai_client

    async def run(
        self, messages: list[dict[str, Any]], session_state: Any = None, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if context is None:
            context = {}
        q = messages[-1]["content"]
        sql_prompt = f"Translate to SQL:\n{q}"
        completion = await self.openai_client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[{"role": "user", "content": sql_prompt}],
        )
        sql = completion.choices[0].message.content.strip()
        rows = run_sql(sql)
        return {
            "message": {"role": "assistant", "content": f"Ran:\n{sql}"},
            "context": {"sql": sql, "rows": rows},
            "session_state": session_state,
        }


def run_sql(sql: str) -> list[dict[str, Any]]:
    """Execute a SQL query against the claims database."""
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:text2sql.database.windows.net,1433;"
        "Database=claims;"
        "Authentication=ActiveDirectoryInteractive;"
        "UID=gwhy500@gmail.com;"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows
