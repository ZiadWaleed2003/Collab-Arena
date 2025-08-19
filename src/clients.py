import openai
import os
from dotenv import load_dotenv
from tavily import TavilyClient

def get_llm_client():
    
    load_dotenv()

    """"a simple function returning an OpenAI client"""

    client = openai.OpenAI(
        base_url="https://integrate.api.nvidia.com/v1", 
        api_key=os.getenv("NVIDIA_API_KEY") 
    )
    return client


def get_llm():

    """Just a simple function returnign the name of the used LLM"""

    model = "qwen/qwen3-235b-a22b"

    return model

def get_search_client() -> TavilyClient:
    """Initializes and returns a shared TavilyClient instance."""
    load_dotenv()
    print("--- Initializing Tavily Client ---")
    api_key = os.getenv('TAVILY_API_KEY')
    return TavilyClient(api_key=api_key)