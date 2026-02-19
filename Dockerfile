# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
RUN echo "BUILD_VERSION: 1.0.1 - FORCING PEER DEPS FIX"
WORKDIR /app/web-app
COPY web-app/package*.json ./
# Use --legacy-peer-deps and --force to handle React 19 peer dependency conflicts.
RUN npm install --legacy-peer-deps --force
COPY web-app/ ./
RUN  # 1. Build the container image (FORCING NO CACHE TO ENSURE UPDATES)
- name: 'gcr.io/cloud-builders/docker'
args: ['build', '--no-cache', '-t', 'gcr.io/$PROJECT_ID/bonus-dashboard:$SHORT_SHA', '.']python:3.11-slim
WORKDIR /app

# Install system dependencies if needed (e.g. for pandas/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from Stage 1 to the location api.py expects
COPY --from=frontend-builder /app/web-app/dist /app/web-app/dist

# Expose the port FastAPI will run on
EXPOSE 8080

# Run the application using uvicorn
# We use port 8080 as required by Cloud Run
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
