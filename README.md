# Literary Companion

## Description

Literary Companion is a web application that provides readers with interesting fun facts and trivia related to the book they are currently reading. As the user reads, the application analyzes the text and generates relevant information to enhance their reading experience.

## Features

- **Fun Fact Generation:** Automatically generates fun facts about the people, places, and concepts mentioned in the book.
- **Interactive Reading Experience:** Provides a side panel with fun facts that update as the user progresses through the text.
- **Google Cloud Integration:** Utilizes Google Cloud Storage for storing book content and Vertex AI for generative AI tasks.

## Getting Started

### Prerequisites

- Python 3.7+
- Google Cloud SDK
- A Google Cloud project with the following APIs enabled:
    - Vertex AI API
    - Cloud Storage API

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/literary-companion.git
   cd literary-companion
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**
   - Create a `.env` file in the root directory of the project.
   - Add the following environment variables to the `.env` file:
     ```
     GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
     GOOGLE_CLOUD_LOCATION="your-gcp-region"
     GCS_BUCKET_NAME="your-gcs-bucket-name"
     GCS_FILE_NAME="your-book-file-name.txt"
     DEFAULT_AGENT_MODEL="gemini-1.5-flash"
     ```

### Usage

1. **Upload your book to Google Cloud Storage:**
   - Make sure the book is a plain text file (`.txt`).
   - Upload the file to the GCS bucket you specified in your `.env` file.

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your web browser and navigate to `http://127.0.0.1:5001`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
