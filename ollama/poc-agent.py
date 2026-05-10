import os
import asyncio
from dotenv import load_dotenv
from google.genai import Client
from backend_agent import gemini_agent

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API Key: ")
    client = Client(api_key=api_key)

    messages = []
    print("\n=== STAGER AGENT EXTRACTION TEST ===")
    print("Type your message below, or '/exit' to quit.")
    print("Hint: Ask it to describe the scene or create a chair to trigger tools!\n")

    while True:
        user_input = input("\n📝 You: ")
        if user_input.strip().lower() == "/exit":
            break
        if not user_input.strip():
            continue

        # Add user message to history
        messages.append({"role": "user", "parts": [{"text": user_input}]})

        extracted_data = await gemini_agent(messages, client)
        
        print("\n" + "="*40)
        print("         DATA SEPARATION PROOF         ")
        print("="*40)
        
        # 1. Thoughts
        if extracted_data.thoughts:
            print(f"\n🧠 THOUGHT SIGNATURE:\n{extracted_data.thoughts}")
        else:
            print("\n🧠 THOUGHT SIGNATURE: None")
            
        # 2. Tools
        if extracted_data.tool_calls:
            print("\n🛠️ TOOLS REQUESTED:")
            for idx, tool in enumerate(extracted_data.tool_calls):
                print(f"  [{idx + 1}] {tool.name} (id: {tool.id})")
                print(f"      Args: {tool.args}")
                if tool.response:
                    print(f"      Response: {tool.response}")
        else:
            print("\n🛠️ TOOLS REQUESTED: None")
            
        # 3. Text
        print(f"\n🗣️ TEXT RESPONSE:\n{extracted_data.text if extracted_data.text else 'No text response generated.'}")
        print("="*40)

if __name__ == "__main__":
    asyncio.run(main())