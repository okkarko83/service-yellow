# service-blue/Dockerfile
FROM python:3.9-slim 

# Set the working directory
WORKDIR /app 

# Copy requirements first to leverage Docker layer caching
COPY src/requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the application source code from the 'src' directory
COPY src/ .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]