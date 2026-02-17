import ollama
from pydantic import BaseModel

class CarDescription(BaseModel):
    name: str
    estimated_cost: int
    cost_of_maintenance: int
    summary: str

def ollama_car_advisor( prompt: str ) -> CarDescription:
    
    response = ollama.chat(
        model="gpt-oss:120b-cloud",
        think=False,
        stream=False,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format=CarDescription.model_json_schema()
    )
    
    print("-" * 20)
    print(response.message)
    print("-" * 20)

    json_response = response.message.content
    
    review = CarDescription.model_validate_json(json_response)
    return review

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
- name: string with the car's name
- estimated_cost: int with the car's starting price
- cost_of_maintenance: int grade from 0 to 100 of the car's monthly maintenance cost, with 100 being the cheapest
- summary: string with a short summary about the car. No more than 100 characters.
</Format>
"""

if __name__ == "__main__":
    car_name = input("\nEnter a car name to research: ").strip()
    
    print(f"\n🔍 Analyzing '{car_name}'... Please wait.\n")

    prompt = system_prompt.format(car_name=car_name)
    car = ollama_car_advisor(prompt)
        
    print(f"📌 Name:     {car.name}")
    print(f" Price:    ${car.estimated_cost:,}")
    print(f"🛠️  Maint:    {car.cost_of_maintenance}/100")
    print(f"\n📝 Summary:")
    print(f"   {car.summary}")
