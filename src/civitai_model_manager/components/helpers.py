# -*- coding: utf-8 -*-

"""
==========================================================
Civitai CLI Manager - Helpers
==========================================================

This module contains helper functions for the Civitai Model Manager.

"""
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from rich import print
from rich.table import Table

console = Console(soft_wrap=True)


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

