# Use official Python base image
FROM python:3.9

# Set working directory inside container
WORKDIR /app

# Copy all project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose Flask port
EXPOSE 5000

# Start Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
