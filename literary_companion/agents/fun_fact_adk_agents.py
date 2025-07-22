# literary_companion/agents/fun_fact_adk_agents.py

import asyncio
import json
import os
import sys
from typing import AsyncGenerator, List, Dict

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part

from literary_companion.config import GCS_BUCKET_NAME
from literary_companion.lib import fun_fact_generators
from literary_companion.tools.gcs_tool import check_gcs_object_exists, read_gcs_object, write_gcs_object


class FunFactCoordinatorAgent(BaseAgent):
    """
    A Custom Agent to orchestrate the generation of multiple fun facts.
    This agent is now more efficient, checking for cached results first
    and generating facts directly if no cache is found.
    """
    fun_fact_types: List[str]
    book_name: str
    chapter_number: int

    def __init__(self, fun_fact_types: List[str], book_name: str, chapter_number: int):
        super().__init__(
            name="FunFactCoordinator",
            fun_fact_types=fun_fact_types,
            book_name=book_name,
            chapter_number=chapter_number,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """The main orchestration logic for generating fun facts."""
        print("--- ADK FunFactCoordinator: Starting fun fact generation. ---")

        if not GCS_BUCKET_NAME:
            error_msg = "Server configuration error: GCS_BUCKET_NAME is not set."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            yield Event(author=self.name, content=Content(parts=[Part(text=error_msg)]))
            return

        # Normalize book name by removing extension if present
        base_book_name, _ = os.path.splitext(self.book_name)
        cache_path = f"{base_book_name}/chapter_{self.chapter_number}_fun_facts.json"

        try:
            # 1. Check for cached fun facts
            if check_gcs_object_exists(GCS_BUCKET_NAME, cache_path):
                print(f"--- Cache hit for {cache_path}. Reading from GCS. ---")
                cached_data = read_gcs_object(GCS_BUCKET_NAME, cache_path)
                final_results = json.loads(cached_data)
                # Yield final event with cached data and exit immediately
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text=json.dumps(final_results))]),
                    actions=EventActions(state_delta={"final_fun_facts": final_results}),
                )
                print("--- ADK FunFactCoordinator: Finished early due to cache hit. ---")
                return

            # 2. Cache miss: Proceed with generation
            print(f"--- Cache miss for {cache_path}. Generating fun facts. ---")

            # 3. Read the prepared book content to get the text segment
            prepared_book_path = f"{base_book_name}_prepared.json"
            print(f"--- Reading prepared book from: {prepared_book_path} ---")
            book_data = json.loads(read_gcs_object(GCS_BUCKET_NAME, prepared_book_path))
            paragraphs = [
                p["original_text"]
                for p in book_data.get("paragraphs", [])
                if p.get("chapter_number") == self.chapter_number
            ]
            if not paragraphs:
                error_msg = f"No paragraphs found for chapter {self.chapter_number} in {prepared_book_path}."
                print(f"ERROR: {error_msg}", file=sys.stderr)
                yield Event(author=self.name, content=Content(parts=[Part(text=error_msg)]))
                return

            text_segment = "\n".join(paragraphs)

            # 4. Generate fun facts in parallel
            tasks = []
            for fact_type in self.fun_fact_types:
                generator_func = getattr(fun_fact_generators, f"analyze_{fact_type}", None)
                if generator_func:
                    # We need a wrapper to run the sync function in an async context
                    tasks.append(
                        asyncio.to_thread(generator_func, text_segment)
                    )

            generated_results = await asyncio.gather(*tasks)

            # 5. Aggregate results
            final_results = {}
            for i, fact_type in enumerate(self.fun_fact_types):
                # The result from the generator is a dict, e.g., {"status": "success", "fact": "..."}
                final_results[fact_type] = generated_results[i].get("fact", "No fact generated.")

            # 6. Write the new results to the cache
            write_gcs_object(GCS_BUCKET_NAME, cache_path, json.dumps(final_results, indent=4))
            print(f"--- Wrote fun facts to cache: {cache_path} ---")

        except Exception as e:
            error_msg = f"Error during fun fact generation or caching: {e}"
            print(f"--- {error_msg} ---", file=sys.stderr)
            final_results = {"error": error_msg}

        print(f"--- ADK FunFactCoordinator: Fun fact generation complete. Final results: {final_results} ---")

        # 7. Yield the final event with the results
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text=json.dumps(final_results))]),
            actions=EventActions(state_delta={"final_fun_facts": final_results}),
        )
