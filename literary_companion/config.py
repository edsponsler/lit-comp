# literary_companion/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists.
# This is useful for local development when not using gcenv.sh
load_dotenv()

# The default model to use for generative tasks.
# This is sourced from the DEFAULT_AGENT_MODEL environment variable.
# A fallback is provided for local development if the variable is not set.
DEFAULT_AGENT_MODEL = os.environ.get("DEFAULT_AGENT_MODEL", "gemini-1.5-flash")

# The GCS bucket for caching fun facts.
# This is sourced from the GCS_BUCKET_NAME environment variable.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

# The GCS file name for the prepared book.
# This is sourced from the GCS_FILE_NAME environment variable.
GCS_FILE_NAME = os.environ.get("GCS_FILE_NAME")

# Redis configuration for caching book data
# Sourced from environment variables with defaults for local setup.
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

