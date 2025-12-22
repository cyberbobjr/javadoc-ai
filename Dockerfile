FROM python:3.12-slim

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY config.yaml.template ./

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variable for Python unbuffered output
ENV PYTHONUNBUFFERED=1

# Run the automation script
CMD ["python", "javadoc_automation.py"]
