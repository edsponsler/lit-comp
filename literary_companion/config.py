# literary_companion/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists.
# This is useful for local development when not using gcenv.sh
load_dotenv()

# The default model to use for generative tasks.
# This is sourced from the DEFAULT_AGENT_MODEL environment variable.
# A fallback is provided for local development if the variable is not set.
DEFAULT_AGENT_MODEL = os.environ.get("DEFAULT_AGENT_MODEL", "gemini-2.5-flash")