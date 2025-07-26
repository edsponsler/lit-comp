# In literary_companion/agents/screenplay_coordinator_v2.py
import logging
import json
from typing import AsyncGenerator, Optional, Any
from collections import defaultdict
import pathlib
from typing_extensions import override

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from literary_companion.config import DEFAULT_AGENT_MODEL
from google.genai.types import GenerateContentConfig, Content, Part

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _load_mock_data(filename: str) -> Optional[Any]:
    """Loads mock data from the mocks directory."""
    mock_path = pathlib.Path(__file__).parent.parent / "mocks" / filename
    if not mock_path.exists():
        logger.error(f"[MOCK] Mock file not found: {mock_path}")
        return None
    try:
        with open(mock_path, 'r', encoding='utf-8') as f:
            if filename.endswith(".json"):
                return json.load(f)
            return f.read()
    except Exception as e:
        logger.error(f"[MOCK] Error loading mock file {mock_path}: {e}")
        return None


def _clean_and_parse_json(json_string: Optional[str], log_context: str) -> Optional[Any]:
    """Strips markdown from a JSON string and parses it."""
    if not json_string:
        return None

    # Remove markdown fences and whitespace
    cleaned_str = json_string.strip()
    if cleaned_str.startswith("```json"):
        cleaned_str = cleaned_str[7:]
    if cleaned_str.endswith("```"):
        cleaned_str = cleaned_str[:-3]
    cleaned_str = cleaned_str.strip()

    try:
        return json.loads(cleaned_str)
    except json.JSONDecodeError:
        logger.error(f"[{log_context}] Failed to decode JSON. Content: {cleaned_str[:500]}...")
        return None

# --- 1. Define the Sub-Agents for Each Step ---

scene_generator_agent = LlmAgent(
    name="SceneGenerator",
    model=DEFAULT_AGENT_MODEL,
    instruction="""You are a screenwriter. Based on the provided novel text below, break it down into a detailed list of scenes.
For each scene, provide a scene heading (INT./EXT. LOCATION - DAY/NIGHT), a detailed action description, and any key dialogue from the original text.
Respond with a JSON list of scenes, where each scene is an object with 'scene_heading', 'action', and 'dialogue' keys.

Novel Text:
---
{novel_text}
---
""",
    generate_content_config=GenerateContentConfig(max_output_tokens=8192),
    output_key="scenes",
)

creative_prompt_generator_agent = LlmAgent(
    name="CreativePromptGenerator",
    model=DEFAULT_AGENT_MODEL,
    instruction="""You are a creative director. For the given scene with action '{action}' and dialogue '{dialogue}',
generate prompts for an AI to create related assets.
Generate one prompt for each of the following: 'music', 'sound_effects', 'concept_art', and 'narration'.
The prompts should be detailed and evocative.
Respond ONLY with a single JSON object containing the prompts. Do not add any other text, markdown, or explanations.""",
    generate_content_config=GenerateContentConfig(max_output_tokens=4096),
    output_key="creative_prompts",
)

screenplay_assembler_agent = LlmAgent(
    name="ScreenplayAssembler",
    model=DEFAULT_AGENT_MODEL,
    instruction="""You are a production assistant. Assemble the scenes provided below into a single, well-formatted screenplay document in markdown.
For each scene, first list the scene heading and action/dialogue.
Then, list the generated creative prompts under a 'Creative Assets' heading, including subheadings for Music, Sound Effects, Concept Art, and Narration.

Scenes with Prompts:
---
{scenes_with_prompts}
---
""",
    generate_content_config=GenerateContentConfig(max_output_tokens=8192),
    output_key="final_screenplay",
)


# --- 2. Define the Custom Orchestrator Agent ---

class ScreenplayCoordinatorV2(BaseAgent):
    """
    Custom agent for an enhanced screenplay generation workflow.
    This agent orchestrates LLM agents to generate a screenplay, create asset
    prompts, and assemble a final document.
    """
    scene_generator: LlmAgent
    creative_prompt_generator: LlmAgent
    screenplay_assembler: LlmAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str = "ScreenplayCoordinatorV2",
        scene_generator: LlmAgent = scene_generator_agent,
        creative_prompt_generator: LlmAgent = creative_prompt_generator_agent,
        screenplay_assembler: LlmAgent = screenplay_assembler_agent,
    ):
        sub_agents_list = [
            scene_generator,
            creative_prompt_generator,
            screenplay_assembler,
        ]
        super().__init__(
            name=name,
            scene_generator=scene_generator,
            creative_prompt_generator=creative_prompt_generator,
            screenplay_assembler=screenplay_assembler,
            sub_agents=sub_agents_list,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Implements the custom orchestration logic for the screenplay workflow."""
        logger.info(f"[{self.name}] Starting enhanced screenplay workflow.")
        use_mocks = ctx.session.state.get("use_mocks", False)

        if use_mocks:
            logger.warning(f"[{self.name}] RUNNING IN MOCK MODE. NO LLM CALLS WILL BE MADE.")
            logger.info(f"[{self.name}] Loading mock final screenplay...")
            final_screenplay = _load_mock_data("mock_final_screenplay.md")
            if final_screenplay:
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text=final_screenplay)]),
                    actions=EventActions(state_delta={"final_screenplay": final_screenplay}),
                )
            logger.info(f"[{self.name}] Mock workflow finished.")
            return

        # --- Live Workflow ---

        # Step 1: Group paragraphs by chapter
        paragraphs = ctx.session.state.get("paragraphs", [])
        if not paragraphs:
            logger.error(f"[{self.name}] No paragraphs found in initial state. Aborting.")
            return

        chapters = defaultdict(list)
        for p in paragraphs:
            chapters[p["chapter_number"]].append(p["translated_text"])

        final_screenplays_by_chapter = {}
        # Loop through each chapter to generate a separate screenplay
        for chapter_num in sorted(chapters.keys()):
            logger.info(f"[{self.name}] --- Starting screenplay for Chapter {chapter_num} ---")

            # --- Generate Scenes for the current chapter ---
            chapter_text = "\n\n".join(chapters[chapter_num])
            scene_gen_ctx = ctx.model_copy(update={"session": ctx.session.model_copy(update={"state": {"novel_text": chapter_text}})})
            
            async for event in self.scene_generator.run_async(scene_gen_ctx):
                yield event
            
            scenes_text = ctx.session.state.pop("scenes", None)
            scenes_for_chapter = _clean_and_parse_json(scenes_text, f"{self.name}-Chap{chapter_num}")

            if not scenes_for_chapter:
                logger.warning(f"[{self.name}] No scenes generated for Chapter {chapter_num}. Skipping.")
                continue
            
            logger.info(f"[{self.name}] Generated {len(scenes_for_chapter)} scenes for Chapter {chapter_num}.")

            # --- Generate Creative Prompts for this chapter's scenes ---
            scenes_with_prompts = []
            for i, scene in enumerate(scenes_for_chapter):
                logger.info(f"[{self.name}] Generating prompts for scene {i+1}/{len(scenes_for_chapter)} (Chapter {chapter_num})...")
                prompt_gen_state = {"action": scene.get("action", ""), "dialogue": scene.get("dialogue", "")}
                prompt_gen_ctx = ctx.model_copy(update={"session": ctx.session.model_copy(update={"state": prompt_gen_state})})

                async for event in self.creative_prompt_generator.run_async(prompt_gen_ctx):
                    yield event

                prompts_text = ctx.session.state.pop("creative_prompts", None)
                creative_prompts = _clean_and_parse_json(prompts_text, f"{self.name}-Chap{chapter_num}-Scene{i+1}")
                
                if not creative_prompts:
                    creative_prompts = {"error": "Failed to generate or parse creative prompts."}
                scene["creative_prompts"] = creative_prompts
                scenes_with_prompts.append(scene)
            
            logger.info(f"[{self.name}] Finished generating prompts for Chapter {chapter_num}.")

            # --- Assemble the Final Screenplay for this chapter ---
            logger.info(f"[{self.name}] Assembling screenplay for Chapter {chapter_num}...")
            assembler_state = {"scenes_with_prompts": scenes_with_prompts}
            assembler_ctx = ctx.model_copy(update={"session": ctx.session.model_copy(update={"state": assembler_state})})

            async for event in self.screenplay_assembler.run_async(assembler_ctx):
                yield event

            chapter_screenplay = ctx.session.state.pop("final_screenplay", None)
            if chapter_screenplay:
                final_screenplays_by_chapter[chapter_num] = chapter_screenplay
                logger.info(f"[{self.name}] Successfully assembled screenplay for Chapter {chapter_num}.")
            else:
                logger.warning(f"[{self.name}] Failed to assemble screenplay for Chapter {chapter_num}.")

        # After the loop, save the dictionary of all screenplays to the main state
        ctx.session.state["chapter_screenplays"] = final_screenplays_by_chapter
        logger.info(f"[{self.name}] Workflow finished. All chapter screenplays are in 'chapter_screenplays' state variable.")

        # Yield a final event to signal completion and commit the state
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text="All chapter screenplays generated.")]),
            actions=EventActions(state_delta={"chapter_screenplays": final_screenplays_by_chapter}),
        )

# --- 3. Create a default instance of the coordinator ---
screenplay_coordinator_v2 = ScreenplayCoordinatorV2()