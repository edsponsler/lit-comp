# literary_companion/lib/fun_fact_generators.py

from vertexai.generative_models import GenerativeModel
from cie_core.config import DEFAULT_AGENT_MODEL


def _generate_fact(instruction: str, text: str) -> dict:
    """A helper to make a direct, one-shot call to the generative model via Vertex AI."""
    try:
        # Get the generative model from Vertex AI
        model = GenerativeModel(DEFAULT_AGENT_MODEL)
        
        # Combine the instruction and the text for the prompt
        prompt = f"{instruction}\n\nHere is the text:\n---\n{text}\n---"
        
        response = model.generate_content(prompt)
        
        return {"status": "success", "fact": response.text}
    except Exception as e:
        print(f"--- Generator Error: {e} ---")
        return {"status": "error", "fact": f"Failed to generate fact. {e}"}


# --- The analyze_* functions below remain exactly the same ---

def analyze_historical_context(text: str) -> dict:
    """Analyzes the text for historical context."""
    instruction = (
        "You are a history expert. Based on the provided text from a classic novel, "
        "identify and explain one interesting piece of historical context (e.g., "
        "customs, technologies, events, societal norms) relevant to what the characters "
        "are experiencing. Be concise and engaging."
    )
    return _generate_fact(instruction, text)

def analyze_geographical_setting(text: str) -> dict:
    """Analyzes the text for the geographical setting."""
    instruction = (
        "You are a world geography expert. Based on the provided text, describe the "
        "physical location or setting. Mention any real-world places if they are "
        "named or clearly implied. Be concise."
    )
    return _generate_fact(instruction, text)

def analyze_plot_points(text: str) -> dict:
    """Analyzes the text for key plot points."""
    instruction = (
        "You are a literary analyst. Based on the text provided so far, summarize "
        "the main plot points in one or two brief sentences. What are the key events "
        "that have just happened?"
    )
    return _generate_fact(instruction, text)

def analyze_character_sentiments(text: str) -> dict:
    """Analyzes the sentiments of characters."""
    instruction = (
        "You are an expert in character psychology. Based on the provided text, "
        "describe the primary emotion or sentiment of a key character. Use evidence "
        "from the text to support your analysis. Be concise."
    )
    return _generate_fact(instruction, text)

def analyze_character_relationships(text: str) -> dict:
    """Analyzes the relationships between characters."""
    instruction = (
        "You are a literary relationship analyst. Based on the provided text, describe "
        "the nature of the relationship between two key characters mentioned. "
        "Are they friends, rivals, strangers? Be concise."
    )
    return _generate_fact(instruction, text)