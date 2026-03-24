# Stage 1: Build the React frontend
FROM --platform=linux/amd64 node:20-slim AS frontend-builder
WORKDIR /app/web-app
COPY web-app/package*.json ./
# Use --legacy-peer-deps and --force to handle React 19 peer dependency conflicts.
RUN npm install --legacy-peer-deps --force
COPY web-app/ ./
RUN npm run build

# Stage 2: Build the Python backend
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (secrets.toml and .env are excluded via .dockerignore)
COPY . .

# Copy built frontend from Stage 1 to the location api.py expects
COPY --from=frontend-builder /app/web-app/dist /app/web-app/dist

# DATABASE_URL and other secrets must be provided as Cloud Run environment
# variables or via Secret Manager — never baked into the image.
ENV PORT=8080

# Expose the port FastAPI will run on
EXPOSE 8080

# Run the application using uvicorn
# Cloud Run injects $PORT at runtime; default to 8080 if not set.
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}"]
