FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for HEIC support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif-dev \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user before copying files so ownership is set correctly
RUN adduser --disabled-password --gecos "" appuser

# Install Python dependencies
COPY --chown=appuser:appuser app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Copy application code
COPY --chown=appuser:appuser app/ .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
