# Dockerfile

# --- Stage 1: Builder ---
# This stage installs dependencies into a virtual environment. Using a separate
# stage keeps the final image smaller and more secure.
FROM python:3.12-slim as builder

# Create and activate a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image ---
# This stage copies only the necessary application code and the installed
# dependencies from the builder stage.
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy only the necessary application code
COPY app.py .
COPY cie_core ./cie_core
COPY literary_companion ./literary_companion
COPY templates ./templates

# Activate the virtual environment for the running container
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable for the port
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
# Use exec form to properly handle signals and environment variable expansion
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --preload app:app
