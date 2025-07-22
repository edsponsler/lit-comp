# literary_companion/agents/fun_fact_adk_agents.py

import json
import sys
from typing import AsyncGenerator, List

from google.adk.agents import LlmAgent, BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part
from literary_companion.config import DEFAULT_AGENT_MODEL, GCS_BUCKET_NAME
from literary_companion.tools.gcs_tool import check_gcs_object_exists, read_gcs_object, write_gcs_object


def get_generator_instruction(fact_type: str) -> str:
    """Returns the appropriate instruction for a given fun fact type."""
    instructions = {
        "historical_context": (
            "You are a history expert. Based on the provided text from a classic novel, "
            "identify and explain one interesting piece of historical context (e.g., "
            "customs, technologies, events, societal norms) relevant to what the characters "
            "are experiencing. Be concise and engaging."
        ),
        "geographical_setting": (
            "You are a world geography expert. Based on the provided text, describe the "
            "physical location or setting. Mention any real-world places if they are "
            "named or clearly implied. Be concise."
        ),
        "plot_points": (
            "You are a literary analyst. Based on the text provided so far, summarize "
            "the main plot points in one or two brief sentences. What are the key events "
            "that have just happened?"
        ),
        "character_sentiments": (
            "You are an expert in character psychology. Based on the provided text, "
            "describe the primary emotion or sentiment of a key character. Use evidence "
            "from the text to support your analysis. Be concise."
        ),
        "character_relationships": (
            "You are a literary relationship analyst. Based on the provided text, describe "
            "the nature of the relationship between two key characters mentioned. "
            "Are they friends, rivals, strangers? Be concise."
        ),
    }
    return instructions.get(
        fact_type,
        "You are a helpful assistant. Generate a fun fact based on the provided text.",
    )


class FunFactGeneratorAgent(LlmAgent):
    """An LLM Agent that generates a single fun fact of a specific type."""

    def __init__(self, fact_type: str):
        super().__init__(
            name=f"FunFactGenerator_{fact_type}",
            model=DEFAULT_AGENT_MODEL,
            instruction=f"""{get_generator_instruction(fact_type)}

You will be given a text segment from a book in the session state under the key 'text_segment'.
Base your fun fact on this text: {{text_segment}}
""",
            output_key=f"{fact_type}_result",
        )


class FunFactCoordinatorAgent(BaseAgent):
    """A Custom Agent to orchestrate the generation of multiple fun facts."""
    fun_fact_types: List[str]
    book_name: str
    chapter_number: int
    # The list holds agents that are, at a minimum, BaseAgents.
    # This aligns with the type of the _generator_agents variable used
    # for initialization, resolving the type conflict.
    generator_agents: List[BaseAgent]
    workflow_agent: ParallelAgent

    def __init__(self, fun_fact_types: List[str], book_name: str, chapter_number: int):
        # To avoid ambiguity from local variables shadowing class fields,
        # we use uniquely named local variables for construction.
        # Explicitly type the list as containing BaseAgent to satisfy the
        # invariant type checker for the 'sub_agents' parameter.
        _generator_agents: List[BaseAgent] = [
            FunFactGeneratorAgent(fact_type) for fact_type in fun_fact_types
        ]
        _workflow_agent = ParallelAgent(
            name="FunFactWorkflow", sub_agents=_generator_agents
        )

        # Pydantic's BaseModel.__init__ (the superclass of BaseAgent) validates
        # that all declared fields are provided on creation. We must pass all
        # fields to the super() call to satisfy this runtime requirement.
        super().__init__(
            name="FunFactCoordinator",
            sub_agents=[_workflow_agent],
            fun_fact_types=fun_fact_types,
            book_name=book_name,
            chapter_number=chapter_number,
            generator_agents=_generator_agents,
            workflow_agent=_workflow_agent,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """The main orchestration logic for generating fun facts."""
        print("--- ADK FunFactCoordinator: Starting fun fact generation. ---")

        if not GCS_BUCKET_NAME:
            error_msg = "Server configuration error: GCS_BUCKET_NAME is not set."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            # Yield an error event and stop
            yield Event(author=self.name, content=Content(parts=[Part(text=error_msg)]))
            return

        cache_path = f"{self.book_name}/chapter_{self.chapter_number}_fun_facts.json"

        try:
            if check_gcs_object_exists(GCS_BUCKET_NAME, cache_path):
                print(f"--- Cache hit for {cache_path}. Reading from GCS. ---")
                cached_data = read_gcs_object(GCS_BUCKET_NAME, cache_path)
                final_results = json.loads(cached_data)
            else:
                print(f"--- Cache miss for {cache_path}. Generating fun facts. ---")
                # Run the parallel workflow to generate all fun facts
                async for event in self.workflow_agent.run_async(ctx):
                    yield event

                # Aggregate the results from the session state
                print(f"--- ADK FunFactCoordinator: Session state after workflow: {ctx.session.state} ---")
                final_results = {}
                for fact_type in self.fun_fact_types:
                    result_key = f"{fact_type}_result"
                    if result_key in ctx.session.state:
                        final_results[fact_type] = ctx.session.state[result_key]

                write_gcs_object(GCS_BUCKET_NAME, cache_path, json.dumps(final_results, indent=4))
                print(f"--- Wrote fun facts to cache: {cache_path} ---")
        except Exception as e:
            print(f"--- Error during fun fact generation or caching: {e} ---")
            final_results = {"error": str(e)}

        print(f"--- ADK FunFactCoordinator: Fun fact generation complete. Final results: {final_results} ---")

        # Create a state delta to explicitly signal the final state change.
        state_delta = {"final_fun_facts": final_results}

        # Yield a final event. This is crucial because it signals the ADK Runner
        # to process any pending state changes, including the "final_fun_facts"
        # we just added to the session state.
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text=json.dumps(final_results))]),
            actions=EventActions(state_delta=state_delta),
        )
