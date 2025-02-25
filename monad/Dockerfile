# Use Python 3.9 slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set default RPC URLs (these will be overridden by environment variables if provided)
ENV MONAD_RPC_URLS='["https://testnet-rpc.monad.xyz", "https://monad-testnet.drpc.org"]'
ENV CHAIN_ID=10143
ENV MIN_DELAY_SECONDS=60
ENV MAX_DELAY_SECONDS=300
ENV MAX_RPC_TRIES=3
ENV RPC_TIMEOUT_SECONDS=10

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Create and set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Create and activate virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership of the application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to run the application
CMD ["python", "main.py"] 