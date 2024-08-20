"""
==========================================================
Civitai CLI Manager - UTILS
==========================================================

This module contains utility functions for the Civitai Model Manager.

"""

import os
import sys
import json
import math

import humanize

from urllib.parse import urlparse, urlunparse, quote
from typing import List, Tuple, Dict, Optional

def clean_text(text: str) -> str:
    """Cleans text by removing special characters."""
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()


def format_file_size(size_bytes) -> str:
    """Converts file size in bytes to human-readable format."""
    # Convert bytes to megabytes
    size_in_mb = size_bytes / (1024 * 1024)
    size_in_gb = size_bytes / (1024 * 1024 * 1024)
    

    return f"{size_in_mb:.2f} MB ({size_in_gb:.2f} GB)" if size_in_gb >= 1 else f"{size_in_mb:.2f} MB"


def convert_kb(kb: float) -> str:
    """Converts KB to human-readable format."""
    if kb <= 0:
        raise ValueError("Input must be a positive number.")
    units = ["KB", "MB", "GB", "TB"]
    i = 0
    while kb >= 1024 and i < len(units) - 1: 
        kb /= 1024.0  
        i += 1

    return f"{round(kb, 2)} {units[i]}"


def safe_get(collection, keys, default=None):
    """_summary_

    Args:
        collection (_type_): _description_
        keys (_type_): _description_
        default (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    for key in keys:
        try:
            collection = collection[key]
        except (KeyError, IndexError, TypeError):
            return default
    return collection


def safe_url(url: str) -> str:
    parts = urlparse(url)
    return urlunparse(parts._replace(path=quote(parts.path)))


def sort_models(models: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Sort models by name."""
    return sorted(models, key=lambda x: x[0])