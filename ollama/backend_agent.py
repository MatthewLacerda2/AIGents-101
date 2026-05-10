from typing import List
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig
from ollama_tools import *

load_dotenv()


def extract_response_data(parts, afc_history=None) -> tuple[str, list, str]:
    text_segments = []
    tool_calls = []
    thoughts = []

    for part in parts:
        if getattr(part, "text", None):
            text_segments.append(part.text)
        
        # If AFC is disabled, tool calls might be here
        if getattr(part, "function_call", None):
            args = part.function_call.args
            if hasattr(args, "items"):
                args = {k: v for k, v in args.items()}
            tool_calls.append({
                "name": part.function_call.name,
                "args": args
            })
            
        if getattr(part, "thought", None):
            thoughts.append(str(part.thought))
        elif getattr(part, "thought_signature", None):
            thoughts.append(str(part.thought_signature))

    # Extract tool calls from AFC history if it exists
    if afc_history:
        for history_content in afc_history:
            if getattr(history_content, "role", None) == "model" and hasattr(history_content, "parts"):
                for part in history_content.parts:
                    if getattr(part, "function_call", None):
                        args = part.function_call.args
                        if hasattr(args, "items"):
                            args = {k: v for k, v in args.items()}
                        tool_calls.append({
                            "name": part.function_call.name,
                            "args": args
                        })
                    
                    if getattr(part, "thought", None):
                        thoughts.append(str(part.thought) + "\n")
                    elif getattr(part, "thought_signature", None):
                        thoughts.append(str(part.thought_signature) + "\n")

    return "".join(text_segments), tool_calls, "".join(thoughts)

async def gemini_agent(messages: List[dict], client: Client):
    try:
        response = await client.aio.models.generate_content(
            contents=messages,
            model="gemini-3.1-flash-lite-preview",
            config=GenerateContentConfig(
                system_instruction=(
                    "You are a helpful AI assistant. You have access to various tools to interact "
                    "with the filesystem, terminal, and web. When a user asks you to list files, read files, "
                    "or perform actions, you MUST use the corresponding tools instead of guessing or answering directly."
                ),
                tools=[
                    fetch_website_text,
                    list_files,
                    read_text_files,
                    read_image_file,
                    create_file,
                    create_text_file,
                    get_video_screenshot,
                    get_target_info,
                    edit_text_files,
                    bash
                ]
            )
        )

        # Dump the full response to JSON for inspection
        try:
            with open("response_dump.json", "w", encoding="utf-8") as f:
                f.write(response.model_dump_json(indent=2))
        except Exception as dump_err:
            print(f"[Warning] Could not dump response: {dump_err}")

        usage = response.usage_metadata
        if usage:
            print(f"\n📊 Tokens: {usage.total_token_count} (Input: {usage.prompt_token_count} | Output: {usage.candidates_token_count})")

        parts = response.candidates[0].content.parts
        afc_history = getattr(response, "automatic_function_calling_history", None)
        text_response, extracted_tools, thoughts = extract_response_data(parts, afc_history)

        if text_response:
            print(f"\n🤖 Assistant: {text_response}\n")

        # Crucial: Append the original parts to maintain tool call context
        messages.append({"role": "model", "parts": parts})
        
        return text_response, extracted_tools, thoughts

    except Exception as e:
        print(f"\n[Error querying Gemini]: {e}")
        return "", [], ""