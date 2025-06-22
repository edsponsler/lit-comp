# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the rest of the application code
COPY . . 

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable for the port
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Set the environment variable for Flask
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--preload", "app:app"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "--preload", "app:app"]
