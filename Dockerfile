# Dockerfile for AI-Agent-Workflow Project
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY basic_logs/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src

# Set the default command to run the main orchestrator
CMD ["python", "src/main_orchestrator.py"]
