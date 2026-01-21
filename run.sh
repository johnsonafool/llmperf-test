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
echo "=== Token Configuration ==="
echo "Choose configuration method:"
echo "  1) Use case preset (rag/generate/normal)"
echo "  2) Fixed token lengths"
echo "  3) Mean/stddev (default)"
read -p "Configuration method [1/2/3, default: 3]: " CONFIG_METHOD
CONFIG_METHOD=${CONFIG_METHOD:-3}

case $CONFIG_METHOD in
    1)
        echo "Available presets:"
        echo "  rag      - Input: 1k-10k tokens, Output: 200-500 tokens"
        echo "  generate - Input: 100-200 tokens, Output: 1k-10k tokens"
        echo "  normal   - Input: 100-200 tokens, Output: 200-500 tokens"
        read -p "Use case preset [default: normal]: " USE_CASE
        USE_CASE=${USE_CASE:-normal}
        TOKEN_ARGS="--use-case $USE_CASE"
        ;;
    2)
        read -p "Input token length [default: 550]: " INPUT_TOKENS
        INPUT_TOKENS=${INPUT_TOKENS:-550}
        read -p "Output token length [default: 150]: " OUTPUT_TOKENS
        OUTPUT_TOKENS=${OUTPUT_TOKENS:-150}
        TOKEN_ARGS="--input-token-length $INPUT_TOKENS --output-token-length $OUTPUT_TOKENS"
        ;;
    3)
        read -p "Mean input tokens [default: 550]: " MEAN_INPUT
        MEAN_INPUT=${MEAN_INPUT:-550}
        read -p "Stddev input tokens [default: 150]: " STDDEV_INPUT
        STDDEV_INPUT=${STDDEV_INPUT:-150}
        read -p "Mean output tokens [default: 150]: " MEAN_OUTPUT
        MEAN_OUTPUT=${MEAN_OUTPUT:-150}
        read -p "Stddev output tokens [default: 10]: " STDDEV_OUTPUT
        STDDEV_OUTPUT=${STDDEV_OUTPUT:-10}
        TOKEN_ARGS="--mean-input-tokens $MEAN_INPUT --stddev-input-tokens $STDDEV_INPUT --mean-output-tokens $MEAN_OUTPUT --stddev-output-tokens $STDDEV_OUTPUT"
        ;;
esac

echo ""
echo "=== Cache Prevention (for VLLM hardware testing) ==="
read -p "Disable prefix caching for pure hardware testing? (y/n) [default: n]: " DISABLE_CACHE
if [ "$DISABLE_CACHE" = "y" ] || [ "$DISABLE_CACHE" = "Y" ]; then
    TOKEN_ARGS="$TOKEN_ARGS --disable-prefix-caching --unique-prompts"
    echo "Prefix caching disabled - each prompt will have a unique prefix"
fi

echo ""
echo "=== Configuration Summary ==="
echo "API Base: $OPENAI_API_BASE"
echo "Model: $MODEL_NAME"
echo "Max completed requests: $MAX_COMPLETED_REQUESTS"
echo "Token config: $TOKEN_ARGS"
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
        $TOKEN_ARGS \
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
