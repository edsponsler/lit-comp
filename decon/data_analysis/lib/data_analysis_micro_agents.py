from typing import Dict, Any, List
import re
import json

# A simple list of common English "stopwords". In a real-world scenario,
# you would use a more comprehensive list from a library like NLTK or spaCy.
STOPWORDS = set([
    "a", "an", "the", "and", "but", "or", "in", "on", "at", "for", "to", "of",
    "i", "you", "he", "she", "it", "we", "they", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "shall", "should", "can", "could", "may", "might", "must", "with", "from",
    "by", "as", "that", "this", "these", "those", "what", "which", "who", "whom"
])

def extract_keywords(text_input: str) -> dict:
    """
    Extracts keywords and returns them as a JSON string.
    """
    if not isinstance(text_input, str) or not text_input:
        return {"keywords": []}

    text = text_input.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    keywords = [
        word for word in words if word not in STOPWORDS and len(word) > 2
    ]
    
    # Dump the output dictionary to a JSON string
    output_dict = {"keywords": list(set(keywords))}
    return output_dict

# The tool will return a dictionary directly.
def segment_sentences(text_input: str) -> dict:
    """
    Segments text into sentences. Returns a dictionary containing the list
    of sentences, mimicking the agent's final desired output.
    """
    if not isinstance(text_input, str) or not text_input:
        return {"sentences": []}

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text_input)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Return a raw dictionary, not a JSON string.
    output_dict = {"sentences": sentences}
    return output_dict