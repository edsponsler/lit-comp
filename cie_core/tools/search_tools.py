# cie_core/tools/search_tools.py
import os
import requests
from bs4 import BeautifulSoup
from google.adk.tools import FunctionTool

CUSTOM_SEARCH_API_KEY = os.getenv("CUSTOM_SEARCH_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT") # For ADK

# Number of search results to process
NUM_SEARCH_RESULTS = 3 # try to find a max that works well without hitting API limits
MAX_CONTENT_LENGTH = 1500 # Max characters to extract per page

def simple_web_search(query: str) -> dict:
    """
    Performs a web search using Google Custom Search API for a given query,
    then scrapes basic textual content from the top results.
    Args:
        query (str): The search query.
    Returns:
        dict: A dictionary containing a status and a list of search results
              (URL and scraped content).
    """
    print(f"--- Tool: simple_web_search (real) called with query: {query} ---")

    if not CUSTOM_SEARCH_API_KEY or not CUSTOM_SEARCH_ENGINE_ID:
        print("--- Tool: Error: CUSTOM_SEARCH_API_KEY or CUSTOM_SEARCH_ENGINE_ID not set. ---")
        return {"status": "error", "message": "Search API key or engine ID not configured."}

    search_results_data = []
    api_url = f"https://www.googleapis.com/customsearch/v1?key={CUSTOM_SEARCH_API_KEY}&cx={CUSTOM_SEARCH_ENGINE_ID}&q={query}&num={NUM_SEARCH_RESULTS}"

    try:
        print(f"--- Tool: Querying Google Custom Search API: {api_url.replace(CUSTOM_SEARCH_API_KEY, '[API_KEY_HIDDEN]')} ---")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        search_items = response.json().get("items", [])

        if not search_items:
            print(f"--- Tool: No search results found for query: {query} ---")
            return {"status": "success", "data": {"results": []}, "message": "No search results found."}

        print(f"--- Tool: Found {len(search_items)} search results. Attempting to scrape... ---")

        for item in search_items:
            url = item.get("link")
            title = item.get("title")
            snippet_from_search = item.get("snippet") # Google's snippet

            if not url:
                continue

            print(f"--- Tool: Attempting to scrape content from: {url} ---")
            try:
                page_response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                page_response.raise_for_status()
                
                # Check content type, proceed only if it's likely HTML
                content_type = page_response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    print(f"--- Tool: Skipping non-HTML content at {url} (type: {content_type}) ---")
                    search_results_data.append({
                        "url": url,
                        "title": title,
                        "content": f"Skipped: Content type is '{content_type}', not HTML. Search snippet: {snippet_from_search}"
                    })
                    continue

                soup = BeautifulSoup(page_response.content, 'html.parser')
                
                # Basic content extraction: join text from all paragraph tags
                # You can make this more sophisticated (e.g., extract from main content tags)
                paragraphs = soup.find_all('p')
                content = "\n".join([para.get_text(separator=' ', strip=True) for para in paragraphs])
                
                if not content.strip() and snippet_from_search: # If no <p> tags, use Google's snippet
                    content = f"Could not extract paragraph content. Using Google snippet: {snippet_from_search}"
                elif not content.strip():
                    content = "No textual content found in paragraphs."

                search_results_data.append({
                    "url": url,
                    "title": title,
                    "content": content[:MAX_CONTENT_LENGTH] # Truncate if too long
                })
                print(f"--- Tool: Successfully scraped and processed: {url} ---")

            except requests.exceptions.RequestException as e_req:
                print(f"--- Tool: Error fetching page {url}: {e_req} ---")
                search_results_data.append({
                    "url": url,
                    "title": title,
                    "content": f"Error fetching page: {e_req}. Search snippet: {snippet_from_search}"
                })
            except Exception as e_parse: # Catch other errors like parsing errors
                print(f"--- Tool: Error processing page {url}: {e_parse} ---")
                search_results_data.append({
                    "url": url,
                    "title": title,
                    "content": f"Error processing page: {e_parse}. Search snippet: {snippet_from_search}"
                })
        
        return {"status": "success", "data": {"results": search_results_data}}

    except requests.exceptions.RequestException as e:
        print(f"--- Tool: Error calling Google Custom Search API: {e} ---")
        return {"status": "error", "message": f"Search API request failed: {e}"}
    except Exception as e_gen: # Catch-all for other unexpected errors
        print(f"--- Tool: An unexpected error occurred in simple_web_search: {e_gen} ---")
        return {"status": "error", "message": f"An unexpected error occurred: {e_gen}"}

simple_web_search_tool = FunctionTool(simple_web_search)

print("SearchTool (simple_web_search - REAL with scraping) defined.")