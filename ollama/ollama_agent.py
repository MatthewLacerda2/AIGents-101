import os
from ollama import chat, ChatResponse
from ollama_tools import (
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
    'bash': bash,
}

def main():
    system_msg = {
        "role": "system",
        "content": (
            "You are a personal AI assistant running locally. "
            "You are given tools to help you with your tasks, use them if and when necessary. "
            "You can read files in chunks and make edits to specific line chunks of code using edit_text_files. "
            "You can run terminal commands or shell scripts using the bash tool."
        )
    }
    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")
    print("For performance reasons, the chat only keeps context of the latest 3 prompts and responses\n")
    
    max_loop_limit = 16
    turns = []
    
    while True:
        user_input = input("\n📝 You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue
            
        current_turn_messages = [{'role': 'user', 'content': user_input}]
        
        for loop_counter in range(max_loop_limit):
            active_messages = [system_msg]
            for turn in turns[-2:]:
                active_messages.extend(turn)
            active_messages.extend(current_turn_messages)
            
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=active_messages,
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
                ],
                think=True,
            )
            current_turn_messages.append(response.message)
            
            has_thought = False
            if hasattr(response.message, 'thinking') and response.message.thinking:
                raw_thinking = response.message.thinking
                short_thinking = (raw_thinking[:128] + "...") if len(raw_thinking) > 128 else raw_thinking
                print(f"\n🧠 Thinking: {short_thinking}")
                has_thought = True
            
            if response.message.content:
                lead = "" if has_thought else "\n"
                print(f"{lead}🤖 Assistant: {response.message.content}\n")

            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    function_name = tc.function.name
                    arguments = tc.function.arguments
                    
                    print(f"\n{function_name} is being executed...")
                    
                    if function_name in available_functions:
                        try:
                            result = available_functions[function_name](**arguments)
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                    else:
                        result = f"Error: Tool {function_name} not found."
                        
                    tool_message = {
                        'role': 'tool', 
                        'name': function_name, 
                        'arguments': arguments,
                        'content': f"Arguments passed: {arguments}\nResult: {result}"
                    }
                    current_turn_messages.append(tool_message)

                    if function_name == 'read_image_file' and "Success" in str(result):
                        image_paths = arguments.get('image_paths') or arguments.get('image_path') or []
                        if isinstance(image_paths, str):
                            image_paths = [image_paths]
                        loaded_images = []
                        for path in image_paths:
                            abs_path = os.path.abspath(path)
                            if f"Success: Loaded image from '{abs_path}'." in result:
                                loaded_images.append(abs_path)
                        if loaded_images:
                            current_turn_messages.append({
                                'role': 'user',
                                'content': 'Here are the images you requested to read.',
                                'images': loaded_images
                            })
            else:
                break
        else:
            print(f"\n[Warning] Reached the maximum loop limit of {max_loop_limit}.")
            
        turns.append(current_turn_messages)

if __name__ == "__main__":
    main()