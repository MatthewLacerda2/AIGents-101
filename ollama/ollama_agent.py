import os
import requests
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


available_functions = {
  'fetch_website_text': fetch_website_text,
  'list_files': list_files,
}

def main():
    messages = []
    print("\nChatbot initialized. Type your message below, or '/exit' to quit.\n")
    
    max_loop_limit = 8
    
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue
            
        messages.append({'role': 'user', 'content': user_input})
        
        loop_counter = 0
        while loop_counter < max_loop_limit:
            loop_counter += 1
            
            response: ChatResponse = chat(
                model='gemma4:e4b',
                messages=messages,
                tools=[fetch_website_text, list_files],
                think=True,
            )
            messages.append(response.message)
            
            if hasattr(response.message, 'thinking') and response.message.thinking:
                print(f"Thinking: {response.message.thinking}")
            
            if response.message.content:
                print(f"Assistant: {response.message.content}")

            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if tc.function.name in available_functions:
                        print(f"\n{tc.function.name} is being executed...")
                        result = available_functions[tc.function.name](**tc.function.arguments)
                        
                        # add the tool result to the messages
                        messages.append({
                            'role': 'tool', 
                            'name': tc.function.name, 
                            'content': str(result)
                        })
            else:
                # end the loop when there are no more tool calls
                break
        
        if loop_counter >= max_loop_limit:
            print(f"\n[Warning] Reached the maximum loop limit of {max_loop_limit}.")

if __name__ == "__main__":
    main()