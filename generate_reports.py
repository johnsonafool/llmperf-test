import argparse
import glob
import json
import logging
import os
import shutil
from datetime import datetime

import pandas as pd
import yaml
from PIL import Image

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_preset_config(use_case):
    """Load preset configuration from presets.yml."""
    config_paths = [
        os.path.join(os.getcwd(), "presets.yml"),
        os.path.join(os.path.dirname(__file__), "presets.yml"),
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            presets = config.get("presets", config)
            if use_case in presets:
                return presets[use_case]
    return None

# Multi-language support
TRANSLATIONS = {
    "en": {
        "title": "Performance Report",
        "generated": "Generated",
        "section1_title": "1. Metrics Description",
        "section1_intro": "The following diagram illustrates the key performance metrics measured during LLM inference:",
        "metrics_explained": "Key Metrics Explained",
        "ttft_title": "Time to First Token (TTFT)",
        "ttft_desc": "The time elapsed from when the query is sent until the first token is received. This measures the initial response latency and is critical for user-perceived responsiveness.",
        "itl_title": "Inter-token Latency (ITL)",
        "itl_desc": "The time between consecutive tokens during generation. Lower ITL means smoother streaming output and better user experience during text generation.",
        "e2e_title": "End-to-End Latency",
        "e2e_desc": "The total time from sending the query to receiving the complete response. This includes TTFT plus the entire generation time.",
        "throughput_title": "Output Throughput",
        "throughput_desc": "The number of tokens generated per second. Higher throughput indicates better generation efficiency.",
        "section2_title": "2. Performance Testing Metrics",
        "section3_title": "3. Concurrent Performance Visualization",
        "full_chart_title": "Full Performance Chart",
        "metric_e2e": "End-to-End Latency (seconds)",
        "metric_itl": "Inter-token Latency (seconds)",
        "metric_ttft": "Time to First Token (seconds)",
        "metric_throughput": "Output Throughput (tokens/s)",
        "section0_title": "Test Configuration",
        "use_case": "Use Case",
        "use_case_rag": "RAG (Retrieval-Augmented Generation)",
        "use_case_generate": "Text Generation",
        "use_case_normal": "Normal Conversation",
        "input_tokens": "Input Tokens",
        "output_tokens": "Output Tokens",
        "token_config": "Configuration",
        "token_range": "Preset Range",
        "token_fixed": "Fixed Value",
        "rounds": "Rounds",
        "test_settings": "Test Settings",
        "cache_prevention": "Cache Prevention",
        "cache_prevention_desc": "Prefix caching disabled + Unique prompts enabled for accurate hardware performance measurement",
    },
    "tw": {
        "title": "效能報告",
        "generated": "產生時間",
        "section1_title": "1. 指標說明",
        "section1_intro": "以下圖表說明 LLM 推論過程中測量的關鍵效能指標：",
        "metrics_explained": "關鍵指標說明",
        "ttft_title": "首 Token 延遲 (TTFT)",
        "ttft_desc": "從發送查詢到收到第一個 token 所經過的時間。此指標衡量初始回應延遲，對於使用者感知的回應性至關重要。",
        "itl_title": "Token 間延遲 (ITL)",
        "itl_desc": "生成過程中連續 token 之間的時間間隔。較低的 ITL 意味著更流暢的串流輸出和更好的文字生成使用者體驗。",
        "e2e_title": "端到端延遲",
        "e2e_desc": "從發送查詢到收到完整回應的總時間。這包括 TTFT 加上整個生成時間。",
        "throughput_title": "輸出吞吐量",
        "throughput_desc": "每秒生成的 token 數量。較高的吞吐量表示更好的生成效率。",
        "section2_title": "2. 效能測試指標",
        "section3_title": "3. 併發效能視覺化",
        "full_chart_title": "完整效能圖表",
        "metric_e2e": "端到端延遲（秒）",
        "metric_itl": "Token 間延遲（秒）",
        "metric_ttft": "首 Token 延遲（秒）",
        "metric_throughput": "輸出吞吐量（tokens/s）",
        "section0_title": "測試配置",
        "use_case": "使用案例",
        "use_case_rag": "RAG（檢索增強生成）",
        "use_case_generate": "文本生成",
        "use_case_normal": "一般對話",
        "input_tokens": "輸入 Token",
        "output_tokens": "輸出 Token",
        "token_config": "配置",
        "token_range": "預設範圍",
        "token_fixed": "固定值",
        "rounds": "輪次",
        "test_settings": "測試設定",
        "cache_prevention": "快取防護",
        "cache_prevention_desc": "已停用前綴快取 + 已啟用唯一提示詞，確保準確的硬體效能測量",
    },
    "cn": {
        "title": "性能报告",
        "generated": "生成时间",
        "section1_title": "1. 指标说明",
        "section1_intro": "以下图表说明 LLM 推理过程中测量的关键性能指标：",
        "metrics_explained": "关键指标说明",
        "ttft_title": "首 Token 延迟 (TTFT)",
        "ttft_desc": "从发送查询到收到第一个 token 所经过的时间。此指标衡量初始响应延迟，对于用户感知的响应性至关重要。",
        "itl_title": "Token 间延迟 (ITL)",
        "itl_desc": "生成过程中连续 token 之间的时间间隔。较低的 ITL 意味着更流畅的流式输出和更好的文本生成用户体验。",
        "e2e_title": "端到端延迟",
        "e2e_desc": "从发送查询到收到完整响应的总时间。这包括 TTFT 加上整个生成时间。",
        "throughput_title": "输出吞吐量",
        "throughput_desc": "每秒生成的 token 数量。较高的吞吐量表示更好的生成效率。",
        "section2_title": "2. 性能测试指标",
        "section3_title": "3. 并发性能可视化",
        "full_chart_title": "完整性能图表",
        "metric_e2e": "端到端延迟（秒）",
        "metric_itl": "Token 间延迟（秒）",
        "metric_ttft": "首 Token 延迟（秒）",
        "metric_throughput": "输出吞吐量（tokens/s）",
        "section0_title": "测试配置",
        "use_case": "使用案例",
        "use_case_rag": "RAG（检索增强生成）",
        "use_case_generate": "文本生成",
        "use_case_normal": "一般对话",
        "input_tokens": "输入 Token",
        "output_tokens": "输出 Token",
        "token_config": "配置",
        "token_range": "预设范围",
        "token_fixed": "固定值",
        "rounds": "轮次",
        "test_settings": "测试设置",
        "cache_prevention": "缓存防护",
        "cache_prevention_desc": "已禁用前缀缓存 + 已启用唯一提示词，确保准确的硬件性能测量",
    },
}


def split_performance_chart(results_dir, output_dir):
    """Split the 2x2 performance chart into individual charts."""
    chart_path = os.path.join(results_dir, "performance_chart.png")
    if not os.path.exists(chart_path):
        logger.warning(f"Performance chart not found: {chart_path}")
        return False

    img = Image.open(chart_path)
    width, height = img.size

    mapping = [
        "inter_token_latency",
        "end_to_end_latency",
        "time_to_first_token",
        "output_throughput",
    ]

    half_width = width // 2
    half_height = height // 2

    boxes = [
        (0, 0, half_width, half_height),  # Top-left
        (half_width, 0, width, half_height),  # Top-right
        (0, half_height, half_width, height),  # Bottom-left
        (half_width, half_height, width, height),  # Bottom-right
    ]

    os.makedirs(output_dir, exist_ok=True)

    for i, box in enumerate(boxes):
        part = img.crop(box)
        output_path = os.path.join(output_dir, mapping[i] + ".png")
        part.save(output_path)
        logger.info(f"Saved: {output_path}")

    # Copy the full chart as well
    shutil.copy(chart_path, os.path.join(output_dir, "performance_chart.png"))
    return True


def dataframe_to_markdown(df):
    """Convert a DataFrame to markdown table without tabulate dependency."""
    headers = df.columns.tolist()
    header_row = "| " + " | ".join(str(h) for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"

    rows = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(v) for v in row.values) + " |"
        rows.append(row_str)

    return "\n".join([header_row, separator] + rows)


def load_metrics_data(results_dir, lang="en"):
    """Load CSV metrics data and return as formatted markdown tables."""
    t = TRANSLATIONS[lang]
    metric_files = {
        t["metric_e2e"]: "end_to_end_latency.csv",
        t["metric_itl"]: "inter_token_latency.csv",
        t["metric_ttft"]: "time_to_first_token.csv",
        t["metric_throughput"]: "output_throughput.csv",
    }

    tables = []
    for metric_name, filename in metric_files.items():
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            tables.append(f"### {metric_name}\n\n{dataframe_to_markdown(df)}\n")
        else:
            logger.warning(f"CSV file not found: {filepath}")

    return "\n".join(tables)


def copy_inference_diagram(output_dir):
    """Copy the inference diagram to the output directory."""
    # Look for inference.png in the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inference_src = os.path.join(script_dir, "inference.png")

    if os.path.exists(inference_src):
        shutil.copy(inference_src, os.path.join(output_dir, "inference.png"))
        logger.info(f"Copied inference diagram to {output_dir}")
        return True
    else:
        logger.warning(f"Inference diagram not found: {inference_src}")
        return False


def read_fixed_tokens_from_summary(results_dir):
    """Read the actual fixed input/output tokens from a summary JSON in results_dir."""
    for summary_file in glob.glob(os.path.join(results_dir, "*", "*_summary.json")):
        try:
            with open(summary_file, "r") as f:
                data = json.load(f)
            return (
                data.get("results_number_input_tokens_mean", data.get("mean_input_tokens", 0)),
                data.get("results_number_output_tokens_mean", data.get("mean_output_tokens", 0)),
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return None, None


def generate_test_config_section(use_case, preset_config, results_dir, t):
    """Generate the test configuration section content."""
    if not use_case or not preset_config:
        return ""

    # Get use case display name
    use_case_names = {
        "rag": t.get("use_case_rag", "RAG"),
        "generate": t.get("use_case_generate", "Text Generation"),
        "normal": t.get("use_case_normal", "Normal Conversation"),
    }
    use_case_display = use_case_names.get(use_case, use_case)

    # Preset range from config
    min_in = preset_config.get("min_input_tokens", 0)
    max_in = preset_config.get("max_input_tokens", 0)
    min_out = preset_config.get("min_output_tokens", 0)
    max_out = preset_config.get("max_output_tokens", 0)

    # Read actual fixed tokens used from summary JSON
    fixed_in, fixed_out = read_fixed_tokens_from_summary(results_dir)

    section = f"""## {t.get("section0_title", "Test Configuration")}

### {t.get("use_case", "Use Case")}: {use_case_display}

| {t.get("token_config", "Configuration")} | {t.get("input_tokens", "Input Tokens")} | {t.get("output_tokens", "Output Tokens")} |
|---|---|---|
| {t.get("token_range", "Preset Range")} | {min_in:,} - {max_in:,} | {min_out:,} - {max_out:,} |
| **{t.get("token_fixed", "Fixed Value")}** | **{fixed_in:,}** | **{fixed_out:,}** |

### {t.get("test_settings", "Test Settings")}

- **{t.get("cache_prevention", "Cache Prevention")}**: {t.get("cache_prevention_desc", "Enabled")}

---

"""
    return section


def generate_report(results_dir, model_name, output_dir, lang="en", use_case=None):
    """Generate performance report."""
    os.makedirs(output_dir, exist_ok=True)

    # Get translations
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    # Load preset config if use_case is provided
    preset_config = None
    if use_case:
        preset_config = load_preset_config(use_case)
        if preset_config:
            logger.info(f"Loaded preset config for use case: {use_case}")

    # Split performance chart
    logger.info("Splitting performance chart...")
    split_performance_chart(results_dir, output_dir)

    # Copy inference diagram
    logger.info("Copying inference diagram...")
    copy_inference_diagram(output_dir)

    # Load metrics data
    logger.info("Loading metrics data...")
    metrics_tables = load_metrics_data(results_dir, lang)

    # Generate markdown report
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate test configuration section
    config_section = generate_test_config_section(use_case, preset_config, results_dir, t)

    report_content = f"""# {t["title"]}: {model_name}

**{t["generated"]}:** {current_time}

---

{config_section}## {t["section1_title"]}

{t["section1_intro"]}

![Inference Metrics](inference.png)

### {t["metrics_explained"]}

- **{t["ttft_title"]}**: {t["ttft_desc"]}

- **{t["itl_title"]}**: {t["itl_desc"]}

- **{t["e2e_title"]}**: {t["e2e_desc"]}

- **{t["throughput_title"]}**: {t["throughput_desc"]}

---

## {t["section2_title"]}

{metrics_tables}

---

## {t["section3_title"]}

### {t["metric_itl"]}
![Inter-token Latency](inter_token_latency.png)

### {t["metric_e2e"]}
![End-to-End Latency](end_to_end_latency.png)

### {t["metric_ttft"]}
![Time to First Token](time_to_first_token.png)

### {t["metric_throughput"]}
![Output Throughput](output_throughput.png)

---

## {t["full_chart_title"]}

![Performance Chart](performance_chart.png)
"""

    report_path = os.path.join(output_dir, "performance_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Report saved to: {report_path}")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate performance report")
    parser.add_argument(
        "--results-dir", required=True, help="Path to the results directory with CSVs and chart"
    )
    parser.add_argument(
        "--model-name", required=True, help="Name of the model being evaluated"
    )
    parser.add_argument(
        "--output-dir", help="Output directory for the report (defaults to results-dir/report)"
    )
    parser.add_argument(
        "--language", choices=["en", "tw", "cn"], default="en",
        help="Report language: en (English), tw (Traditional Chinese), cn (Simplified Chinese)"
    )
    parser.add_argument(
        "--use-case", choices=["rag", "generate", "normal"],
        help="Use case preset name to include configuration details in the report"
    )
    args = parser.parse_args()

    results_dir = args.results_dir
    if not os.path.isabs(results_dir):
        results_dir = os.path.join(os.getcwd(), results_dir)

    output_dir = args.output_dir
    if output_dir:
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.getcwd(), output_dir)
    else:
        output_dir = os.path.join(results_dir, "report")

    if not os.path.exists(results_dir):
        logger.error(f"Results directory does not exist: {results_dir}")
        exit(1)

    report_path = generate_report(results_dir, args.model_name, output_dir, args.language, args.use_case)
    if report_path:
        print(f"\nReport generated successfully: {report_path}")
    else:
        logger.error("Failed to generate report")
        exit(1)
