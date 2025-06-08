from typing import Dict, Any, List
import re

# A simple list of common English "stopwords". In a real-world scenario,
# you would use a more comprehensive list from a library like NLTK or spaCy.
STOPWORDS = set([
    "a", "an", "the", "and", "but", "or", "in", "on", "at", "for", "to", "of",
    "i", "you", "he", "she", "it", "we", "they", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "shall", "should", "can", "could", "may", "might", "must", "with", "from",
    "by", "as", "that", "this", "these", "those", "what", "which", "who", "whom"
])

def extract_keywords(text_input: str) -> Dict[str, Any]:
    """
    A simple micro-agent function to extract keywords from a text.

    This function embodies the principle of a simple, specialized agent.
    It performs one basic function: identifying potentially important words.

    Args:
        text_input: The string of text to analyze.

    Returns:
        A dictionary containing the list of extracted keywords.
    """
    if not isinstance(text_input, str) or not text_input:
        return {"keywords": []}

    # Normalize the text: lowercase, remove punctuation
    text = text_input.lower()
    text = re.sub(r'[^\w\s]', '', text) # Remove punctuation

    # Split into words and filter out stopwords and short words
    words = text.split()
    keywords = [
        word for word in words if word not in STOPWORDS and len(word) > 2
    ]

    # Return the findings in the standard dictionary format
    return {"keywords": list(set(keywords))} # Use set() to get unique keywords

def segment_sentences(text_input: str) -> Dict[str, Any]:
    """
    A simple micro-agent function to segment text into sentences.

    This is another example of a specialized agent performing a foundational
    task without needing to "understand" the content.

    Args:
        text_input: The string of text to segment.

    Returns:
        A dictionary containing the list of sentences.
    """
    if not isinstance(text_input, str) or not text_input:
        return {"sentences": []}

    # A simple regex to split sentences based on punctuation.
    # This is a basic approach; more advanced libraries would handle
    # cases like "Mr. Smith" better.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text_input)

    # Filter out any empty strings that might result from the split
    sentences = [s.strip() for s in sentences if s.strip()]

    return {"sentences": sentences}