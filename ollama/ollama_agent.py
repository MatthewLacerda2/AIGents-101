import os
from ollama import chat, ChatResponse
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

def main():
    messages = [
        {
            "role": "system",
            "content": (
                "You are a personal AI assistant running locally. "
                "You are given tools to help you with your tasks, use them when necessary. "
                "Your tools calls are listed as you call them, so you don't lose track of them. "
                "It is thus nice to add a 'plan' to your response, so you don't lose track of what's important. "
                "Such 'scratchpad' is added to your chat context as your turn's response."
            )
        }
    ]
    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")
    
    max_loop_limit = 16
    
    while True:
        user_input = input("\n📝 You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue
            
        messages.append({'role': 'user', 'content': user_input})
        
        for loop_counter in range(max_loop_limit):
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=messages,
                tools=[
                    fetch_website_text,
                    list_files,
                    read_files,
                    read_image_file,
                    create_file,
                    get_video_screenshot,
                    get_target_info
                ],
                think=True,
            )
            messages.append(response.message)
            
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
                        'content': str(result)
                    }
                    if function_name == 'read_image_file' and "Success" in str(result):
                        tool_message['images'] = [os.path.abspath(arguments['image_path'])]
                        
                    messages.append(tool_message)
            else:
                break
        else:
            print(f"\n[Warning] Reached the maximum loop limit of {max_loop_limit}.")

if __name__ == "__main__":
    main()