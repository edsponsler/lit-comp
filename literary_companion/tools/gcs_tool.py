# literary_companion/tools/gcs_tool.py
import json
import logging
import re
import tempfile
import time
import concurrent.futures
from typing import List, Optional

from google.cloud import storage
from google.adk.tools import FunctionTool

from literary_companion.tools.translation_tool import translate_text

# Configure logging for structured output that integrates well with Cloud Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a single, module-level client instance for reuse.
try:
    storage_client = storage.Client()
except Exception as e:
    logging.critical(f"Failed to initialize GCS client: {e}", exc_info=True)
    storage_client = None

def check_gcs_object_exists(bucket_name: str, object_name: str) -> bool:
    """Checks if an object exists in a GCS bucket."""
    if not storage_client:
        logging.error("GCS client not initialized.")
        return False
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        exists = blob.exists()
        logging.info(f"Checked for gs://{bucket_name}/{object_name}. Exists: {exists}")
        return exists
    except Exception as e:
        logging.error(f"Error checking existence of gs://{bucket_name}/{object_name}: {e}", exc_info=True)
        return False

def read_gcs_object(bucket_name: str, object_name: str) -> str:
    """Reads a text file from a GCS bucket."""
    if not storage_client:
        raise ConnectionError("GCS client not initialized.")
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        content = blob.download_as_text()
        logging.info(f"Successfully read {len(content)} chars from gs://{bucket_name}/{object_name}")
        return content
    except Exception as e:
        logging.error(f"Error reading from GCS: {e}", exc_info=True)
        raise IOError(f"Could not read gs://{bucket_name}/{object_name}") from e

def write_gcs_object(bucket_name: str, object_name: str, content: str) -> str:
    """Writes text content to a file in a GCS bucket."""
    if not storage_client:
        return "Error: GCS client not initialized."
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(content)
        logging.info(f"Successfully wrote to gs://{bucket_name}/{object_name}")
        return f"Success: Content written to gs://{bucket_name}/{object_name}"
    except Exception as e:
        logging.error(f"Error writing to GCS: {e}", exc_info=True)
        return f"Error: Could not write file to GCS. {e}"

def _translate_paragraph_worker(
    paragraph_id: int,
    paragraph_text: str,
    chapter_number: int,
    paragraph_in_chapter: int,
) -> Optional[dict]:
    """
    Worker function to translate a single paragraph.
    Designed to be called from a ThreadPoolExecutor.
    """
    if not paragraph_text:
        return None

    translated_text = translate_text(paragraph_text)

    if translated_text.startswith("Error:"):
        logging.warning(f"Skipping p-{paragraph_id} due to translation error.")
        return None

    logging.info(f"Successfully translated p-{paragraph_id} (Chapter {chapter_number}, Paragraph {paragraph_in_chapter}).")

    return {
        "paragraph_id": f"p-{paragraph_id}",
        "chapter_number": chapter_number,
        "paragraph_in_chapter": paragraph_in_chapter,
        "original_text": paragraph_text,
        "translated_text": translated_text,
    }

def process_and_translate_book(bucket_name: str, file_name: str) -> str:
    """
    Reads a book from GCS, identifies chapters, translates paragraph by paragraph
    in parallel, and writes the structured result back to GCS.
    """
    logging.info("Starting book processing workflow.")
    if not storage_client:
        return "Error: GCS client not initialized."
    start_time = time.monotonic()
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        original_content = blob.download_as_text()
        logging.info(f"Successfully read {len(original_content)} chars.")
    except Exception as e:
        return f"Error: Failed to read source file. {e}"

    # 1. Split the entire text by double newlines to get paragraph blocks.
    paragraph_blocks = re.split(r'(?:\r\n|\n){2,}', original_content.strip())

    # 2. Process paragraphs to assign chapter and paragraph numbers
    chapter_number = 0
    paragraph_in_chapter = 0
    total_paragraph_counter = 0
    paragraphs_with_metadata = []
    # This regex is case-insensitive and looks for "CHAPTER" followed by a space and a number/roman numeral.
    chapter_pattern = re.compile(r'^CHAPTER\s+[\w.]+', re.IGNORECASE)

    for p_block in paragraph_blocks:
        clean_block = p_block.strip()
        if not clean_block:
            continue  # Skip empty blocks

        if chapter_pattern.match(clean_block):
            chapter_number += 1
            paragraph_in_chapter = 0
            # We don't add the chapter title itself as a paragraph to translate
        else:
            paragraph_in_chapter += 1
            total_paragraph_counter += 1
            paragraphs_with_metadata.append({
                "text": clean_block.replace('\n', ' ').replace('\r', ' '),
                "total_id": total_paragraph_counter,
                "chapter": chapter_number,
                "para_in_chapter": paragraph_in_chapter
            })

    total_paragraphs = len(paragraphs_with_metadata)
    logging.info(f"Segmented text into {total_paragraphs} paragraphs across {chapter_number} chapters. Starting parallel translation...")

    prepared_paragraphs: List[Optional[dict]] = [None] * total_paragraphs

    # 3. Use a ThreadPoolExecutor to run translations in parallel.
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_index = {
            executor.submit(
                _translate_paragraph_worker,
                p_meta["total_id"],
                p_meta["text"],
                p_meta["chapter"],
                p_meta["para_in_chapter"]
            ): i
            for i, p_meta in enumerate(paragraphs_with_metadata)
        }

        processed_count = 0
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                if result:
                    prepared_paragraphs[index] = result
            except Exception as exc:
                logging.error(f"Paragraph index {index} generated an exception: {exc}", exc_info=True)

            processed_count += 1
            if processed_count % 50 == 0 or processed_count == total_paragraphs:
                percentage_complete = (processed_count / total_paragraphs) * 100
                logging.info(f"Progress - Completed translation for {processed_count} of {total_paragraphs} paragraphs ({percentage_complete:.2f}% complete).")

    # Filter out any None results from failed translations
    final_paragraphs = [p for p in prepared_paragraphs if p is not None]

    output_filename = file_name.replace('.txt', '_prepared.json')

    # 4. Use a temporary file to build the JSON for memory efficiency.
    try:
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=True) as tmp_file:
            tmp_file.write('{\n  "paragraphs": [\n')
            is_first_paragraph = True
            for paragraph_data in final_paragraphs:
                if not is_first_paragraph:
                    tmp_file.write(',\n')
                json.dump(paragraph_data, tmp_file, indent=4)
                is_first_paragraph = False

            tmp_file.write('\n  ]\n}\n')
            tmp_file.seek(0)
            output_blob = bucket.blob(output_filename)
            output_blob.upload_from_file(tmp_file, content_type='application/json')
            end_time = time.monotonic()
            duration_minutes = (end_time - start_time) / 60
            result_message = (
                f"Success! Processed {len(final_paragraphs)} paragraphs and saved to gs://{bucket_name}/{output_filename}. "
                f"Total time: {duration_minutes:.2f} minutes."
            )
            logging.info(result_message)
            return result_message
    except Exception as e:
        logging.error(f"Failed to write prepared file to GCS: {e}", exc_info=True)
        return f"Error: Failed to write prepared file to GCS. {e}"

# Expose the functions as ADK FunctionTools
gcs_reader_tool = FunctionTool(read_gcs_object)
gcs_writer_tool = FunctionTool(write_gcs_object)
book_processor_tool = FunctionTool(process_and_translate_book)