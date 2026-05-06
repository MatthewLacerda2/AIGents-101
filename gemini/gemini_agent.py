import asyncio
import os
import sys
from typing import Any, List
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig, GenerateContentResponse

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ollama")))
from ollama_tools import (
    fetch_website_text,
    list_files,
    read_text_files,
    read_image_file,
    create_file,
    create_text_file,
    get_video_screenshot,
    get_target_info,
    edit_text_files
)

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
        read_text_files,
        read_image_file,
        create_file,
        create_text_file,
        get_video_screenshot,
        get_target_info,
        edit_text_files
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
        
        try:
            response = await gemini_agent(
                client,
                messages, 
                tools, 
                "gemini-3.1-flash-lite-preview", 
                system_instruction=instruction
            )
            
            usage = response.usage_metadata
            if usage:
                print(f"\n📊 Tokens: {usage.total_token_count} (Input: {usage.prompt_token_count} | Output: {usage.candidates_token_count})")
                
            if response.text:
                print(f"\n🤖 Assistant: {response.text}\n")
                
            messages.append({"role": "model", "parts": response.candidates[0].content.parts})
                
        except Exception as e:
            print(f"\n[Error querying Gemini]: {e}")

if __name__ == "__main__":
    asyncio.run(main())
