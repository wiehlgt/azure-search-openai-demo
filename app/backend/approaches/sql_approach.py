from typing import Any, cast

import pyodbc

from approaches.retrievethenread import RetrieveThenReadApproach
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam


def run_sql(sql: str) -> list[dict[str, Any]]:
    """Execute a SQL query against the claims database."""
    server   = 'text2sql.database.windows.net'
    database = 'claims'
    username = 'gtw22936'
    password = 'playingwiththeB0ys?'

    conn_str = f"""
        DRIVER={{ODBC Driver 18 for SQL Server}};
        SERVER={server},1433;
        DATABASE={database};
        UID={username};
        PWD={password};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
    """
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows

class SqlApproach(RetrieveThenReadApproach):
    """Simple approach that converts a natural language question into SQL."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(
        self,
        messages: list[ChatCompletionMessageParam],
        session_state: Any = None,
        context: dict[str, Any] = {},
    ) -> dict[str, Any]:
        overrides = context.get("overrides", {})
        auth_claims = context.get("auth_claims", {})
        use_agentic_retrieval = True if overrides.get("use_agentic_retrieval") else False
        q = messages[-1]["content"]
        if not isinstance(q, str):
            raise ValueError("The most recent message content must be a string.")

        if use_agentic_retrieval:
            extra_info = await self.run_agentic_retrieval_approach(messages, overrides, auth_claims)
        else:
            extra_info = await self.run_search_approach(messages, overrides, auth_claims)

        # Process results
        messages = self.prompt_manager.render_prompt(
            self.answer_prompt,
            self.get_system_prompt_variables(overrides.get("prompt_template"))
            | {"user_query": q, "text_sources": extra_info.data_points.text},
        )

        chat_completion = cast(
            ChatCompletion,
            await self.create_chat_completion(
                self.chatgpt_deployment,
                self.chatgpt_model,
                messages=messages,
                overrides=overrides,
                response_token_limit=self.get_response_token_limit(self.chatgpt_model, 1024),
            ),
        )
        extra_info.thoughts.append(
            self.format_thought_step_for_chatcompletion(
                title="Prompt to generate answer",
                messages=messages,
                overrides=overrides,
                model=self.chatgpt_model,
                deployment=self.chatgpt_deployment,
                usage=chat_completion.usage,
            )
        )
        print(chat_completion.choices[0].message.content)
        print(run_sql(chat_completion.choices[0].message.content))
        #print(run_sql(chat_completion.choices[0].message.content))
        return {
            "message": {
                "content": chat_completion.choices[0].message.content,
                "role": chat_completion.choices[0].message.role,
            },
            "context": extra_info,
            "session_state": session_state,
        }