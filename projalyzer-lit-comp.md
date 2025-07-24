# Project Summary

The Literary Companion is a web application designed to enhance the reading experience of classic novels by providing modern English translations and contextually relevant "fun facts." It leverages Python, Flask, the Google Agent Development Kit (ADK), and Vertex AI.

**Purpose:** To enrich the classic reading experience by providing a modern translation and AI-generated insights.

**Capabilities:**

*   **Side-by-Side Reading:** Displays original text alongside a modern translation.
*   **Fun Fact Generation:** Generates contextually relevant trivia related to the current passage (historical context, geographical settings, plot points, character sentiments, and relationships).
*   **Screenplay Generation:** Includes tools to generate a beat sheet or scene list from a novel.
*   **Cloud-Native Deployment:** Deployed on Google Cloud Run using Docker.
*   **Caching:** Implements a Redis-based caching mechanism (with GCS fallback) to improve performance.
*   **Book Preparation Workflow:** Processes raw book files into a structured format.

**Current Development Status:**

The project appears to be a functional application with a well-defined architecture. The `README.md` provides instructions for setting up and running the application locally. The architecture is modular and cloud-native, utilizing Google Cloud services like Cloud Run, Vertex AI, and Cloud Storage. The project also has contribution guidelines, suggesting active development and a willingness to accept community contributions. The use of Google ADK suggests the project is leveraging a modern approach to building AI-powered applications. The presence of `requirements.in` and `requirements.txt` indicate dependency management. The `ARCHITECTURE.md` file shows a mature project with consideration of caching and deployment. The `app.py` shows integration with Redis and GCS.

# Chosen Activities

## Improvement

**Summary:** Refactor the project to move all configuration parameters to `config.py` and use the `python-decouple` library to manage environment variables. This will improve maintainability and scalability by centralizing configuration and providing a cleaner separation of concerns.

## Development

**Summary:** Switch the project to using `pip-compile` from `pip-tools` for dependency management. This will improve the reliability of the project by ensuring deterministic builds and preventing dependency conflicts, while also addressing the existing issue of having both `requirements.in` and `requirements.txt` files.

## New Feature

**Summary:** Add "User Bookmarks and Highlighting" functionality to the project. This will enhance user engagement and personalization by allowing users to save specific passages and highlight text, making it easier to return to important sections of the book.

# Gemini CLI Prompts

## Improvement Prompt

Provide a project outline with specific steps to refactor the Literary Companion project, moving all configuration parameters from `app.py` and other modules to `config.py`. Use the `python-decouple` library to manage environment variables. Include instructions on how to install `python-decouple`, modify `config.py` to load environment variables, and update the codebase to use the centralized configuration.

## Development Prompt

Generate a project outline detailing how to switch the Literary Companion project to using `pip-compile` from `pip-tools` for dependency management. Include instructions on how to install `pip-tools`, create and update `requirements.in`, compile `requirements.txt` from `requirements.in`, and integrate this process into the project's development workflow. Make sure to remove any conflicting or obsolete files and practices, such as directly editing `requirements.txt`.

## New Feature Prompt

Create a project outline to add 'User Bookmarks and Highlighting' functionality to the Literary Companion project. The outline should include steps for: 1) Designing the database schema in Firestore to store bookmarks and highlights, including user association (using session ID initially). 2) Implementing the backend API endpoints (using Flask) to create, read, update, and delete bookmarks and highlights. 3) Implementing the frontend UI (using HTML, CSS, and JavaScript) to allow users to bookmark passages, highlight text, and manage their bookmarks and highlights. 4) Consider how to integrate a rich text editor or text selection library for highlighting and formatting.