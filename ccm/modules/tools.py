# -*- coding: utf-8 -*-

"""
==========================================================
Civitai CLI Manager - Tools
==========================================================

This module contains tools functions for the Civitai Model Manager.

"""

import os
from pathlib import Path
import requests
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from rich.table import Table
from tqdm import tqdm
import time

from ollama import Client as OllamaClient
from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient

# TODO: Centralize the options in a single place
OLLAMA_OPTIONS: Final = {
    "model": os.getenv("OLLAMA_MODEL", ""),
    "api_base": os.getenv("OLLAMA_API_BASE", "")
}

OPENAI_OPTIONS = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", ""),
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
}

GROQ_OPTIONS = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", ""),
}

Ollama = OllamaClient(OLLAMA_OPTIONS["api_base"]) if OLLAMA_OPTIONS["api_base"] else None
OpenAI = OpenAIClient(api_key=OPENAI_OPTIONS["api_key"]) if OPENAI_OPTIONS["api_key"] else None
Groq = GroqClient(api_key=GROQ_OPTIONS["api_key"]) if GROQ_OPTIONS["api_key"] else None



console = Console()

def check_models_dir() -> Dict[str, Any]:
    """_summary_

    Returns:
        Dict[str, Any]: _description_
    """
    models_dir = os.environ.get("MODELS_DIR")
    if not models_dir:
        return {"status": False, "message": "MODELS_DIR environment variable not set"}
    
    path = Path(models_dir)
    if not path.exists():
        return {"status": False, "message": f"Directory {models_dir} does not exist"}
    
    if not os.access(path, os.W_OK):
        return {"status": False, "message": f"No write permission for {models_dir}"}
    
    return {"status": True, "message": "Models directory check passed"}


def check_civitai_token() -> Dict[str, Any]:
    """_summary_

    Returns:
        Dict[str, Any]: _description_
    """
    token = os.environ.get("CIVITAI_TOKEN")
    if not token:
        return {"status": False, "message": "CIVITAI_TOKEN environment variable not set"}
    return {"status": True, "message": "CivitAI token check passed"}


def check_api_availability() -> Dict[str, Any]:
    """_summary_

    Returns:
        Dict[str, Any]: _description_
    """
    civitai_models_url = os.environ.get("CIVITAI_MODELS", "https://civitai.com/api/v1/models")
    try:
        response = requests.get(civitai_models_url, timeout=10)
        if response.status_code == 200:
            return {"status": True, "message": "API is accessible"}
        else:
            return {"status": False, "message": f"API returned status code {response.status_code}"}
    except requests.RequestException as e:
        return {"status": False, "message": f"Failed to connect to API: {str(e)}"}


def check_ollama() -> Dict[str, Any]:
    """_summary_

    Returns:
        Dict[str, Any]: _description_
    """
    try:
        response = Ollama.chat(
            model=OLLAMA_OPTIONS["model"],
            messages=[
                {"role": "user", "content": "What is your purpose?"},
            ],
            keep_alive=0 # Free up the VRAM
        )
        print(response)
        return {"status": True, "message": "Ollama is accessible"}
    except Exception as e:
        return {"status": False, "message": f"Failed to connect to Ollama: {str(e)}"}


def check_openai() -> Dict[str, Any]:
    """_summary_

    Returns:
        Dict[str, Any]: _description_
    """
    
    request = OpenAI.chat.completions.create(
        model=OPENAI_OPTIONS["model"],
        messages=[
            {"role": "system", "content": "You are a chatbot."},
            {"role": "user", "content": "What is your purpose?"},
        ])
    return {"status": True, "message": "OpenAI is accessible"}


def sanity_check_cli() -> None:
    CHECKS = {
        "REQUIRED": {
            "MODELS_DIR": check_models_dir,
            "CIVITAI_TOKEN": check_civitai_token,
            "API_AVAILABILITY": check_api_availability,
        },
        "OPTIONAL": {
            #"OLLAMA": check_ollama,
            # "OPENAI": check_openai,
        }
    }

    results = {}
    
    with tqdm(total=len(CHECKS["REQUIRED"]), bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', 
              desc="Running sanity checks", colour="yellow") as pbar:
        for check, func in CHECKS["REQUIRED"].items():
            results[check] = func()
            pbar.update(1)
            time.sleep(0.5)  
            
    if CHECKS["OPTIONAL"] is {}:
        with tqdm(total=len(CHECKS["OPTIONAL"]), bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', 
                desc="Running optional sanity checks", colour="yellow") as pbar:
            for check, func in CHECKS["OPTIONAL"].items():
                if func is not None:
                    results[check] = func()
                    pbar.update(1)
                    time.sleep(0.5)

    sanity_table = Table()
    sanity_table.add_column("Check", style="cyan")
    sanity_table.add_column("Status", style="bright_yellow")
    sanity_table.add_column("Message", style="bright_yellow")

    for check, result in results.items():
        status = "Pass" if result["status"] else "Fail"
        style = "green" if result["status"] else "bright_red"
        message = result["message"]
        sanity_table.add_row(check, status, message, style=style)

    console.print(sanity_table)
