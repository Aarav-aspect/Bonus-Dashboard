# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/web-app
COPY web-app/package*.json ./
# We use --legacy-peer-deps because React 19 is used, and some packages 
# (like tremor/radix) may not have updated their peerDep ranges yet.
RUN npm ci --legacy-peer-deps
COPY web-app/ ./
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.11-slim
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
