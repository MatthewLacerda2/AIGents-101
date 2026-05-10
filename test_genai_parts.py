import asyncio
import os
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig

load_dotenv()

def list_files(directory: str):
    """Lists files in a directory."""
    pass

async def main():
    client = Client(api_key=os.getenv("GEMINI_API_KEY"))
    messages = [{"role": "user", "parts": [{"text": "Please use the list_files tool on the '/my/test/dir' directory."}]}]
    
    response = await client.aio.models.generate_content(
        contents=messages,
        model="gemini-3.1-flash-lite-preview",
        config=GenerateContentConfig(
            tools=[list_files]
        )
    )
    
    parts = response.candidates[0].content.parts
    print("Parts count:", len(parts))
    for i, part in enumerate(parts):
        print(f"\nPart {i}:")
        print(f"  text: {getattr(part, 'text', None) is not None}")
        print(f"  function_call: {getattr(part, 'function_call', None) is not None}")
        print(f"  thought: {getattr(part, 'thought', None) is not None}")
        print("  Attributes:", dir(part))

if __name__ == "__main__":
    asyncio.run(main())
