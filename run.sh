#!/bin/bash

set -e

info() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Configuration file
CONFIG_FILE="presets.yml"
if [ ! -f "$CONFIG_FILE" ]; then
    error "$CONFIG_FILE not found. Please create one in the project root."
fi

echo "=== LLM Performance Benchmark ==="
echo "Loading configuration from $CONFIG_FILE..."
echo ""

# Read all configuration from YAML
eval "$(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)

# API config
api = config.get('api', {})
print(f'OPENAI_API_KEY=\"{api.get(\"openai_api_key\", \"\")}\"')
print(f'OPENAI_API_BASE=\"{api.get(\"openai_api_base\", \"https://api.openai.com/v1\")}\"')

# Benchmark config
bench = config.get('benchmark', {})
print(f'MODEL_NAME=\"{bench.get(\"model_name\", \"gpt-4.1-nano\")}\"')
print(f'MAX_COMPLETED_REQUESTS={bench.get(\"max_completed_requests\", 100)}')
print(f'REQUEST_TIMEOUT={bench.get(\"request_timeout_seconds\", 600)}')

# Concurrent requests as bash array
concurrent = bench.get('concurrent_requests', [1, 10, 20, 30, 40, 50])
print(f'CONCURRENT_REQUESTS=({\" \".join(map(str, concurrent))})')

# Preset names
presets = config.get('presets', {})
print(f'PRESETS=\"{\" \".join(presets.keys())}\"')
")"

export OPENAI_API_KEY
export OPENAI_API_BASE
export MODEL_NAME

echo "=== Configuration Summary ==="
echo "API Base: $OPENAI_API_BASE"
echo "Model: $MODEL_NAME"
echo "Max completed requests: $MAX_COMPLETED_REQUESTS"
echo "Concurrent requests: ${CONCURRENT_REQUESTS[*]}"
echo "Request timeout: ${REQUEST_TIMEOUT}s"
echo "Presets to run: $PRESETS"
echo ""

# Display preset details
echo "=== Preset Details ==="
python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
presets = config.get('presets', {})
for name, preset in presets.items():
    min_in = preset.get('min_input_tokens', 0)
    max_in = preset.get('max_input_tokens', 0)
    min_out = preset.get('min_output_tokens', 0)
    max_out = preset.get('max_output_tokens', 0)
    print(f'  {name:10} - Input: {min_in}-{max_in}, Output: {min_out}-{max_out}')
"
echo ""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BASE_RESULTS_DIR="result_outputs/${MODEL_NAME}_${TIMESTAMP}"

info "Starting performance evaluation for model: ${MODEL_NAME}"
info "Running benchmarks for all presets: $PRESETS"
echo ""

# Loop through each preset
for USE_CASE in $PRESETS
do
    info "=========================================="
    info "Starting benchmark for preset: $USE_CASE"
    info "=========================================="

    RESULTS_DIR="$BASE_RESULTS_DIR/$USE_CASE"
    TOKEN_ARGS="--use-case $USE_CASE --disable-prefix-caching --unique-prompts"

    # Run benchmarks for all concurrent request levels
    for NUM in "${CONCURRENT_REQUESTS[@]}"
    do
        info "[$USE_CASE] Running benchmark with num-concurrent-requests=$NUM"
        python token_benchmark_ray.py \
            --model "$MODEL_NAME" \
            $TOKEN_ARGS \
            --max-num-completed-requests "$MAX_COMPLETED_REQUESTS" \
            --timeout "$REQUEST_TIMEOUT" \
            --num-concurrent-requests "$NUM" \
            --results-dir "$RESULTS_DIR/raw_data/performance/${NUM}" \
            --llm-api openai \
            --additional-sampling-params '{}' || error "Benchmark failed for $USE_CASE with num-concurrent-requests=$NUM."

        info "[$USE_CASE] Benchmark completed. Results saved to $RESULTS_DIR/raw_data/performance/${NUM}"
    done

    info "[$USE_CASE] Generating charts from the results..."
    python generate_charts.py \
        --results-dir "$RESULTS_DIR/raw_data/performance" || error "Chart generation failed for $USE_CASE."

    info "[$USE_CASE] Charts generated successfully."

    info "[$USE_CASE] Generating performance report..."
    python generate_reports.py \
        --results-dir "$RESULTS_DIR/raw_data/performance" \
        --model-name "$MODEL_NAME" \
        --output-dir "$RESULTS_DIR/report" \
        --use-case "$USE_CASE" || error "Report generation failed for $USE_CASE."

    info "[$USE_CASE] Performance report generated successfully."
    echo ""
done

info "=========================================="
info "All benchmarks completed!"
info "Results saved in: $BASE_RESULTS_DIR"
for USE_CASE in $PRESETS; do
    info "  - $BASE_RESULTS_DIR/$USE_CASE/"
done
info "=========================================="
