# Project Summary

Literary Companion is a web application designed to enhance the reading experience by providing readers with fun facts and trivia related to the book they are reading. It analyzes the text in real-time and generates relevant information in a side panel as the user progresses through the book.

**Capabilities:**

*   Generates fun facts about people, places, and concepts mentioned in a book.
*   Provides an interactive reading experience with dynamically updating information.
*   Integrates with Google Cloud Storage for storing book content.
*   Utilizes Vertex AI for generative AI tasks (likely for fact generation).

**Development Status:**

The project appears to be in a functional state, with instructions for installation, setup, and usage provided in the README. It leverages Google Cloud services and requires specific environment variables to be configured. The presence of files like `Dockerfile` and `cloudbuild.yaml` suggests that it is containerized and deployable to Google Cloud. The `requirements.txt` file indicates that the project uses Python.

# Chosen Activities

## Improvement

The chosen improvement activity is to replace the current `InMemorySessionService` with Redis as a persistent session store. This enhancement is crucial for production readiness, ensuring session data is preserved across application restarts, which is essential for a stable user experience.

## Development

The chosen development activity is to implement unit and integration tests for the application. Currently, there are no tests in place. Implementing tests will help ensure the application's reliability and prevent regressions as new features are added. Focus will be given to testing the core logic of fun fact generation and the interaction with Google Cloud Storage.

## New Feature

The chosen new feature activity is to add multi-format support to the application. The application currently only supports plain text files. Supporting additional ebook formats like EPUB and PDF will make the application more accessible and appealing to a wider audience.

# Gemini CLI Prompts

## Improvement Prompt

```
I have a Python Flask application called Literary Companion that uses Google's ADK and Vertex AI. Currently, it uses `InMemorySessionService` for session management.

Create a project outline detailing the steps necessary to replace `InMemorySessionService` with Redis as a persistent session store.
Include steps for setting up Redis, integrating it with the Flask application, and migrating any existing session data (if applicable).
The Literary Companion application uses Google Cloud Storage (GCS) and Vertex AI. Consider this when suggesting how to configure Redis.
Provide example code snippets where appropriate. The code should be well-commented.
```

## Development Prompt

```
I have a Python Flask application called Literary Companion that uses Google's ADK and Vertex AI. The application currently has no unit or integration tests.

Create a project outline for implementing unit and integration tests for the application.
Focus on testing the core logic of fun fact generation (implemented using Vertex AI) and the interaction with Google Cloud Storage (GCS).
Specify which testing framework to use (e.g., pytest) and provide examples of how to write unit and integration tests for these specific components.
The Literary Companion application uses Google Cloud Storage (GCS) and Vertex AI. Take into account potential mocking or patching strategies for these external services when writing tests.
Provide example code snippets where appropriate. The code should be well-commented.
```

## New Feature Prompt

```
I have a Python Flask application called Literary Companion that currently only supports plain text files (.txt).

Create a project outline detailing the steps necessary to add support for EPUB and PDF file formats.
Include steps for installing necessary libraries (e.g., ebooklib, PyPDF2), parsing the files, extracting the text content, and handling potential errors.
Also describe how to integrate the new file format support into the existing application, ensuring that the fun fact generation logic can handle the extracted text from the various file types. Consider any preprocessing or standardization steps needed to ensure consistent input for the fun fact generation agent.
Provide example code snippets where appropriate. The code should be well-commented.
```

