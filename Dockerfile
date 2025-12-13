# Use an appropriate base image with Python pre-installed
FROM alpine:3.18

# Set the working directory inside the container
WORKDIR /app

# Install Python dependencies in a single layer
RUN apk add --no-cache python3 py3-pip

# Copy requirements first for better layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Run Python script
CMD ["python", "main.py"]
