# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
# PYTHONUNBUFFERED ensures that python output is sent straight to the terminal
# without being first buffered, which is useful for logging.
ENV PYTHONUNBUFFERED=True
# PORT is the standard environment variable for Cloud Run to specify the listening port.
ENV PORT=8080

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# Command to run the application using Gunicorn.
# Gunicorn is a robust production-ready WSGI server.
# We bind to the port specified by the $PORT environment variable set by Cloud Run.
# --preload loads application code before forking workers, which can save memory.
# We use 'sh -c' to ensure the $PORT environment variable is correctly expanded.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --preload app:app"]
