# In scripts/filter_prepared_book.py

import json
import argparse
import os
import sys

def filter_book_by_chapter(input_path: str, max_chapter: int, output_path: str | None = None):
    """
    Reads a prepared book JSON file and creates a new version containing only
    chapters up to and including the specified chapter number.

    Args:
        input_path: Path to the input '_prepared.json' file.
        max_chapter: The maximum chapter number to include in the output.
        output_path: Optional path for the output file. If None, a new name is
                     generated based on the input path and max_chapter.
    """
    print(f"Reading from: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_path}'. File may be corrupt.", file=sys.stderr)
        sys.exit(1)

    if "paragraphs" not in data:
        print(f"Error: 'paragraphs' key not found in '{input_path}'. Invalid format.", file=sys.stderr)
        sys.exit(1)

    print(f"Filtering paragraphs to include chapters 1 through {max_chapter}...")
    filtered_paragraphs = [
        p for p in data["paragraphs"]
        if p.get("chapter_number") is not None and int(p["chapter_number"]) <= max_chapter
    ]

    if not filtered_paragraphs:
        print(f"Warning: No paragraphs found for chapters up to {max_chapter}. The output file will be empty.")

    new_data = {"paragraphs": filtered_paragraphs}

    if not output_path:
        base, ext = os.path.splitext(input_path)
        # Ensure we replace _prepared.json correctly
        if base.endswith('_prepared'):
            base = base[:-9]
        output_path = f"{base}_prepared_chap_1-{max_chapter}{ext}"

    print(f"Writing {len(filtered_paragraphs)} paragraphs to: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=4)
        print("Successfully created filtered file.")
    except IOError as e:
        print(f"Error: Could not write to output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filters a prepared book JSON file to include only a specified range of chapters."
    )
    parser.add_argument("input_file", help="Path to the input '_prepared.json' file.")
    parser.add_argument("chapter_number", type=int, help="The maximum chapter number to include in the output file.")
    parser.add_argument("--output_file", help="Optional. The full path for the output file. If not provided, a name will be generated automatically.")
    args = parser.parse_args()

    if args.chapter_number <= 0:
        print("Error: chapter_number must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    filter_book_by_chapter(args.input_file, args.chapter_number, args.output_file)