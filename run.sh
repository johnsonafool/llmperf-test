#!/bin/bash

set -e

# Default values
DEFAULT_OPENAI_API_KEY="sk-proj-xxxx"
DEFAULT_OPENAI_API_BASE="https://api.openai.com/v1"
DEFAULT_MODEL_NAME="gpt-4.1-nano"
DEFAULT_MAX_COMPLETED_REQUESTS=100
DEFAULT_REPORT_LANGUAGE="en"

CONCURRENT_REQUESTS=(1 10 20 30 40 50)

# Prompt for user input
echo "=== LLM Performance Benchmark Configuration ==="
echo ""

read -sp "OpenAI API Key [default: ****]: " OPENAI_API_KEY
echo ""
export OPENAI_API_KEY=${OPENAI_API_KEY:-$DEFAULT_OPENAI_API_KEY}

read -p "OpenAI API Base URL [default: $DEFAULT_OPENAI_API_BASE]: " OPENAI_API_BASE
export OPENAI_API_BASE=${OPENAI_API_BASE:-$DEFAULT_OPENAI_API_BASE}

read -p "Model name [default: $DEFAULT_MODEL_NAME]: " MODEL_NAME
MODEL_NAME=${MODEL_NAME:-$DEFAULT_MODEL_NAME}
export MODEL_NAME

read -p "Max number of completed requests [default: $DEFAULT_MAX_COMPLETED_REQUESTS]: " MAX_COMPLETED_REQUESTS
MAX_COMPLETED_REQUESTS=${MAX_COMPLETED_REQUESTS:-$DEFAULT_MAX_COMPLETED_REQUESTS}

read -p "Report language (en/tw/cn) [default: $DEFAULT_REPORT_LANGUAGE]: " REPORT_LANGUAGE
REPORT_LANGUAGE=${REPORT_LANGUAGE:-$DEFAULT_REPORT_LANGUAGE}

echo ""
echo "=== Configuration Summary ==="
echo "API Base: $OPENAI_API_BASE"
echo "Model: $MODEL_NAME"
echo "Max completed requests: $MAX_COMPLETED_REQUESTS"
echo "Report language: $REPORT_LANGUAGE"
echo ""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="result_outputs/${MODEL_NAME}_${TIMESTAMP}"

info() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

info "Starting performance evaluation for model: ${MODEL_NAME}"
for NUM in "${CONCURRENT_REQUESTS[@]}"
do
    info "Running benchmark with num-concurrent-requests=$NUM"
    python token_benchmark_ray.py \
        --model "$MODEL_NAME" \
        --mean-input-tokens 550 \
        --stddev-input-tokens 150 \
        --mean-output-tokens 150 \
        --stddev-output-tokens 10 \
        --max-num-completed-requests "$MAX_COMPLETED_REQUESTS" \
        --timeout 600 \
        --num-concurrent-requests "$NUM" \
        --results-dir "$RESULTS_DIR/raw_data/performance/${NUM}" \
        --llm-api openai \
        --additional-sampling-params '{}' || error "Benchmark failed for num-concurrent-requests=$NUM."

    info "Benchmark completed. Results saved to $RESULTS_DIR/raw_data/performance/${NUM}"
done

info "Generating charts from the results..."
python generate_charts.py \
    --results-dir "$RESULTS_DIR/raw_data/performance" || error "Chart generation failed."

info "Charts generated successfully. Saved in $RESULTS_DIR/raw_data/performance."

info "Generating performance report..."
python generate_reports.py \
    --results-dir "$RESULTS_DIR/raw_data/performance" \
    --model-name "$MODEL_NAME" \
    --output-dir "$RESULTS_DIR/report" \
    --language "$REPORT_LANGUAGE" || error "Report generation failed."

info "Performance report generated successfully. Saved in $RESULTS_DIR/report/"
