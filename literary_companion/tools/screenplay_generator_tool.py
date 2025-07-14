# In literary_companion/tools/screenplay_generator_tool.py

import os
import json
from google.cloud import storage
from literary_companion.tools.translation_tool import generate_content_with_prompt

# A tool to generate a screenplay beat sheet from a novel
def create_beat_sheet(bucket_name: str, file_name: str) -> str:
    """
    Creates a high-level, three-act beat sheet for the entire novel. Use this tool when the user asks for a beat sheet, outline, or high-level structure.
    
    Args:
        bucket_name: The GCS bucket where the novel is stored.
        file_name: The name of the prepared novel JSON file in the GCS bucket.

    Returns:
        The GCS path to the generated beat sheet file.
    """
    print(f"Starting beat sheet generation for gs://{bucket_name}/{file_name}")

    # 1. Initialize GCS client and determine output path.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # 2. Determine output filename and check if it already exists to prevent re-work.
    base_name = os.path.splitext(file_name.replace('_prepared.json', ''))[0]
    output_filename = f"{base_name}_beatsheet.txt"
    output_blob = bucket.blob(output_filename)
    if output_blob.exists():
        error_message = f"Error: Output file already exists at gs://{bucket_name}/{output_filename}. Please delete it first if you want to regenerate."
        print(error_message)
        return error_message

    # 3. Read the prepared JSON file from GCS and extract the modern translation.
    blob = bucket.blob(file_name)
    try:
        json_content = blob.download_as_text()
        data = json.loads(json_content)
        paragraphs = data.get("paragraphs", [])
        # Join all translated paragraphs to form the full modern text of the novel.
        modern_novel_text = " ".join(p.get("translated_text", "") for p in paragraphs if p.get("translated_text"))
        if not modern_novel_text:
            return "Error: Could not find any translated text in the prepared file."
    except Exception as e:
        return f"Error reading or parsing prepared file: {e}"

    # 4. Define a generic prompt for creating a beat sheet.
    instruction_prompt = """
Analyze the provided novel text. Based on standard three-act screenplay structure, create a beat sheet or a high-level outline for a feature film adaptation.
Identify the key plot points that should occur in:
- Act I (The Setup): Introduction of the main characters, the world they live in, and the inciting incident that sets the story in motion.
- Act II (The Confrontation): The rising action. The protagonist faces a series of obstacles and conflicts, leading to a major turning point or Midpoint.
- Act III (The Resolution): The climax of the story, where the central conflict is resolved, followed by the falling action and final outcome.
"""

    # Combine the instruction and the novel text into a single prompt for the model.
    full_prompt = f"{instruction_prompt}\n\nNOVEL TEXT:\n---\n{modern_novel_text}\n---\n\nBEAT SHEET:"

    # 5. Use the generative model to create the beat sheet
    print("Generating beat sheet with generative AI...")
    beat_sheet_text = generate_content_with_prompt(prompt=full_prompt)

    # 6. Save the beat sheet to a new file in GCS
    output_blob.upload_from_string(beat_sheet_text)
    
    print(f"Beat sheet successfully saved to gs://{bucket_name}/{output_filename}")
    return f"gs://{bucket_name}/{output_filename}"

def generate_scene_list(bucket_name: str, file_name: str, chapters_to_process: str) -> str:
    """
    Generates a detailed list of scenes for a specific range of chapters. This tool requires a 'chapters_to_process' argument (e.g., "Chapters 1 through 16"). Use this when the user asks for a scene list or wants to break down a part of the novel.

    Args:
        bucket_name: The GCS bucket where the prepared novel is stored.
        file_name: The name of the prepared novel JSON file (e.g., 'moby_dick_prepared.json').
        chapters_to_process: A string describing the chapters to include (e.g., "Chapters 1 through 16").

    Returns:
        The GCS path to the generated scene list file.
    """
    print(f"Starting scene list generation for {chapters_to_process} from gs://{bucket_name}/{file_name}")

    # 1. Initialize GCS client and determine output path.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # 2. Determine output filename and check if it already exists to prevent re-work.
    base_name = os.path.splitext(file_name.replace('_prepared.json', ''))[0]
    chapters_filename_part = chapters_to_process.lower().replace(" ", "_").replace(".", "")
    output_filename = f"{base_name}_{chapters_filename_part}_scenes.txt"
    output_blob = bucket.blob(output_filename)
    if output_blob.exists():
        error_message = f"Error: Output file already exists at gs://{bucket_name}/{output_filename}. Please delete it first if you want to regenerate."
        print(error_message)
        return error_message

    # 3. Read the prepared JSON file and get the modern text.
    blob = bucket.blob(file_name)
    try:
        json_content = blob.download_as_text()
        data = json.loads(json_content)
        paragraphs = data.get("paragraphs", [])
        modern_novel_text = " ".join(p.get("translated_text", "") for p in paragraphs if p.get("translated_text"))
        if not modern_novel_text:
            return "Error: Could not find any translated text in the prepared file."
    except Exception as e:
        return f"Error reading or parsing prepared file: {e}"

    # 4. Define the prompt for scene list generation.
    instruction_prompt = f"""
    Based on the provided novel text, take {chapters_to_process} and convert this section into a sequence of individual scenes.

    For each scene, provide the following in standard screenplay format:
    - A Scene Heading (INT./EXT. LOCATION - DAY/NIGHT).
    - A concise, one-sentence summary of the scene's core action or purpose.

    For example:
    SCENE 1
    INT. SPOUTER-INN - NIGHT
    Ishmael arrives in New Bedford and must share a bed with the intimidating, tattooed harpooneer, Queequeg.

    SCENE 2
    INT. SPOUTER-INN - DAY
    Ishmael and Queequeg bond over breakfast, forming an unlikely friendship.

    Now, generate the scene list for {chapters_to_process}.
    """
    
    full_prompt = f"{instruction_prompt}\n\nNOVEL TEXT:\n---\n{modern_novel_text}\n---\n\nSCENE LIST:"

    # 5. Use the generative model
    print("Generating scene list with generative AI...")
    scene_list_text = generate_content_with_prompt(prompt=full_prompt)

    # 6. Save the scene list to a new file in GCS
    output_blob.upload_from_string(scene_list_text)
    
    output_path = f"gs://{bucket_name}/{output_filename}"
    print(f"Scene list successfully saved to {output_path}")
    return output_path
