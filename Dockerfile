# Use python-slim for better wheel compatibility and stability while maintaining small size
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install runtime dependencies
# libmagic1 is required by python-magic (dependency of Mastodon.py)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependencies
COPY pyproject.toml uv.lock /app/

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy the application code
COPY . /app

# Run Python script with unbuffered output for container logs
CMD ["python", "-u", "main.py"]
