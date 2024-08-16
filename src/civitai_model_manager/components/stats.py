# -*- coding: utf-8 -*-

"""
==========================================================
Civitai CLI Manager - Stats
==========================================================

This module contains functions for generating statistics for the Civitai Model Manager.

"""

import os
import json
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from rich.table import Table

from .helpers import feedback_message

FILE_TYPES = (".safetensors", ".pt", ".pth", ".ckpt")

stats_console = Console(soft_wrap=True)

def count_models(model_dir: str) -> Dict[str, int]:
    model_counts = {}
    for root, _, files in os.walk(model_dir):
        # Get the top-level directory name
        top_level_dir = os.path.relpath(root, model_dir).split(os.sep)[0]
        for file in files:
            if file.endswith(FILE_TYPES):
                #print(f"Found model file: {file} in directory: {root}")  Debugging statement
                if top_level_dir in model_counts:
                    model_counts[top_level_dir] += 1
                else:
                    model_counts[top_level_dir] = 1
    return model_counts

def get_model_sizes(model_dir: str) -> Dict[str, str]:
    model_sizes = {}
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith(FILE_TYPES):
                model_path = os.path.join(root, file)
                size_in_bytes = os.path.getsize(model_path)
                size_in_mb = size_in_bytes / (1024 * 1024)
                size_in_gb = size_in_bytes / (1024 * 1024 * 1024)

                size_str = f"{size_in_mb:.2f} MB ({size_in_gb:.2f} GB)" if size_in_gb >= 1 else f"{size_in_mb:.2f} MB"

                model_name = os.path.basename(file)
                model_sizes[model_name] = size_str
    return model_sizes


# find model by file name on disk and return the path
def find_model_by_name(model_dir: str, model_name: str) -> Optional[str]:
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file == model_name:
                return os.path.join(root, file)
    return None


def inspect_models_cli(MODELS_DIR: str) -> None:
    """Stats on the parent models directory."""
    model_counts = count_models(MODELS_DIR)

    if not model_counts:
        feedback_message("No models found.", "warning")
        return table

    total_count = sum(model_counts.values())

    table = Table(title_justify="left")
    table.add_column("Model Type", style="cyan")
    table.add_column("Model Per Directory ", style="bright_yellow")
    table.add_column("Model Type Paths", style="bright_yellow")
    table.add_column("Model Path", style="bright_yellow")
    table.add_column(f"Model Breakdown // Total Model Count: {total_count}", style="bright_yellow")
            
    for model_type, count in model_counts.items():
        base_path = os.path.join(MODELS_DIR, model_type)
        path_types = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        
        if not path_types:
            path_types_breakdown = "[white]No subdirectories[/white]"
        else:
            subdir_counts = {}
            total_subdir_files = 0
            for subdir in path_types:
                subdir_path = os.path.join(base_path, subdir)
                file_count = len([f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))])
                subdir_counts[subdir] = file_count
                total_subdir_files += file_count
            
            breakdown_parts = []
            for subdir, subdir_count in subdir_counts.items():
                percentage = subdir_count / total_subdir_files if total_subdir_files > 0 else 0
                breakdown_parts.append(f"[white]{subdir}:[/white] [bold]{subdir_count} ({percentage:.2%})[/bold]")
            
            path_types_breakdown = f"{', '.join(breakdown_parts)} (Total: {total_subdir_files})"

        table.add_row(
            model_type,
            f"{count}",
            f"[bright_yellow]{path_types_breakdown}[/bright_yellow]",
            os.path.join(MODELS_DIR, model_type),
            f"{count/total_count:.2%}"
        )

    stats_console.print(table)

    # Get top 10 largest models
    model_sizes = get_model_sizes(MODELS_DIR)
    

    table = Table(title_justify="left")
    table.add_column("Top 10 Largest Models // Model Name", style="cyan")
    table.add_column("Size on Disk", style="bright_yellow")
    table.add_column("Model Path", style="bright_yellow")

    for model_name, size in sorted(model_sizes.items(), key=lambda x: float(x[1].split()[0]), reverse=True)[:10]:
        table.add_row(model_name, size, find_model_by_name(MODELS_DIR, model_name))

    stats_console.print(table)