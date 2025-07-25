import os
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

INDEX_NAME = "notes-v9"
INDEX_NAMESPACE = "default"
TRACKED_FILE = f"pinecone_tracked_files_{INDEX_NAME}.txt"

IN_CI = os.getenv("GITHUB_ACTIONS") is not None

# Define ANSI escape codes
CYAN = "\033[96m"
GREEN = "\033[92m"
GREY = "\033[90m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"
