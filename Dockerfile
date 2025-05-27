# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Ensure google-cloud-cli is NOT installed in the image for Cloud Run,
# as authentication is handled via the service account.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# Be mindful of what's copied; .dockerignore can exclude files like .git, .venv, __pycache__
COPY . .

# Ensure .env is NOT copied if it contains secrets. [cite: 45]
# These should be set as environment variables in Cloud Run. [cite: 46]
# The .gitignore should already prevent .env from being committed to git. [cite: 46]

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable for the port (Cloud Run expects 8080 by default)
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE 
# Other ENV vars like GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION,
# CUSTOM_SEARCH_API_KEY, CUSTOM_SEARCH_ENGINE_ID will be set in Cloud Run.

# Run app.py when the container launches using Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "180", "app:app"]
CMD exec gunicorn --bind 0.0.0.0:$PORT --timeout 180 app:app