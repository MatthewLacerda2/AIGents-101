from pydantic import BaseModel
from google.genai.types import GenerateContentResponse
from gemini_client import get_client, get_gemini_config

class CarDescription(BaseModel):
    name: str
    models: list[str]
    estimated_cost: int
    cost_of_maintenance: int
    summary: str

def gemini_car_advisor( prompt: str ) -> CarDescription:

    client = get_client()
    model = "gemini-2.5-flash-lite"
    
    #model_json_schema() is how you tell the model the response format you want
    config = get_gemini_config(CarDescription.model_json_schema())

    response: GenerateContentResponse = client.models.generate_content(
        model=model, contents=prompt, config=config
    )

    #print("Total tokens:", response.usage_metadata.total_token_count)
    #print("Total tokens:", response.usage_metadata.prompt_token_count)
    #print("Total tokens:", response.usage_metadata.candidates_token_count)
    json_response = response.text

    #This is how you take the response and parse it to your format
    return CarDescription.model_validate_json(json_response)

system_prompt = """
<Context>
The user wants the information about the {car_name} car.
</Context>

<Task>
You must output a response with what you know about the car.
</Task>

<Guideline>
If you cannot be exact, give your best guess.
Be direct and concise.
</Guideline>

<Format>
You must output a json:
- Name: string with the car's name
- Models: list of strings with the car's models
- Estimated cost: int with the car's starting price
- Cost of maintenance: int grade from 0 to 100 of the car's monthly maintenance cost, with 100 being the cheapest
- Summary: string with a short summary about the car. No more than 100 characters.
</Format>
"""

if __name__ == "__main__":
    car_name = input("\nEnter a car name to research: ").strip()
    
    print(f"\n🔍 Analyzing '{car_name}'... Please wait.\n")

    prompt = system_prompt.format(car_name=car_name)
    car = gemini_car_advisor(prompt)
        
    print(f"📌 Name:     {car.name}")
    print(f"🚙 Models:   {', '.join(car.models)}")
    print(f"💰 Price:    ${car.estimated_cost:,}")
    print(f"🛠️  Maint:    {car.cost_of_maintenance}/100")
    print(f"\n📝 Summary:")
    print(f"   {car.summary}")
    