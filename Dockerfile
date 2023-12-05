# Use an appropriate base image with Python pre-installed
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the entire current directory into the container at /app
COPY . /app

# Install any Python dependencies
RUN pip install -r requirements.txt

# Run your Python script
CMD ["python", "main.py"]
