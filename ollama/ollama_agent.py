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


def read_image_file(image_path: str) -> str:
  """Loads an image from the specified path to be processed by the model.

  Args:
    image_path: The filesystem path to the image file.

  Returns:
    A success message if the file exists, otherwise an error.
  """
  if not os.path.exists(image_path):
      return f"Error: Image file not found at '{image_path}'."
  return f"Success: Loaded image from '{image_path}'."


def create_file(name: str, extension: str, content: str) -> str:
  """Creates a new file with the specified name, extension, and content.

  This tool only supports creating files with the following extensions: .py, .ts, .md, and .txt.

  Args:
    name: The base name of the file to create (e.g., 'hello' or 'notes').
    extension: The file extension, including the dot (e.g., '.py', '.ts', '.md', '.txt').
    content: The string content to write into the new file.

  Returns:
    A success confirmation message, or an error description.
  """
  allowed_extensions = {'.py', '.ts', '.md', '.txt'}
  
  # Normalize extension formatting
  ext = extension.strip().lower()
  if not ext.startswith('.'):
      ext = '.' + ext
      
  if ext not in allowed_extensions:
      return f"Error: Extension '{extension}' is not permitted. Only .py, .ts, .md, and .txt files are allowed."
      
  # Form the full filename safely
  filename = name.strip()
  if not filename.endswith(ext):
      filename += ext
      
  try:
      with open(filename, 'w', encoding='utf-8') as f:
          f.write(content)
      return f"Success: File '{filename}' was successfully created."
  except Exception as e:
      return f"Error creating file '{filename}': {e}"


available_functions = {
  'fetch_website_text': fetch_website_text,
  'list_files': list_files,
  'read_files': read_files,
  'read_image_file': read_image_file,
  'create_file': create_file,
}

def main():
    # Dedicated system prompt to anchor model behavior
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
        
        # Pythonic agentic loop using range and for...else
        for loop_counter in range(max_loop_limit):
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=messages,
                tools=[fetch_website_text, list_files, read_files, read_image_file, create_file],
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
                    
                    # Robust inline tool execution error handling
                    if function_name in available_functions:
                        try:
                            result = available_functions[function_name](**arguments)
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                    else:
                        result = f"Error: Tool {function_name} not found."
                        
                    # add the tool result to the messages
                    tool_message = {
                        'role': 'tool', 
                        'name': function_name, 
                        'content': str(result)
                    }
                    # If reading an image was successful, append the image path to the next ollama call context
                    if function_name == 'read_image_file' and "Success" in str(result):
                        tool_message['images'] = [arguments['image_path']]
                        
                    messages.append(tool_message)
            else:
                # end the loop when there are no more tool calls
                break
        else:
            # Triggered if loop completed without breaking (max loop limit reached)
            print(f"\n[Warning] Reached the maximum loop limit of {max_loop_limit}.")

if __name__ == "__main__":
    main()