import os

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("langfuse_public_key"),
    secret_key=os.getenv("langfuse_secret_key"),
    host=os.getenv("langfuse_host")
)

langfuse_config = None

try:
    langfuse.auth_check()
    print("Langfuse client is authenticated and ready!")
    langfuse_handler = CallbackHandler()
    langfuse_config = {"callbacks": [langfuse_handler]}
except:
    print("Authentication failed. Please check your credentials and host.")