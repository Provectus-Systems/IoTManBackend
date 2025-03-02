# Use an official Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first, to utilize Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose port 80 (though we already do that via docker-compose)
EXPOSE 80

# By default, we won't specify the command here. 
# We'll use 'command' in docker-compose to run uvicorn.
