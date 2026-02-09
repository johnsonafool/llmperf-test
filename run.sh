#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
print(f'ROUNDS={bench.get(\"rounds\", 5)}')
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
export RAY_DEDUP_LOGS=0

echo "=== Configuration Summary ==="
echo "API Base: $OPENAI_API_BASE"
echo "Model: $MODEL_NAME"
echo "Rounds: $ROUNDS"
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
        MAX_COMPLETED_REQUESTS=$((NUM * ROUNDS))
        info "[$USE_CASE] Running benchmark with num-concurrent-requests=$NUM, max-completed-requests=$MAX_COMPLETED_REQUESTS ($ROUNDS rounds)"
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
    echo ""
done

# Generate overall report combining all use cases
info "Generating overall performance report..."
python generate_overall_report.py \
    --results-dir "$BASE_RESULTS_DIR" \
    --model-name "$MODEL_NAME" \
    --output-dir "$BASE_RESULTS_DIR/report" || error "Overall report generation failed."

info "Overall performance report generated successfully."

info "=========================================="
info "All benchmarks completed!"
info "Results saved in: $BASE_RESULTS_DIR"
info "Overall report: $BASE_RESULTS_DIR/report/performance_report.md"
info "=========================================="
