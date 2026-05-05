import asyncio
import re
import os
from typing import Any, List
from dotenv import load_dotenv

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from google.genai import Client
from google.genai.types import GenerateContentConfig, GenerateContentResponse

load_dotenv()

# --- Tools ---

async def execute_sql(sql_query: str, db: AsyncSession) -> str:
    """
    The actual execution logic for the SQL tool.
    Filters out write operations and runs the query.
    """
    try:
        # Regex to identify lines with write operations
        write_ops_pattern = r'(?i)\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b'
        
        # Filter the query line by line
        lines = sql_query.splitlines()
        safe_lines = [line for line in lines if not re.search(write_ops_pattern, line)]
        
        cleaned_query = "\n".join(safe_lines).strip()
        
        if not cleaned_query:
            return "Error: The provided query contained only forbidden operations or was empty."

        result = await db.execute(text(cleaned_query))
        
        if result.returns_rows:
            rows = result.fetchall()
            if not rows:
                return "Query returned no results."
            
            data = [dict(row._mapping) for row in rows]
            return str(data)
        else:
            return "Query executed successfully."
            
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

def sql_tool(sql_query: str) -> str:
    """
    Executes a SQL query to fetch information from the database. 
    Use this to answer questions.
    Only READ operations are allowed.
    """
    pass

async def execute_describe_db(db_name: str, db: AsyncSession) -> str:
    """
    Execution logic for describing the database schema.
    """
    try:
        # A generic query to list tables and columns in standard SQL databases
        # We try information_schema first as it is standard across Postgres, MySQL, etc.
        query = f"""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_catalog = '{db_name}' OR table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            # Fallback to a DESCRIBE query if information_schema is empty or not matching
            try:
                result = await db.execute(text(f"DESCRIBE {db_name}"))
                rows = result.fetchall()
            except Exception:
                pass
            
        if not rows:
            return "Could not retrieve schema information."
            
        data = [dict(row._mapping) for row in rows]
        return str(data)
    except Exception as e:
        return f"Error executing describe db: {str(e)}"

def describe_db_tool() -> str:
    """
    Describes the tables and schema of the connected database.
    Use this first to understand what data is available in the database.
    """
    pass

# --- Agent ---

async def gemini_agent(
    client: Client, messages: List[dict], tools: List[Any], model: str, system_instruction: str = None
) -> GenerateContentResponse:
    
    config = GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        temperature=0.5,
    )

    return await client.aio.models.generate_content(
        model=model, contents=messages, config=config
    )

# --- Prompt ---

def system_prompt(db_name: str) -> str:
    return f"""
<Context>
  You are an AI assistant that queries a SQL database to answer the user's questions.
  The user is connected to a database named: {db_name}.
</Context>

<Instructions>
  Give direct and clear answers.
  When the user asks a question, first use `describe_db_tool` to understand the database schema if needed.
  Then, formulate a query and use `sql_tool` to execute it.
  Present the final answer based on the data retrieved.
  Do not explain your thought process unless useful to help the user understand the answer.
  You may use markdown to format your text answers.
</Instructions>
"""

# --- Chat Loop ---

async def main():
    conn_string = input("Enter SQL connection string (e.g., sqlite+aiosqlite:///example.db, postgresql+asyncpg://user:pass@localhost/db): ")
    db_name = input("Enter database name: ")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API Key: ")
    client = Client(api_key=api_key)

    try:
        engine = create_async_engine(conn_string)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        return

    instruction = system_prompt(db_name)
    tools = [sql_tool, describe_db_tool]
    messages = []

    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")

    # Start the async session
    async with AsyncSession(engine) as db:
        while True:
            user_input = input("You: ")
            if user_input.strip().lower() == "/exit":
                break
            if not user_input.strip():
                continue
            
            messages.append({"role": "user", "parts": [{"text": user_input}]})
            
            LOOP_LIMIT = 8
            for i in range(LOOP_LIMIT):
                try:
                    response = await gemini_agent(
                        client,
                        messages, 
                        tools, 
                        "gemini-3.1-flash-lite-preview", 
                        system_instruction=instruction
                    )
                except Exception as e:
                    print(f"\n[Error querying Gemini]: {e}")
                    break
                    
                if response.text:
                    print(f"Assistant: {response.text}")
                    
                if not response.function_calls:
                    # No more tool calls, turn is over
                    break
                    
                messages.append({"role": "model", "parts": response.parts})
                
                tool_responses = []
                for tool_call in response.function_calls:
                    tool_name = tool_call.name
                    tool_args = tool_call.args
                    
                    if tool_name == "sql_tool":
                        print(f"[DEBUG] Executing SQL Query: {tool_args.get('sql_query')}")
                        result = await execute_sql(tool_args["sql_query"], db)
                        print(f"[DEBUG] SQL Result (truncated): {str(result)[:200]}...")
                    elif tool_name == "describe_db_tool":
                        print(f"[DEBUG] Executing Describe DB...")
                        result = await execute_describe_db(db_name, db)
                        print(f"[DEBUG] DB Describe Result (truncated): {str(result)[:200]}...")
                    else:
                        result = f"Error: Tool {tool_name} not found."
                    
                    tool_responses.append({
                        "function_response": {
                            "name": tool_name,
                            "response": {"result": result}
                        }
                    })
                    
                messages.append({"role": "user", "parts": tool_responses})

if __name__ == "__main__":
    asyncio.run(main())
