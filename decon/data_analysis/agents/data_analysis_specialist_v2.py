# decon/data_analysis/agents/data_analysis_specialist_v2.py

from google.adk.agents import Agent
from cie_core.config import DEFAULT_AGENT_MODEL
from decon.data_analysis.orchestrator import run_data_analysis_agency
from decon.data_analysis.tools.micro_task_board_tool import post_micro_entry
import json

# This instruction aligns the agent with the Coordinator's expectations.
DATA_ANALYSIS_V2_INSTRUCTION = """
You are a Data Analysis Specialist who uses a reliable Python orchestrator.
Your task is to process retrieved textual information and extract key insights.
You will receive the text to analyze, a `session_id`, and a `task_id`.

Your steps are:
1.  Acknowledge the task. Immediately use the `post_micro_entry` tool to update your status on the task board to 'processing_analysis_request'. You MUST use the `session_id` and `task_id` you were given.
2.  Internally, run the `run_data_analysis_agency` orchestrator on the provided text data.
3.  Once the orchestrator is complete and returns a result dictionary, you MUST use the `post_micro_entry` tool again to post the result.
    -   Set the status to 'completed_analysis'.
    -   Use the same `session_id` and `task_id`.
    -   Place the entire result dictionary from the orchestrator into the `output_payload_dict` argument of the `post_micro_entry` tool.
4.  Your final response to the coordinator should be a simple confirmation message, such as "Analysis complete and results have been posted to the board for task [task_id]."
"""

# Use the same status board tool as the other specialists.
data_analysis_specialist_v2 = Agent(
    name="DataAnalysisSpecialist_v2",
    model=DEFAULT_AGENT_MODEL,
    description="A specialist agent that uses a deterministic Python orchestrator to run a data analysis workflow and reports its status and final results to the Micro-Task board.",
    instruction=DATA_ANALYSIS_V2_INSTRUCTION,
    tools=[
        post_micro_entry,
        # We explicitly give it the orchestrator as a tool it can reason about, even if the prompt doesn't ask it to call it.
        # This can help the model understand its capabilities.
        run_data_analysis_agency
    ]
)

print(f"Agent '{data_analysis_specialist_v2.name}' created.")