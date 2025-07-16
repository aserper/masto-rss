# Step 1: Use an official, slim Python image as a base
# 'slim' is a good balance between size and functionality.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Step 2: Copy only the requirements file
# This makes optimal use of Docker's layer caching.
COPY requirements.txt .

# Step 3: Install the dependencies
# The --no-cache-dir option keeps the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Now, copy the rest of the application code
# Because the code changes more often than the dependencies, this step is placed later.
COPY . .

# Step 5: Execute the correct Python script
# Note the correct filename.
CMD ["python3", "main.py"]
