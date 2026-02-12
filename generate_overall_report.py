import argparse
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


# Multi-language support
TRANSLATIONS = {
    "en": {
        "title": "Performance Report",
        "generated": "Generated",
        "metrics_title": "Metrics Description",
        "metrics_intro": "The following diagram illustrates the key performance metrics measured during LLM inference:",
        "metrics_explained": "Key Metrics Explained",
        "ttft_title": "Time to First Token (TTFT)",
        "ttft_desc": "The time elapsed from when the query is sent until the first token is received. This measures the initial response latency and is critical for user-perceived responsiveness.",
        "itl_title": "Inter-token Latency (ITL)",
        "itl_desc": "The time between consecutive tokens during generation. Lower ITL means smoother streaming output and better user experience during text generation.",
        "e2e_title": "End-to-End Latency",
        "e2e_desc": "The total time from sending the query to receiving the complete response. This includes TTFT plus the entire generation time.",
        "throughput_title": "Output Throughput",
        "throughput_desc": "The number of tokens generated per second. Higher throughput indicates better generation efficiency.",
        "use_case_section": "Use Case",
        "test_config": "Test Configuration",
        "performance_metrics": "Performance Metrics",
        "performance_charts": "Performance Charts",
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
        "metric_e2e": "End-to-End Latency (seconds)",
        "metric_itl": "Inter-token Latency (seconds)",
        "metric_ttft": "Time to First Token (seconds)",
        "metric_throughput": "Output Throughput (tokens/s)",
        "full_chart_title": "Full Performance Chart",
    },
    "tw": {
        "title": "效能報告",
        "generated": "產生時間",
        "metrics_title": "指標說明",
        "metrics_intro": "以下圖表說明 LLM 推論過程中測量的關鍵效能指標：",
        "metrics_explained": "關鍵指標說明",
        "ttft_title": "首 Token 延遲 (TTFT)",
        "ttft_desc": "從發送查詢到收到第一個 token 所經過的時間。此指標衡量初始回應延遲，對於使用者感知的回應性至關重要。",
        "itl_title": "Token 間延遲 (ITL)",
        "itl_desc": "生成過程中連續 token 之間的時間間隔。較低的 ITL 意味著更流暢的串流輸出和更好的文字生成使用者體驗。",
        "e2e_title": "端到端延遲",
        "e2e_desc": "從發送查詢到收到完整回應的總時間。這包括 TTFT 加上整個生成時間。",
        "throughput_title": "輸出吞吐量",
        "throughput_desc": "每秒生成的 token 數量。較高的吞吐量表示更好的生成效率。",
        "use_case_section": "使用案例",
        "test_config": "測試配置",
        "performance_metrics": "效能測試指標",
        "performance_charts": "效能視覺化",
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
        "metric_e2e": "端到端延遲（秒）",
        "metric_itl": "Token 間延遲（秒）",
        "metric_ttft": "首 Token 延遲（秒）",
        "metric_throughput": "輸出吞吐量（tokens/s）",
        "full_chart_title": "完整效能圖表",
    },
    "cn": {
        "title": "性能报告",
        "generated": "生成时间",
        "metrics_title": "指标说明",
        "metrics_intro": "以下图表说明 LLM 推理过程中测量的关键性能指标：",
        "metrics_explained": "关键指标说明",
        "ttft_title": "首 Token 延迟 (TTFT)",
        "ttft_desc": "从发送查询到收到第一个 token 所经过的时间。此指标衡量初始响应延迟，对于用户感知的响应性至关重要。",
        "itl_title": "Token 间延迟 (ITL)",
        "itl_desc": "生成过程中连续 token 之间的时间间隔。较低的 ITL 意味着更流畅的流式输出和更好的文本生成用户体验。",
        "e2e_title": "端到端延迟",
        "e2e_desc": "从发送查询到收到完整响应的总时间。这包括 TTFT 加上整个生成时间。",
        "throughput_title": "输出吞吐量",
        "throughput_desc": "每秒生成的 token 数量。较高的吞吐量表示更好的生成效率。",
        "use_case_section": "使用案例",
        "test_config": "测试配置",
        "performance_metrics": "性能测试指标",
        "performance_charts": "性能可视化",
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
        "metric_e2e": "端到端延迟（秒）",
        "metric_itl": "Token 间延迟（秒）",
        "metric_ttft": "首 Token 延迟（秒）",
        "metric_throughput": "输出吞吐量（tokens/s）",
        "full_chart_title": "完整性能图表",
    },
}


def load_presets_config():
    """Load all presets from presets.yml."""
    config_paths = [
        os.path.join(os.getcwd(), "presets.yml"),
        os.path.join(os.path.dirname(__file__), "presets.yml"),
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            return config.get("presets", {})
    return {}


def dataframe_to_markdown(df):
    """Convert a DataFrame to markdown table."""
    headers = df.columns.tolist()
    header_row = "| " + " | ".join(str(h) for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"

    rows = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(v) for v in row.values) + " |"
        rows.append(row_str)

    return "\n".join([header_row, separator] + rows)


def load_metrics_data(results_dir, t):
    """Load CSV metrics data and return as formatted markdown tables."""
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
            tables.append(f"#### {metric_name}\n\n{dataframe_to_markdown(df)}\n")
        else:
            logger.warning(f"CSV file not found: {filepath}")

    return "\n".join(tables)


def copy_inference_diagram(output_dir):
    """Copy the inference diagram to the output directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inference_src = os.path.join(script_dir, "inference.png")

    if os.path.exists(inference_src):
        shutil.copy(inference_src, os.path.join(output_dir, "inference.png"))
        logger.info(f"Copied inference diagram to {output_dir}")
        return True
    else:
        logger.warning(f"Inference diagram not found: {inference_src}")
        return False


def split_and_copy_charts(results_dir, output_dir, use_case):
    """Split the 2x2 performance chart and copy to output directory with use_case prefix."""
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
        (0, 0, half_width, half_height),
        (half_width, 0, width, half_height),
        (0, half_height, half_width, height),
        (half_width, half_height, width, height),
    ]

    for i, box in enumerate(boxes):
        part = img.crop(box)
        output_path = os.path.join(output_dir, f"{use_case}_{mapping[i]}.png")
        part.save(output_path)
        logger.info(f"Saved: {output_path}")

    # Copy full chart
    shutil.copy(chart_path, os.path.join(output_dir, f"{use_case}_performance_chart.png"))
    return True


def generate_metrics_description_section(t):
    """Generate the metrics description section (appears once at top)."""
    return f"""## 1. {t["metrics_title"]}

{t["metrics_intro"]}

![Inference Metrics](inference.png)

### {t["metrics_explained"]}

- **{t["ttft_title"]}**: {t["ttft_desc"]}

- **{t["itl_title"]}**: {t["itl_desc"]}

- **{t["e2e_title"]}**: {t["e2e_desc"]}

- **{t["throughput_title"]}**: {t["throughput_desc"]}

---

"""


def read_fixed_tokens_from_summary(results_dir):
    """Read the actual fixed input/output tokens from a summary JSON in results_dir."""
    import glob
    for summary_file in glob.glob(os.path.join(results_dir, "*", "*_summary.json")):
        try:
            with open(summary_file, "r") as f:
                data = json.load(f)
            return data.get("mean_input_tokens", 0), data.get("mean_output_tokens", 0)
        except (json.JSONDecodeError, KeyError):
            continue
    return None, None


def generate_use_case_section(use_case, preset_config, results_dir, output_dir, section_num, t):
    """Generate a section for one use case."""
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

    # Split and copy charts for this use case
    split_and_copy_charts(results_dir, output_dir, use_case)

    # Load metrics tables
    metrics_tables = load_metrics_data(results_dir, t)

    section = f"""## {section_num}. {t["use_case_section"]}: {use_case_display}

### {t["test_config"]}

| {t["token_config"]} | {t["input_tokens"]} | {t["output_tokens"]} |
|---|---|---|
| {t["token_range"]} | {min_in:,} - {max_in:,} | {min_out:,} - {max_out:,} |
| **{t["token_fixed"]}** | **{fixed_in:,}** | **{fixed_out:,}** |

- **{t["cache_prevention"]}**: {t["cache_prevention_desc"]}

### {t["performance_metrics"]}

{metrics_tables}

### {t["performance_charts"]}

#### {t["metric_itl"]}
![Inter-token Latency]({use_case}_inter_token_latency.png)

#### {t["metric_e2e"]}
![End-to-End Latency]({use_case}_end_to_end_latency.png)

#### {t["metric_ttft"]}
![Time to First Token]({use_case}_time_to_first_token.png)

#### {t["metric_throughput"]}
![Output Throughput]({use_case}_output_throughput.png)

#### {t["full_chart_title"]}
![Performance Chart]({use_case}_performance_chart.png)

---

"""
    return section


def generate_overall_report(base_results_dir, model_name, output_dir, lang="en"):
    """Generate a single overall report combining all use cases."""
    os.makedirs(output_dir, exist_ok=True)

    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    presets = load_presets_config()

    # Copy inference diagram
    copy_inference_diagram(output_dir)

    # Generate report header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"""# {t["title"]}: {model_name}

**{t["generated"]}:** {current_time}

---

"""

    # Add metrics description section (only once)
    report_content += generate_metrics_description_section(t)

    # Find and iterate through all use cases that have results
    section_num = 2
    for use_case in presets.keys():
        use_case_dir = os.path.join(base_results_dir, use_case, "raw_data", "performance")
        if os.path.exists(use_case_dir):
            logger.info(f"Processing use case: {use_case}")
            preset_config = presets[use_case]
            report_content += generate_use_case_section(
                use_case, preset_config, use_case_dir, output_dir, section_num, t
            )
            section_num += 1
        else:
            logger.warning(f"Results not found for use case: {use_case} at {use_case_dir}")

    # Write report
    report_path = os.path.join(output_dir, "performance_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Overall report saved to: {report_path}")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate overall performance report")
    parser.add_argument(
        "--results-dir", required=True,
        help="Base results directory containing all use case subdirectories"
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

    report_path = generate_overall_report(results_dir, args.model_name, output_dir, args.language)
    if report_path:
        print(f"\nOverall report generated successfully: {report_path}")
    else:
        logger.error("Failed to generate report")
        exit(1)
