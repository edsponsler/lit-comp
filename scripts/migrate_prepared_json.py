import json
import re
import argparse
import os

def migrate_json_schema(source_txt_path, prepared_json_path):
    """
    Updates an existing _prepared.json file to include chapter and paragraph numbers.

    Args:
        source_txt_path (str): The path to the original .txt file of the book.
        prepared_json_path (str): The path to the existing _prepared.json file to migrate.
    """
    print(f"Starting migration for {prepared_json_path} using source {source_txt_path}.")

    # 1. Read the original source text to build a map of paragraph metadata
    try:
        # Use 'utf-8-sig' to automatically handle and remove the
        # Byte Order Mark (BOM) character (\ufeff) from the start of the file.
        with open(source_txt_path, 'r', encoding='utf-8-sig') as f:
            original_content = f.read()
    except FileNotFoundError:
        print(f"Error: Source text file not found at {source_txt_path}")
        return

    paragraph_blocks = re.split(r'(?:\r\n|\n){2,}', original_content.strip())
    
    # Chapter numbering starts at 1. Any text before the first chapter marker
    # will be considered part of Chapter 1.
    chapter_number = 1
    paragraph_in_chapter = 0
    text_to_metadata_map = {}
    chapter_pattern = re.compile(r'^CHAPTER\s+[\w.]+', re.IGNORECASE)
    first_chapter_marker_seen = False

    for p_block in paragraph_blocks:
        # Normalize all whitespace (newlines, tabs, multiple spaces) to a single space
        # to create a more robust matching key.
        clean_block = ' '.join(p_block.split())
        if not clean_block:
            continue

        is_chapter_heading = chapter_pattern.match(clean_block)

        # If this is a chapter heading AND we've already seen the first one,
        # then it's a new chapter (e.g., Chapter 2, 3, etc.).
        if is_chapter_heading and first_chapter_marker_seen:
            chapter_number += 1
            paragraph_in_chapter = 0  # Reset for the new chapter.

        paragraph_in_chapter += 1

        if is_chapter_heading:
            first_chapter_marker_seen = True

        # The key is the sanitized original text. By including chapter titles
        # in the map, we ensure they can be matched from the JSON.
        text_to_metadata_map[clean_block] = {
            "chapter_number": chapter_number,
            "paragraph_in_chapter": paragraph_in_chapter
        }
    
    print(f"Source text analyzed: Found {len(text_to_metadata_map)} paragraphs across {chapter_number} chapters.")

    # 2. Read the existing prepared JSON file
    try:
        with open(prepared_json_path, 'r', encoding='utf-8') as f:
            prepared_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Prepared JSON file not found at {prepared_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {prepared_json_path}")
        return

    # 3. Iterate through JSON paragraphs and enrich them with the new metadata
    updated_paragraphs = []
    match_count = 0
    for p_data in prepared_data.get("paragraphs", []):
        # Normalize whitespace in the JSON's text to match the key generation
        # from the source .txt file.
        original_text_key = ' '.join(p_data.get("original_text", "").lstrip('\ufeff').split())
        if original_text_key in text_to_metadata_map:
            metadata = text_to_metadata_map[original_text_key]
            p_data["chapter_number"] = metadata["chapter_number"]
            p_data["paragraph_in_chapter"] = metadata["paragraph_in_chapter"]
            updated_paragraphs.append(p_data)
            match_count += 1
        else:
            # If a paragraph from the JSON isn't found in the source text map,
            # we can choose to either drop it or keep it without the new metadata.
            # For this script, we'll log it and drop it to ensure data integrity.
            print(f"Warning: Could not find a match for paragraph ID {p_data.get('paragraph_id')}. It will be excluded.")

    print(f"Successfully matched and updated {match_count} out of {len(prepared_data.get('paragraphs', []))} paragraphs.")

    # 4. Write the updated data to a new file
    output_path = prepared_json_path.replace('_prepared.json', '_prepared_v2.json')
    
    output_data = {"paragraphs": updated_paragraphs}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print(f"\nMigration complete! The updated file has been saved to:\n{output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Migrate a _prepared.json file to include chapter and paragraph numbers."
    )
    parser.add_argument(
        "source_txt",
        help="Path to the source .txt file of the book."
    )
    parser.add_argument(
        "prepared_json",
        help="Path to the _prepared.json file to be migrated."
    )
    args = parser.parse_args()

    migrate_json_schema(args.source_txt, args.prepared_json)
