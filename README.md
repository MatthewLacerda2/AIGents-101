# AIGents-101
AI easy-usage examples

These are easy-win examples for:
- How to get response in a specific json format
- How to quickly group embeddings

# How to use

You do not need money or beefy GPU.

For Ollama, they have models on the Cloud and a generous free tier.
Download the app, settings -> signup/login.

For Gemini, they have a not-that-generous free tier. Serves as proof-of-concept.
Go to: https://aistudio.google.com/app/apikey and get one for free.
The daily limit for LLMs is short, but for embeddings you can run plenty a day.

*You can just take the code here and ask an AI to adapt for your use-case*

# How to run

Copy the .env.example to a .env and replace the values.

`python -m venv venv`

`source venv/Scripts/activate` (linux)
`venv\Scripts\activate` (windows)

`pip install -r requirements.txt`

Then run the scripts:
`python gemini/gemini_json.py`
`python ollama/ollama_json.py`
`python gemini/gemini_embeddings.py`
`python ollama/ollama_embeddings.py`

# Good practices

## Budget

If you have money for an AI model, you're better off with Gemini 3 models.

If you're on a budget, manage your usage smartly and stick to Ollama Cloud free tier.
Those Cloud models are way better than what you can get locally in a tight budget.

## AI models

Keep the request as simple as possible, they are more reliable this way:
- You must be able to read the prompt and write the json yourself easily!
- The responses must come less than 400 characters or they're too long
  - The only exception is using the AI as a search engine or write a neat text

Calling an AI model is a last resource!
- They are expensive
- Slow
- Not that smart
- A lotta code must be built for them in advance

You only resort to them when you can't do it otherwise!
If your pipeline is deterministic and not-subjective, *do not* use AI for that.

Do NOT use nested classes in your JSONs, it confuses the AI
  - You're better off doing two separate calls (e.g 'validation' 'assessment')

Your requests must give *precise, direct, clear* instructions.
You should ask for *concise, simple* responses and give a margin for error.

It's ok to send a longer prompt to be more clear.
Prompts should have between 80 and 1000 characters.
Do *NOT* give examples in your prompt unless you want the AI to answer in categories.
- They tend to answer in those examples

## Embeddings

When using Embeddings, you should first filter out the items as much as possible:
- Filter by date
- Filter by tags/keywords
- Filter by country/language
Then only consider results with >0.65 cosine similarity

Short texts leave very unreliable embeddings. I used them in the examples just as a proof-of-concept.

You can ask an AI to write a detailed description of something, and then embed it. Works fine.