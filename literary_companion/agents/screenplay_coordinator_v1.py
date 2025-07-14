# In literary_companion/agents/screenplay_coordinator_v1.py
# (Modify your existing agent definition)

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from literary_companion.tools import screenplay_generator_tool
from literary_companion.config import DEFAULT_AGENT_MODEL

# Expose both functions as tools for the agent with EXPLICIT descriptions.
beat_sheet_tool = FunctionTool(
    func=screenplay_generator_tool.create_beat_sheet
)

scene_list_tool = FunctionTool(
    func=screenplay_generator_tool.generate_scene_list
)

SCREENPLAY_COORDINATOR_V1_INSTRUCTIONS = """
You are a screenplay production assistant.
Your goal is to manage the process of converting a novel into a screenplay.
You will use the provided tools to execute each step of the conversion process.
Carefully read the user's prompt to determine which tool is appropriate.
- Use the `create_beat_sheet` tool for high-level outlines of the whole novel.
- Use the `generate_scene_list` tool for detailed scene breakdowns of specific chapters.
"""

screenplay_coordinator = Agent(
    name="ScreenplayCoordinator_v1",
    model=DEFAULT_AGENT_MODEL,
    description="Manages the generation of screenplay components from a prepared novel.",
    instruction=SCREENPLAY_COORDINATOR_V1_INSTRUCTIONS,
    tools=[beat_sheet_tool, scene_list_tool]
)