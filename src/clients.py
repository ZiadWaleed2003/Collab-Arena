import openai
import os
from dotenv import load_dotenv

def get_llm_client():
    
    load_dotenv()

    """"a simple function returning an OpenAI client"""

    # Option 1: Cerebras (Fast inference, free tier available)
    client = openai.OpenAI(
        base_url="https://api.cerebras.ai/v1",
        api_key=os.getenv("CEREBRAS_API_KEY")
    )

    # Option 2: OpenRouter (Multiple models, some free)
    # client = openai.OpenAI(
    #     base_url="https://openrouter.ai/api/v1",
    #     api_key=os.getenv("OPENROUTER_API_KEY")
    # )

    # Option 3: OpenAI (Paid but reliable)
    # client = openai.OpenAI(
    #     api_key=os.getenv("OPENAI_API_KEY")
    # )

    # Option 4: Ollama (Free Local Models)
    # client = openai.OpenAI(
    #     base_url="http://localhost:11434/v1", 
    #     api_key="ollama"  # Ollama doesn't need real API key
    # )

    return client


def get_llm():

    """Just a simple function returning the name of the used LLM"""

    # Option 1: Cerebras models (fast inference)
    model = "llama3.1-8b"  # Try the 8B model first
    
    # Option 2: OpenAI models (paid)
    # model = "gpt-3.5-turbo"  # Cheaper option, or "gpt-4" for better quality
    
    # Option 3: Ollama models (free)
    # model = "llama3.2"  # or "qwen2.5", "phi3", "mistral"

    return model