from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig
from ollama_tools import *

load_dotenv()

@dataclass
class ToolCallData:
    id: str
    name: str
    args: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None

@dataclass
class AgentResponseData:
    text: str
    tool_calls: List[ToolCallData]
    thoughts: str

def extract_response_data(parts, afc_history=None) -> AgentResponseData:
    text_segments = []
    tool_calls: List[ToolCallData] = []
    thoughts = []

    # 1. Process final response parts
    for part in parts:
        if part.text:
            text_segments.append(part.text)
        
        # If AFC is disabled, tool calls might be here
        if part.function_call:
            args = part.function_call.args
            if hasattr(args, "items"):
                args = {k: v for k, v in args.items()}
            tool_calls.append(ToolCallData(
                id=part.function_call.id,
                name=part.function_call.name,
                args=args
            ))
            
        if part.thought:
            thoughts.append(str(part.thought) + "\n")
        elif part.thought_signature:
            thoughts.append(str(part.thought_signature) + "\n")

    # 2. Process Automatic Function Calling history (if it exists)
    if afc_history:
        for history_content in afc_history:
            for part in history_content.parts:
                
                # A. The Model decides to call a tool
                if history_content.role == "model":
                    if part.function_call:
                        args = part.function_call.args
                        if hasattr(args, "items"):
                            args = {k: v for k, v in args.items()}
                        tool_calls.append(ToolCallData(
                            id=part.function_call.id,
                            name=part.function_call.name,
                            args=args
                        ))
                    
                    if part.thought:
                        thoughts.append(str(part.thought) + "\n")
                    elif part.thought_signature:
                        thoughts.append(str(part.thought_signature) + "\n")
                        
                # B. The SDK (User) returns the tool response
                elif history_content.role == "user":
                    if part.function_response:
                        # Find the last tool call with matching name that lacks a response
                        for tc in reversed(tool_calls):
                            if tc.name == part.function_response.name and tc.response is None:
                                tc.response = part.function_response.response
                                break

    return AgentResponseData(
        text="".join(text_segments),
        tool_calls=tool_calls,
        thoughts="".join(thoughts)
    )

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
        extracted_data = extract_response_data(parts, afc_history)

        if extracted_data.text:
            print(f"\n🤖 Assistant: {extracted_data.text}\n")

        # Crucial: Append the original parts to maintain tool call context
        messages.append({"role": "model", "parts": parts})
        
        return extracted_data

    except Exception as e:
        print(f"\n[Error querying Gemini]: {e}")
        return AgentResponseData(text="", tool_calls=[], thoughts="")