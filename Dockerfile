# Use an appropriate base image with Python pre-installed
FROM alpine:3.18

# Set the working directory inside the container
WORKDIR /app

# Copy the entire current directory into the container at /app
COPY . /app

# Install any Python dependencies

RUN apk add python3
RUN apk add py3-pip
RUN pip install -r requirements.txt

# Run Python script
CMD ["python", "main.py"]
