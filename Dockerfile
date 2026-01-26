FROM python:3.11-slim

LABEL maintainer="LLMPerf"
LABEL description="LLM Performance Benchmark Tool"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY token_benchmark_ray.py ./
COPY generate_charts.py ./
COPY generate_reports.py ./
COPY run.sh ./
COPY inference.png ./

# Install Python dependencies
RUN uv pip install --system . && \
    uv pip install --system pandas pillow pyyaml matplotlib

# Copy sonnet.txt to installed package location
RUN cp /app/src/llmperf/sonnet.txt $(python -c "import llmperf; print(llmperf.__path__[0])")

# Make run.sh executable
RUN chmod +x run.sh

# Create mount points with proper permissions
RUN mkdir -p /app/result_outputs && chmod 777 /app/result_outputs

# Default command
CMD ["./run.sh"]
