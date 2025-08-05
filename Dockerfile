# Multi-stage Dockerfile for BorgDash
# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /src/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install all dependencies (including devDependencies) for build
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Build and prepare the Python backend
FROM python:3.13-slim AS backend-builder

WORKDIR /src

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final production image
FROM python:3.13-slim AS production

WORKDIR /app


# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl vim gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/

# Copy backend application code
COPY backend/ ./
RUN mkdir -p /app/contrib
# COPY backend/config.example.toml /app/contrib/config.example.toml

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /src/frontend/dist ./static



# Create data directory and set permissions
# RUN mkdir -p /data && chown -R borgdash:borgdash /data
# RUN mkdir -p /config && chown -R borgdash:borgdash /config


# Set environment for production
ENV PYTHON_ENV=production

VOLUME /data
VOLUME /config


# Do not switch to non-root user here; entrypoint will handle user creation and switching

# Expose port 80
EXPOSE 80

# Set entrypoint to handle config.toml initialization
ENTRYPOINT ["/entrypoint.sh"]

# Run the application (default CMD)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
