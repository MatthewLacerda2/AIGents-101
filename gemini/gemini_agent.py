import asyncio
import os
import sys
from typing import Any, List
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig, GenerateContentResponse

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ollama")))
from ollama_tools import (
    fetch_website_text,
    list_files,
    read_files,
    read_image_file,
    create_file,
    get_video_screenshot,
    get_target_info
)

available_functions = {
    'fetch_website_text': fetch_website_text,
    'list_files': list_files,
    'read_files': read_files,
    'read_image_file': read_image_file,
    'create_file': create_file,
    'get_video_screenshot': get_video_screenshot,
    'get_target_info': get_target_info,
}

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

def system_prompt() -> str:
    return (
        "You are a personal AI assistant running locally. "
        "You are given tools to help you with your tasks, use them when necessary. "
        "Your tools calls are listed as you call them, so you don't lose track of them. "
        "It is thus nice to add a 'plan' to your response, so you don't lose track of what's important. "
        "Such 'scratchpad' is added to your chat context as your turn's response."
    )

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API Key: ")
    client = Client(api_key=api_key)

    instruction = system_prompt()
    tools = [
        fetch_website_text,
        list_files,
        read_files,
        read_image_file,
        create_file,
        get_video_screenshot,
        get_target_info
    ]
    messages = []

    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")

    while True:
        user_input = input("\n📝 You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue
            
        messages.append({"role": "user", "parts": [{"text": user_input}]})
        
        LOOP_LIMIT = 16
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
                print(f"\n🤖 Assistant: {response.text}\n")
                
            if not response.function_calls:
                break
                
            messages.append({"role": "model", "parts": response.parts})
            
            tool_responses = []
            for tool_call in response.function_calls:
                tool_name = tool_call.name
                tool_args = tool_call.args
                
                print(f"\n{tool_name} is being executed...")
                
                if tool_name in available_functions:
                    try:
                        result = available_functions[tool_name](**tool_args)
                    except Exception as e:
                        result = f"Error executing tool: {str(e)}"
                else:
                    result = f"Error: Tool {tool_name} not found."
                
                tool_responses.append({
                    "function_response": {
                        "name": tool_name,
                        "response": {"result": str(result)}
                    }
                })
                
            messages.append({"role": "user", "parts": tool_responses})

if __name__ == "__main__":
    asyncio.run(main())
