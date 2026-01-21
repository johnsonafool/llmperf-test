#!/bin/bash

set -e

export OPENAI_API_KEY=sk-proj
export OPENAI_API_BASE="https://api.openai.com/v1"
export MODEL_NAME="gpt-4.1-nano"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="result_outputs/${MODEL_NAME}_${TIMESTAMP}"
CONCURRENT_REQUESTS=(1 10 20 30 40 50)
REPORT_LANGUAGE="en"  # Options: en (English), tw (Traditional Chinese), cn (Simplified Chinese)

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
        --max-num-completed-requests 10 \
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
