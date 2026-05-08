import asyncio
import os
import sys
from typing import Any, List
from dotenv import load_dotenv
from google.genai import Client, types
from google.genai.types import GenerateContentConfig, GenerateContentResponse

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ollama")))
# pyrefly: ignore [missing-import]
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

available_functions = {
    'fetch_website_text': fetch_website_text,
    'list_files': list_files,
    'read_text_files': read_text_files,
    'read_image_file': read_image_file,
    'create_file': create_file,
    'create_text_file': create_text_file,
    'get_video_screenshot': get_video_screenshot,
    'get_target_info': get_target_info,
    'edit_text_files': edit_text_files,
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
        
        max_loop_limit = 16
        for loop_counter in range(max_loop_limit):
            try:

                custom_safety_settings = [
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
                response = await gemini_agent(
                    client,
                    messages, 
                    tools, 
                    "gemini-3.1-flash-lite-preview", 
                    system_instruction=instruction,
                    safety_settings=custom_safety_settings
                )
                
                usage = response.usage_metadata
                if usage:
                    print(f"\n📊 Tokens: {usage.total_token_count} (Input: {usage.prompt_token_count} | Output: {usage.candidates_token_count})")
                    
                if response.text:
                    print(f"\n🤖 Assistant: {response.text}\n")
                    
                messages.append({"role": "model", "parts": response.candidates[0].content.parts})
                
                if response.function_calls:
                    tool_parts = []
                    images_to_attach = []
                    
                    for tool_call in response.function_calls:
                        function_name = tool_call.name
                        arguments = tool_call.args
                        
                        print(f"\n{function_name} is being executed...")
                        
                        if function_name in available_functions:
                            try:
                                result = available_functions[function_name](**arguments)
                            except Exception as e:
                                result = f"Error executing tool: {str(e)}"
                        else:
                            result = f"Error: Tool {function_name} not found."
                            
                        function_response_part = types.Part.from_function_response(
                            name=function_name,
                            response={"result": str(result)}
                        )
                        tool_parts.append(function_response_part)
                        
                        if function_name == 'read_image_file' and "Success" in str(result):
                            image_paths = arguments.get('image_paths') or arguments.get('image_path') or []
                            if isinstance(image_paths, str):
                                image_paths = [image_paths]
                            for path in image_paths:
                                abs_path = os.path.abspath(path)
                                if f"Success: Loaded image from '{abs_path}'." in result:
                                    try:
                                        with open(abs_path, 'rb') as f:
                                            img_bytes = f.read()
                                        _, ext = os.path.splitext(abs_path)
                                        ext = ext.lower()
                                        mime_type = 'image/jpeg'
                                        if ext == '.png':
                                            mime_type = 'image/png'
                                        elif ext == '.bmp':
                                            mime_type = 'image/bmp'
                                        elif ext == '.webp':
                                            mime_type = 'image/webp'
                                            
                                        images_to_attach.append(types.Part.from_bytes(
                                            data=img_bytes,
                                            mime_type=mime_type,
                                        ))
                                    except Exception as e:
                                        print(f"Failed to load image bytes for {abs_path}: {e}")
                                        
                    messages.append({"role": "user", "parts": tool_parts})
                    
                    if images_to_attach:
                        messages.append({
                            "role": "user",
                            "parts": images_to_attach + [{"text": "Here are the images you requested to read."}]
                        })
                else:
                    break
                    
            except Exception as e:
                print(f"\n[Error querying Gemini]: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
