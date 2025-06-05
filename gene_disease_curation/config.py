import os
import getpass

def setup_environment():
    """Set up environment variables for LangChain and LangSmith"""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    
    # only prompt for API key if not already set
    if "LANGCHAIN_API_KEY" not in os.environ:
        os.environ["LANGCHAIN_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
    
    os.environ["LANGCHAIN_PROJECT"] = "gene-disease-curation"

# Configuration settings
SETTINGS = {
    "batch_size": 5,
    "max_abstracts": 30,
    "llm_model": "gpt-4o-mini",
    "llm_temperature": 0,
    "max_abstract_length": 1500
}