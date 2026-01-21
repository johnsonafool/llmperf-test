import argparse
import csv
import json
import logging
import os
import re

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

sns.set_style("whitegrid")
sns.set_palette("husl")


def convert_to_percentile(data_dict, percentile_index=1):
    """
    Convert the data dictionary to a specific percentile and sort by keys.

    :param data_dict: Dictionary with concurrent users as keys and lists of percentiles as values
    :param percentile_index: Index of the percentile to use (0 for p90, 1 for p95, 2 for p99)
    :return: Sorted dictionary based on keys
    """
    sorted_dict = dict(sorted(data_dict.items()))

    percentile_data = {
        concurrent_users: percentiles[percentile_index]
        for concurrent_users, percentiles in sorted_dict.items()
    }

    return list(percentile_data.values())


def generate_charts(results_dir):
    store = {}
    store2 = {}
    store3 = {}
    store4 = {}

    # Iterate through results directory
    for root, dirs, files in os.walk(results_dir):
        for file_name in files:
            match = re.search(r"(_summary)", file_name)

            if match:
                file_path = os.path.join(root, file_name)

                with open(file_path, "r") as file:
                    data = json.load(file)
                    concurrent_user = int(root.split("/")[-1])

                    # Extract p25, p50, p75
                    store[concurrent_user] = [
                        data["results_inter_token_latency_s_quantiles_p25"],
                        data["results_inter_token_latency_s_quantiles_p50"],
                        data["results_inter_token_latency_s_quantiles_p75"],
                    ]
                    store2[concurrent_user] = [
                        data["results_end_to_end_latency_s_quantiles_p25"],
                        data["results_end_to_end_latency_s_quantiles_p50"],
                        data["results_end_to_end_latency_s_quantiles_p75"],
                    ]
                    store3[concurrent_user] = [
                        data["results_ttft_s_quantiles_p25"],
                        data["results_ttft_s_quantiles_p50"],
                        data["results_ttft_s_quantiles_p75"],
                    ]
                    store4[concurrent_user] = [
                        data[
                            "results_request_output_throughput_token_per_s_quantiles_p25"
                        ],
                        data[
                            "results_request_output_throughput_token_per_s_quantiles_p50"
                        ],
                        data[
                            "results_request_output_throughput_token_per_s_quantiles_p75"
                        ],
                    ]

    x = np.array(sorted(store.keys()))

    # ITL
    p25_sorted = convert_to_percentile(store, percentile_index=0)
    p50_sorted = convert_to_percentile(store, percentile_index=1)
    p75_sorted = convert_to_percentile(store, percentile_index=2)

    # End-to-End Latency
    e2e_p25_sorted = convert_to_percentile(store2, percentile_index=0)
    e2e_p50_sorted = convert_to_percentile(store2, percentile_index=1)
    e2e_p75_sorted = convert_to_percentile(store2, percentile_index=2)

    # Time to First Token
    ttft_p25_sorted = convert_to_percentile(store3, percentile_index=0)
    ttft_p50_sorted = convert_to_percentile(store3, percentile_index=1)
    ttft_p75_sorted = convert_to_percentile(store3, percentile_index=2)

    # Tokens per Second (Throughput)
    tps_p25_sorted = convert_to_percentile(store4, percentile_index=0)
    tps_p50_sorted = convert_to_percentile(store4, percentile_index=1)
    tps_p75_sorted = convert_to_percentile(store4, percentile_index=2)

    # Write data to CSV files
    csv_data = {
        "inter_token_latency.csv": {
            "headers": ["Concurrent_Users", "P25", "P50", "P75"],
            "data": list(zip(x, p25_sorted, p50_sorted, p75_sorted)),
        },
        "end_to_end_latency.csv": {
            "headers": ["Concurrent_Users", "P25", "P50", "P75"],
            "data": list(zip(x, e2e_p25_sorted, e2e_p50_sorted, e2e_p75_sorted)),
        },
        "time_to_first_token.csv": {
            "headers": ["Concurrent_Users", "P25", "P50", "P75"],
            "data": list(zip(x, ttft_p25_sorted, ttft_p50_sorted, ttft_p75_sorted)),
        },
        "output_throughput.csv": {
            "headers": ["Concurrent_Users", "P25", "P50", "P75"],
            "data": list(zip(x, tps_p25_sorted, tps_p50_sorted, tps_p75_sorted)),
        },
    }

    for filename, csv_info in csv_data.items():
        csv_path = os.path.join(results_dir, filename)
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_info["headers"])
            writer.writerows(csv_info["data"])
        logger.info(f"CSV data saved to {csv_path}")

    # Creating the figure and subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.tight_layout(pad=6.0)
    line_properties = {"linewidth": 2.5, "alpha": 0.85, "marker": "o", "markersize": 8}
    colors = ["#2E86AB", "#A23B72", "#F18F01"]

    # Inter-token Latency
    axes[0, 0].plot(x, p75_sorted, label="p75", color=colors[0], **line_properties)
    axes[0, 0].plot(x, p50_sorted, label="p50", color=colors[1], **line_properties)
    axes[0, 0].plot(x, p25_sorted, label="p25", color=colors[2], **line_properties)
    axes[0, 0].set_title("Inter-token Latency (seconds)", fontsize=14)
    axes[0, 0].set_xlabel("Concurrent Users", fontsize=12)
    axes[0, 0].set_ylabel("Seconds", fontsize=12)
    axes[0, 0].set_xticks(x)
    axes[0, 0].tick_params(axis="both", labelsize=10)
    axes[0, 0].legend(fontsize=10)
    axes[0, 0].grid(True)

    # End-to-End Latency
    axes[0, 1].plot(x, e2e_p75_sorted, label="p75", color=colors[0], **line_properties)
    axes[0, 1].plot(x, e2e_p50_sorted, label="p50", color=colors[1], **line_properties)
    axes[0, 1].plot(x, e2e_p25_sorted, label="p25", color=colors[2], **line_properties)
    axes[0, 1].set_title("End-to-End Latency (seconds)", fontsize=14)
    axes[0, 1].set_xlabel("Concurrent Users", fontsize=12)
    axes[0, 1].set_ylabel("Seconds", fontsize=12)
    axes[0, 1].set_xticks(x)
    axes[0, 1].tick_params(axis="both", labelsize=10)
    axes[0, 1].legend(fontsize=10)
    axes[0, 1].grid(True)

    # Time to First Token
    axes[1, 0].plot(x, ttft_p75_sorted, label="p75", color=colors[0], **line_properties)
    axes[1, 0].plot(x, ttft_p50_sorted, label="p50", color=colors[1], **line_properties)
    axes[1, 0].plot(x, ttft_p25_sorted, label="p25", color=colors[2], **line_properties)
    axes[1, 0].set_title("Time to First Token (seconds)", fontsize=14)
    axes[1, 0].set_xlabel("Concurrent Users", fontsize=12)
    axes[1, 0].set_ylabel("Seconds", fontsize=12)
    axes[1, 0].set_xticks(x)
    axes[1, 0].tick_params(axis="both", labelsize=10)
    axes[1, 0].legend(fontsize=10)
    axes[1, 0].grid(True)

    # Output Throughput
    axes[1, 1].plot(x, tps_p75_sorted, label="p75", color=colors[0], **line_properties)
    axes[1, 1].plot(x, tps_p50_sorted, label="p50", color=colors[1], **line_properties)
    axes[1, 1].plot(x, tps_p25_sorted, label="p25", color=colors[2], **line_properties)
    axes[1, 1].set_title("Output Throughput (tokens/s)", fontsize=14)
    axes[1, 1].set_xlabel("Concurrent Users", fontsize=12)
    axes[1, 1].set_ylabel("Tokens per second", fontsize=12)
    axes[1, 1].set_xticks(x)
    axes[1, 1].tick_params(axis="both", labelsize=10)
    axes[1, 1].legend(fontsize=10)
    axes[1, 1].grid(True)

    plt.savefig(
        os.path.join(results_dir, "performance_chart.png"),
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    logger.info(f"Chart saved to {os.path.join(results_dir, 'performance_chart.png')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate charts from benchmark results."
    )
    parser.add_argument(
        "--results-dir", required=True, help="Path to the results directory."
    )
    args = parser.parse_args()

    # Handle both relative and absolute paths
    results_dir = args.results_dir
    if not os.path.isabs(results_dir):
        results_dir = os.path.join(os.getcwd(), results_dir)

    if os.path.exists(results_dir):
        generate_charts(results_dir)
    else:
        logger.error(f"Results directory does not exist: {results_dir}")
        logger.error(f"Current working directory: {os.getcwd()}")
        exit(1)
