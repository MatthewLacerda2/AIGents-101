# AIGents-101
AI easy-usage examples

These are easy-win examples for:
- How to quickly cluster embeddings
- How to get response in a specific json format
- How to get an AI agent that reads and changes your files

# How to use

You do not need money or beefy GPU.

For Ollama, they have models on the Cloud and a generous free tier.
Download the app, settings -> signup/login.

For Gemini, they have a not-that-generous free tier. Serves as proof-of-concept.
Go to: https://aistudio.google.com/app/apikey and get one for free.
The daily limit for LLMs is short, but for embeddings you can run plenty a day.

*You can just take the code here for yourself and be ready for production*

# How to run

Copy the .env.example to a .env and replace the values.

`python -m venv venv`
`requirements.txt`

Then run the script you wish.

Read the files to understand it well. It's of easy reproduction.

# Good practices

## Budget

If you're on a budget, manage your usage smartly and stick to Ollama Cloud free tier.

If you have money for an AI model, you're better off with Gemini 3.0 models.

*Why i don't recommend a local model?* To run a local model as good as gpt-oss:120b or deepseek-r1:671b, you need a beefy GPU, thus you need money for one, and if you had money for one you're better off...

## AI

Keep the responses as simple as possible, they are more reliable this way:
- Read the prompt, read the json format. If you can answer it easily, than it's good

Do NOT use pydantic Field annotations, Gemini wasn't compatible last i saw
Do NOT use nested classes in your JSONs, it confuses the AI
  - You're better off doing two separate calls (e.g 'validation' 'assessment')

Calling an AI model is the last resource. You only call it when you can't do it otherwise.
Usually a content generator or when you need to format a subjective stuff.
Embeddings should be combined with something else to give. e.g filter documents by _start_date_ and _end_date_ and _keyword_ and only vector search the remaining ones.