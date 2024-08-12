"""
==========================================================
Civitai CLI Manager - UTILS
==========================================================

This module contains utility functions for the Civitai Model Manager.

"""

import os
import sys
import json


def clean_text(text: str) -> str:
    """_summary_

    Args:
        text (str): _description_

    Returns:
        str: _description_
    """
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()


def convert_kb(kb: float) -> str:
    """_summary_

    Args:
        kb (float): _description_

    Raises:
        ValueError: _description_

    Returns:
        str: _description_
    """
    if kb <= 0:
        raise ValueError("Input must be a positive number.")
    units = ["KB", "MB", "GB"]
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