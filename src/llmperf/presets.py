"""Use case preset configurations for LLM performance benchmarking."""

from pathlib import Path
from typing import Dict, Tuple

import yaml


def _load_presets() -> Dict[str, Dict[str, int]]:
    """Load presets from YAML file.

    Looks for presets.yml in the following order:
    1. Current working directory
    2. Project root (relative to this file)
    """
    config = None

    # Try current working directory first
    cwd_path = Path.cwd() / "presets.yml"
    if cwd_path.exists():
        with open(cwd_path, "r") as f:
            config = yaml.safe_load(f)

    # Try project root (3 levels up from this file: src/llmperf/presets.py -> root)
    if config is None:
        project_root = Path(__file__).parent.parent.parent / "presets.yml"
        if project_root.exists():
            with open(project_root, "r") as f:
                config = yaml.safe_load(f)

    if config is None:
        raise FileNotFoundError(
            "presets.yml not found. Please create one in the project root or current directory."
        )

    # Extract presets from the config (supports both nested and flat structure)
    if "presets" in config:
        return config["presets"]
    return config


USE_CASE_PRESETS: Dict[str, Dict[str, int]] = _load_presets()


def get_preset(name: str) -> Dict[str, int]:
    """Get a preset configuration by name.

    Args:
        name: The preset name (rag, generate, or normal).

    Returns:
        The preset configuration dictionary.

    Raises:
        ValueError: If the preset name is not recognized.
    """
    if name not in USE_CASE_PRESETS:
        available = list(USE_CASE_PRESETS.keys())
        raise ValueError(f"Unknown preset: {name}. Available presets: {available}")
    return USE_CASE_PRESETS[name]


def calculate_mean_stddev(min_val: int, max_val: int) -> Tuple[int, int]:
    """Convert min/max range to mean/stddev for Gaussian sampling.

    Uses ~2 standard deviations to cover most of the range,
    ensuring samples fall within [min_val, max_val] approximately 95% of the time.

    Args:
        min_val: Minimum value of the range.
        max_val: Maximum value of the range.

    Returns:
        Tuple of (mean, stddev).
    """
    mean = (min_val + max_val) // 2
    # Using range/4 gives ~2 stddev coverage
    stddev = (max_val - min_val) // 4
    return mean, max(stddev, 1)  # Ensure stddev is at least 1


def get_preset_params(name: str) -> Tuple[int, int, int, int]:
    """Get mean/stddev parameters for a preset.

    Args:
        name: The preset name.

    Returns:
        Tuple of (mean_input_tokens, stddev_input_tokens,
                  mean_output_tokens, stddev_output_tokens).
    """
    preset = get_preset(name)
    mean_input, stddev_input = calculate_mean_stddev(
        preset["min_input_tokens"], preset["max_input_tokens"]
    )
    mean_output, stddev_output = calculate_mean_stddev(
        preset["min_output_tokens"], preset["max_output_tokens"]
    )
    return mean_input, stddev_input, mean_output, stddev_output
