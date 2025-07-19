# Literary Companion Report

## 1. Project Summary:

The Literary Companion is a web application designed to enhance the reading experience by providing users with fun facts and trivia related to the book they are currently reading. As the user reads, the application analyzes the text and generates relevant information in real-time. The application utilizes a microservice architecture, with distinct workflows for book preparation and fun fact generation, orchestrated by Google ADK agents. It leverages Google Cloud services, including Google Cloud Storage for storing book content, Vertex AI for generative AI tasks (translation and fun fact generation), and Firestore for a micro-task board within the fun fact generation process. The frontend is built with vanilla JavaScript, HTML, and CSS and served via a Flask backend. The project includes detailed documentation for its architecture and deployment to Google Cloud Run using Docker. The project appears to be in a deployable state, with clear instructions for setting up the necessary Google Cloud environment and deploying the application.

## 2. Chosen Activities:

### Improvement: Comprehensive Logging

Adding detailed logging throughout the application, especially in the agents and tools, will significantly improve debugging and monitoring capabilities. Including request IDs, timestamps, and relevant context information will aid in identifying and resolving issues quickly. Structured logging will allow for easier analysis and aggregation of logs.

### Development: Personalized Vocabulary Building

Identifying unfamiliar words in the text for the user and providing definitions and example sentences, along with the ability to save them to a personal vocabulary list, will directly enhance the user's understanding and engagement with the text.

### New Feature: AI-Powered Q&A

Integrating a feature where users can ask questions about the text and receive AI-generated answers would be incredibly valuable. This leverages the existing Vertex AI models and provides a direct way for users to deepen their understanding of the material.

## 3. Gemini CLI Prompts:

### Improvement Prompt:

```
Create a project outline for implementing comprehensive logging in the Literary Companion application. The logging should include:
- Request IDs
- Timestamps
- Relevant context information
- Configurable log levels
- Structured logging
The logging should be implemented in agents and tools.
```

### Development Prompt:

```
Create a project outline for implementing personalized vocabulary building in the Literary Companion application. The features should include:
- Identifying unfamiliar words in the text for the user.
- Providing definitions and example sentences.
- Allowing users to save these words to a personal vocabulary list for later review.
```

### New Feature Prompt:

```
Create a project outline for implementing AI-Powered Q&A feature in the Literary Companion application. The features should include:
- Allowing users to ask questions about the text.
- Receiving AI-generated answers.
- Leveraging the existing Vertex AI models.
```

