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
`requirements.txt`

Then run the script you wish.

Read the files to understand it well. It's of easy reproduction.

# Good practices

## Budget

If you have money for an AI model, you're better off with Gemini 3 models.

If you're on a budget, manage your usage smartly and stick to Ollama Cloud free tier.
Those Cloud models are way better than what you can get locally in a tight budget.

## AI

Keep the request as simple as possible, they are more reliable this way:
- Your request is only good if you can read the prompt and write the json yourself easily

Do NOT use pydantic Field annotations, Gemini wasn't compatible last i saw
Do NOT use nested classes in your JSONs, it confuses the AI
  - You're better off doing two separate calls (e.g 'validation' 'assessment')

Calling an AI model is a last resource.
- They are expensive
- Slow
- Not that smart

You only call it when you can't do it otherwise.

When using Embeddings, you should first filter out the items as much as possible:
- Filter by date
- Filter by tags/keywords
- Filter by country/language
Then only consider results with >0.65 cosine similarity