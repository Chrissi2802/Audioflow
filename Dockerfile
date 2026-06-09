FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY src/ ./src/

# Install application
RUN poetry install --no-dev --no-interaction --no-ansi

# Create non-root user
RUN useradd --create-home --shell /bin/bash audioflow
USER audioflow

# Set up volumes
VOLUME ["/downloads"]

# Entry point
ENTRYPOINT ["audioflow"]
CMD ["--help"]