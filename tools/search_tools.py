# ~/projects/cie-0/tools/search_tools.py
from google.adk.tools import FunctionTool

def simple_web_search(query: str) -> dict:
    """
    Performs a simulated web search for a given query.
    In a real scenario, this would call an external search API. [cite: 258]
    Args:
        query (str): The search query. [cite: 259]
    Returns:
        dict: A dictionary containing a list of search results (URLs and snippets). [cite: 260]
    """
    print(f"--- Tool: simple_web_search called with query: {query} ---") # [cite: 261]

    # Mock results [cite: 261]
    mock_results = {
        "results": [
            {"url": f"http://example.com/search?q={query.replace(' ', '+')}_result1", "snippet": f"This is the first mock result for {query}."}, # [cite: 261]
            {"url": f"http://example.com/search?q={query.replace(' ', '+')}_result2", "snippet": f"Another interesting mock snippet related to {query}."}, # [cite: 261]
        ]
    }

    # Simulate some processing or data retrieval [cite: 262]
    if "error_trigger" in query: # [cite: 262]
        return {"status": "error", "message": "Simulated search API error."} # [cite: 262]
    return {"status": "success", "data": mock_results} # [cite: 262]

# Create ADK FunctionTool [cite: 262]
search_tool = FunctionTool(simple_web_search)

print("SearchTool (simple_web_search) defined.") # [cite: 262]