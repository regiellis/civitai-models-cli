# -*- coding: utf-8 -*-

"""
==========================================================
Civitai Model Manager - Helpers
==========================================================

This module contains helper functions for the Civitai Model Manager.

"""
import os
import sys
import json
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from rich import print
from rich.table import Table
from rich.traceback import install
install()

console = Console(soft_wrap=True)


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


def feedback_message(message: str, type: str = "info") -> None:
    """_summary_

    Args:
        message (str): _description_
        type (str, optional): _description_. Defaults to "info".

    Returns:
        _type_: _description_
    """
    options = {
        "types": {
            "info": "green",
            "warning": "yellow",
            "error": "red",
        },
        "titles": {
            "info": "Information",
            "warning": "Warning",
            "error": "Error Message",
        }
    }

    feedback_message_table = Table(style=options["types"][type])
    feedback_message_table.add_column(options["titles"][type])
    feedback_message_table.add_row(message)
    console.print(feedback_message_table)
    return None

