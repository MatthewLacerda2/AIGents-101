import os
import requests
from typing import List
from bs4 import BeautifulSoup
from ollama import chat, ChatResponse

def fetch_website_text(url: str) -> str:
  """Visits a website URL and extracts the raw text content without HTML tags"""
  """
  Args:
    url: The full URL to visit (e.g., https://example.com)

  Returns:
    The raw text content of the website
  """
  try:
      headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
      response = requests.get(url, headers=headers, timeout=10)
      response.raise_for_status()
      soup = BeautifulSoup(response.content, 'html.parser')
      # Remove script and style elements
      for script in soup(["script", "style"]):
          script.extract()
      # Get text and clean it up
      text = soup.get_text(separator=' ', strip=True)
      return text
  except Exception as e:
      return f"Error fetching website: {e}"


def list_files(directory: str) -> str:
  """Lists all files and directories within a specified folder path"""
  """
  Args:
    directory: The path to the directory (e.g., /home/user or ./)

  Returns:
    A string containing a list of all files in the directory
  """
  try:
      files = os.listdir(directory)
      if not files:
          return f"The directory '{directory}' is empty."
      return "\n".join(files)
  except Exception as e:
      return f"Error listing directory '{directory}': {e}"


def read_files(file_paths: List[str]) -> str:
  """Reads the contents of multiple files (supports only .py, .ts, .tsx, .md, .txt) and returns their contents.

  Args:
    file_paths: A list of file paths to read.

  Returns:
    The contents of the requested files.
  """
  allowed_extensions = {'.py', '.ts', '.tsx', '.md', '.txt'}
  results = []
  
  for path in file_paths:
      _, ext = os.path.splitext(path)
      if ext.lower() not in allowed_extensions:
          results.append(f"--- File: {path} ---\nError: Reading this file extension is not allowed. Only .py, .ts, .tsx, .md, and .txt are permitted.")
          continue
          
      try:
          with open(path, 'r', encoding='utf-8', errors='ignore') as f:
              content = f.read()
          results.append(f"--- File: {path} ---\n{content}")
      except Exception as e:
          results.append(f"--- File: {path} ---\nError reading file: {e}")
          
  return "\n\n".join(results)


available_functions = {
  'fetch_website_text': fetch_website_text,
  'list_files': list_files,
  'read_files': read_files,
}

def main():
    # Dedicated system prompt to anchor model behavior
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Use the tools provided when necessary."}
    ]
    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")
    
    max_loop_limit = 8
    
    while True:
        user_input = input("\n📝 You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue
            
        messages.append({'role': 'user', 'content': user_input})
        
        # Pythonic agentic loop using range and for...else
        for loop_counter in range(max_loop_limit):
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=messages,
                tools=[fetch_website_text, list_files, read_files],
                think=True,
            )
            messages.append(response.message)
            
            if hasattr(response.message, 'thinking') and response.message.thinking:
                raw_thinking = response.message.thinking
                short_thinking = (raw_thinking[:128] + "...") if len(raw_thinking) > 128 else raw_thinking
                print(f"\n🧠 Thinking: {short_thinking}\n")
            
            if response.message.content:
                print(f"\n🤖 Assistant: {response.message.content}\n")

            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    function_name = tc.function.name
                    arguments = tc.function.arguments
                    
                    print(f"\n{function_name} is being executed...")
                    
                    # Robust inline tool execution error handling
                    if function_name in available_functions:
                        try:
                            result = available_functions[function_name](**arguments)
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                    else:
                        result = f"Error: Tool {function_name} not found."
                        
                    # add the tool result to the messages
                    messages.append({
                        'role': 'tool', 
                        'name': function_name, 
                        'content': str(result)
                    })
            else:
                # end the loop when there are no more tool calls
                break
        else:
            # Triggered if loop completed without breaking (max loop limit reached)
            print(f"\n[Warning] Reached the maximum loop limit of {max_loop_limit}.")

if __name__ == "__main__":
    main()