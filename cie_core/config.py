# --- Central Model Configuration for CIE ---

# The primary model for agents requiring advanced reasoning, planning, and orchestration.
DEFAULT_AGENT_MODEL = "gemini-2.5-pro-preview-05-06"

# A faster, more cost-effective model suitable for simpler, more constrained tasks.
# We used this in the original tutorial for the specialists.
FLASH_AGENT_MODEL = "gemini-2.0-flash"

# You can add other model configurations here as needed in the future.
# For example:
# NEXT_GEN_MODEL = "gemini-3.0-unannounced-preview"