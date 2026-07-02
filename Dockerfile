# Solana Trading Bot Dockerfile
# Multi-stage build for smaller final image
# Base image: Python 3.12.3 (matching local development)

# ============================================================================
# Stage 1: Build stage - Install all dependencies
# ============================================================================
FROM python:3.12.3-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime stage - Slim production image
# ============================================================================
FROM python:3.12.3-slim as runtime

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SOLANA_RPC_URL="https://api.devnet.solana.com" \
    NETWORK="devnet" \
    PYTHONPATH="/app"

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY .env.example .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Default command (can be overridden)
ENTRYPOINT ["python"]
CMD ["-c", "print('Solana Trading Bot - Docker container ready')"]

# ============================================================================
# Build and run instructions:
#   docker build -t solana-trading-bot .
#   docker run -it --rm solana-trading-bot
#
# For development with environment variables:
#   docker run -it --rm -e WALLET_PRIVATE_KEY="..." solana-trading-bot
#
# For mainnet (override default):
#   docker run -it --rm -e NETWORK="mainnet" -e SOLANA_RPC_URL="https://api.mainnet-beta.solana.com" solana-trading-bot
# ============================================================================