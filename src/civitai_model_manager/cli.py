"""
==========================================================
Civitai Model Manager - Simplified Model Retrieval
==========================================================

Simple CLI tool that streamlines the process of managing AI models from the
CivitAI platform. It offers functionalities to list available models,
view their details, search, download selected variants, and remove models from
local storage. It also provides a summary of the model description using
Ollama or OpenAI.

Usage:
$ pipx install civitai-model-manager or pip install civitai-model-manager
$ pip install . or pipx install . # To install the package locally
$ civitai-model-manager [OPTIONS] [COMMAND] [ARGS]

Options:
  list               List available models along with their types and paths.
  stats              Stats on the parent models directory.
  details INT        Get detailed information about a specific model by ID.
  download INT       Download a specific model variant by ID.
  remove             Remove specified models from local storage.
  explain INT        Get a summary of a specific model by ID using Ollama/OpenAI/Groq.
  --help             Show this message and exit.

Examples:

$ civitai-cli-manager --list
$ civitai-cli-manager --stats
$ civitai-cli-manager --details 12345 [--desc] [--images]
$ civitai-cli-manager --download 54321 [--select]
$ civitai-cli-manager --remove
$ civitai-cli-manager --explain 12345 [--service ollama]
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer",
#   "rich",
#   "requests",
#   "shellingham",
#   "html2text",
#   "tqdm",
#   "inquirer",
#   "civitai",
#   "python-dotenv",
#   "ollama",
#   "openai",
#   "groq"
# ]
# ///

import os
import sys
import json
import re

from typing import Any, Dict, List, Optional, Tuple, Final
import requests
import typer
import html2text
import inquirer

from platform import system
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm
from rich.console import Console
from rich import print
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.traceback import install
install()

from .components.helpers import feedback_message, get_model_folder
from .components.tools import sanity_check_cli
from .components.utils import convert_kb, clean_text, safe_get
from .components.stats import inspect_models_cli
from .components.details import get_model_details_cli, get_model_details
from .components.list import list_models_cli, list_models
from .components.download import download_model_cli, select_version

from ollama import Client as OllamaClient
from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient

from civitai import models, tags

# TODO: At some point refactor everything into separate modules and classes
# TODO: Remove the civitai dependency and use the API directly

def load_environment_variables(console: Console = Console()) -> None:
    """
    Load environment variables from .env file.
    
    If the file is not found in the default location, it will be searched in the current directory.
    If still not found, a warning message will be printed to create the file using the sample.env provided.
    """
    env_paths = {
        "Windows": os.path.join(os.path.expanduser("~"), ".env"),
        "Linux": os.path.join(os.path.expanduser("~"), ".config", "civitai-model-manager", ".env"),
        "Darwin": os.path.join(os.path.expanduser("~"), ".config", "civitai-model-manager", ".env")
    }
    
    system_platform = system()
    dotenv_path = env_paths.get(system_platform, ".env")
    
    for path in [Path(dotenv_path), Path(".env")]:
        if path.exists():
            load_dotenv(str(path))
            return
    
    feedback_message(".env file is missing. Please create one using the sample.env provided.", "warning")

load_environment_variables(Console())
MODELS_DIR: Final = os.getenv("MODELS_DIR", "")
CIVITAI_TOKEN: Final = os.getenv("CIVITAI_TOKEN", "")

CIVITAI_MODELS: Final = "https://civitai.com/api/v1/models"
CIVITAI_IMAGES: Final = "https://civitai.com/api/v1/images"
CIVITAI_VERSIONS: Final = "https://civitai.com/api/v1/model-versions"
CIVITAI_DOWNLOAD: Final = "https://civitai.com/api/download/models"

TYPES: Final = {
    "Checkpoint": "checkpoints",
    "TextualInversion": "embeddings",
    "Hypernetwork": "hypernetworks",
    "AestheticGradient": "aesthetic_embeddings",
    "LORA": "loras",
    "LoCon": "models/Lora",
    "Controlnet": "controlnet",
    "Poses": "poses",
    "Upscaler": "esrgan",
    "MotionModule": "motion_module",
    "VAE": "VAE",
    "Wildcards": "wildcards",
    "Workflows": "workflows",
    "Other": "other"
}

FILE_TYPES = (".safetensors", ".pt", ".pth", ".ckpt")
MODEL_TYPES: Final = ["SDXL 1.0", "SDXL 0.9", "SD 1.5", "SD 1.4", "SD 2.0", "SD 2.0 768", "SD 2.1", "SD 2.1 768", "Other"]

OLLAMA_OPTIONS: Final = {
    "model": os.getenv("OLLAMA_MODEL", ""),
    "api_base": os.getenv("OLLAMA_API_BASE", ""),
    "temperature": os.getenv("TEMP", 0.9),
    "top_p": os.getenv("TOP_P", 0.3),
    "html_output": os.getenv("HTML_OUT", False),
    "system_template": (
        "You are an expert in giving detailed explanations of description you are provided. Do not present it "
        "like an update log. Make sure to explains the full description in a clear and concise manner. "
        "The description is provided by the CivitAI API and not written by the user, so don't make recommendations "
        "on how to improve the description, just be detailed, clear and thorough about the provided content. "
        "Include information on recommended settings and tip if they appear in the description:\n "
        "- Tips on Usage\n"
        "- Sampling method\n"
        "- Schedule type\n"
        "- Sampling steps\n"
        "- CFG Scale\n"
        "DO NOT OFFER ADVICE ON HOW TO IMPROVE THE DESCRIPTION!!"
        "Return the description in Markdown format.\n\n"
        "You will find the description below: \n\n"
    )
}

OPENAI_OPTIONS = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"]
}

GROQ_OPTIONS = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"]
}


Ollama = OllamaClient(OLLAMA_OPTIONS["api_base"]) if OLLAMA_OPTIONS["api_base"] else None
OpenAI = OpenAIClient(api_key=OPENAI_OPTIONS["api_key"]) if OPENAI_OPTIONS["api_key"] else None
Groq = GroqClient(api_key=GROQ_OPTIONS["api_key"]) if GROQ_OPTIONS["api_key"] else None


console = Console(soft_wrap=True)
h2t = html2text.HTML2Text()
app = typer.Typer()




# Search for models by query, tag, or types,  which are optional via the api
def search_models(query: str = "", **kwargs) -> List[Dict[str, Any]]:

    allowed_params = {"tags": None, "types": "Checkpoint", "limit": 2, "sort": "Highest Rated", "period": "AllTime", "page": 1}
    params = allowed_params
    

    # Update params with kwargs values that are present in allowed_params
    for key, value in allowed_params.items():
        if key in kwargs:
            params[key] = kwargs[key]

    if query:
        params["query"] = query

    def validate_param(key, valid_values) -> bool:
        if key in kwargs and kwargs[key] not in valid_values and kwargs[key] is not None:
            table = Table(style="bright_yellow")
            table.add_column("Invalid " + key.capitalize())
            table.add_row(f"\"{kwargs[key]}\" is not a valid {key}.\n Please choose from: {', '.join(valid_values)}")
            console.print(table)
            return False
        return True

    if not validate_param("types", TYPES.keys()) or None:
        return []
    if not validate_param("period", ["AllTime", "Year", "Month", "Week", "Day"]) or None:
        return []
    if not validate_param("sort", ["Highest Rated", "Most Downloaded", "Newest"])  or None:
        return []
    
    request = requests.get(CIVITAI_MODELS, params=params)
    if request.status_code == 200:
        response = request.json()
        return response
    return []


def remove_model(model_path: str) -> bool:
    """Remove the specified model file after user confirmation, checking for permissions."""
    if os.path.exists(model_path):
        
        if not os.access(model_path, os.W_OK):
            console.print(f"You do not have permission to remove the model at {model_path}.", style="bright_red")
            return False

        feedback_message(f"This is a desctructive operation and cannot be undone. Please proceed with caution.", "warning")
        confirmation = typer.confirm(f"Are you sure you want to remove the model at {model_path}? (Y/N): ", abort=True)
        if confirmation:
            console.print(f"Removing model at {model_path}...", style="bright_yellow")
            total_size = os.path.getsize(model_path)  
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Removing Model", colour="magenta") as progress_bar:
                # Attempt to delete the model
                try:
                    os.remove(model_path)
                    progress_bar.update(total_size)
                    return True
                except OSError as e:
                    feedback_message(f"Failed to remove the model at {model_path} // {e}.", "error")
                    return False
                feedback_message(f"Model at {model_path} removed successfully.", "info")
        else:
            return False
        
    else:
        feedback_message(f"No model found at {model_path}.", "warning")
    return False


# TODO: Fix the markdown output
def summarize_model_description(model_id: int, service: str) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = get_model_details(CIVITAI_MODELS, CIVITAI_VERSIONS, model_id)
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and Ollama:
            response = Ollama.chat(
                model=OLLAMA_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": OLLAMA_OPTIONS["system_template"]},
                    {"role": "user", "content": f"{OLLAMA_OPTIONS['system_template']} {description}"}
                    # consider adding the system template
                    # to the prompt since not all models follow it
                ],
                options={"temperature": float(OLLAMA_OPTIONS["temperature"]), "top_p": float(OLLAMA_OPTIONS["top_p"])},
                keep_alive=0 # Free up the VRAM
            )
            if 'message' in response and 'content' in response['message']:
                if not OLLAMA_OPTIONS["html_output"]:
                    return h2t.handle(response['message']['content'])
                else:
                    return Markdown(response['message']['content'], justify="left")
                
        elif service == "openai" and OpenAI:
            response = OpenAI.chat.completions.create(
                model=OPENAI_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": OPENAI_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

        elif service == "groq" and Groq:
            response = Groq.chat.completions.create(
                model=GROQ_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": GROQ_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

    except Exception as e:
        feedback_message(f"Failed to summarize the model description using {service} // {e}", "error")
        return None


@app.command("sanity-check", help="Check to see if the app is ready to run.")
def sanity_check_command(): return sanity_check_cli()


@app.command("list", help="List available models along with their types and paths.")
def list_models_command(): list_models_cli(TYPES, MODELS_DIR, FILE_TYPES)


@app.command("stats", help="Stats on the parent models directory.")
def stats_command(): return inspect_models_cli(MODELS_DIR)


@app.command("details", help="Get detailed information about a specific model by ID.")
def details_command(identifier: str, desc: bool = False, images: bool = False):
    get_model_details_cli(identifier, desc, images,  CIVITAI_MODELS, CIVITAI_VERSIONS)


@app.command("download", help="Download a specific model variant by ID.")
def download_model_command(identifier: str, select: bool = False):
    download_model_cli(MODELS_DIR, CIVITAI_MODELS, CIVITAI_VERSIONS, CIVITAI_TOKEN, TYPES, identifier, select)


@app.command("remove", help="Remove specified models from local storage.")
def remove_models_cli():
    """Remove specified models from local storage."""
    model_types_list = list(TYPES.keys())

    console.print("Available model types for deletion:")
    for index, model_type in enumerate(model_types_list, start=1):
        console.print(f"{index}. {model_type}")

    model_type_index = typer.prompt("Enter the number corresponding to the type of model you would like to delete")

    try:
        model_type = model_types_list[int(model_type_index) - 1]
    except (IndexError, ValueError):
        table = Table(title="Invalid selection. Please enter a valid number.", style="bright_red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)
        return

    model_folder = get_model_folder(MODELS_DIR, model_type, TYPES)
    models_in_folder = list_models(model_folder, FILE_TYPES)

    if not models_in_folder:
        feedback_message(f"No models found for type {model_type}.", "warning")
        return

    table = Table(title=f"Models of Type: {model_type}", title_justify="left")
    table.add_column("Model Name", style="cyan")
    table.add_column("Model Type", style="cyan")
    table.add_column("Path", style="bright_yellow")
    

    for model in models_in_folder:
        table.add_row(model[0], model[1], model[2])

    console.print(table)

    model_version_ids = typer.prompt("Enter the model name you wish to delete (comma-separated):")

    if model_version_ids:
        models_to_delete = [model for model in models_in_folder if model[0] in model_version_ids]
        
        if not models_to_delete:
            console.print("No matching model found for deletion.", style="bright_red")
            return
    
        model_removed = remove_model(models_to_delete[0][2])
        if model_removed:
            feedback_message(f"Model {models_to_delete[0][0]} removed successfully.", "info")
    else:
        console.print("No model name provided for deletion.", style="bright_red")


# TODO: Fix table formatting for name and tags (emjois are breaking the table)
@app.command("search", help="Search for models by query, tag, or types, which are optional via the API.")
def search_cli(query: str = "", tags=None, types="Checkpoint", limit=20, sort="Highest Rated", period="AllTime"):
    """Search for models by query, tag, or types, which are optional via the API."""
    kwargs = dict(tags=tags, types=types, limit=limit, sort=sort, period=period)
    models = search_models(query, **kwargs)
    metadata = models.get("metadata", {})
    
    #print(metadata)

    if not models:
        console.print("No models found.", style="bright_yellow")
        return

    table = Table(title_justify="left")
    table.add_column("ID", style="bright_yellow")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white", )
    table.add_column("NSFW", style="bright_red"),
    table.add_column("Tags", style="white")

    for model in models.get("items"):
        name = Text(clean_text(model["name"]), style="bold", overflow="ellipsis")
        tags = Text(", ".join(model["tags"]), style="italic", overflow="ellipsis")
        nsfw = Text("Yes", style="green ") if model["nsfw"] else Text("No", style="bright_red")
        table.add_row(str(model["id"]), name, model["type"], nsfw, tags)
        
    console.print(table)
    
    # Prompt for model it to get more details
    #model_id = typer.prompt("Enter the Model ID for details or type \"next\" to get more models; \"cancel\" to cancel", default="")
    # if model_id == "cancel":
    #     return
    
    # if model_id == "next":
    #     feedback_message(f"Paging not yet functional, pass --limit \\[n] to get more models", "warning")
    #     return
    # else:
    #     get_model_details_cli(model_id)
    #     return

@app.command("explain", help="Get a summary of a specific model by ID using the specified service (default is Ollama).")
def summarize_model_cli(identifier: str, service: str = "ollama"):
    """Get a summary of a specific model by ID using the specified service (default is Ollama)."""
    try:
        model = get_model_details(CIVITAI_MODELS, CIVITAI_VERSIONS, int(identifier))
        model_id = model.get("id", "")
        model_name = model.get("name", "")
        summary = summarize_model_description(model_id, service)
        
        summary_table = Table(title_justify="left")
        summary_table.add_column(f"Summary of model {model_name}/{model_id} using {service}:", style="cyan")
        summary_table.add_row(summary)
        
        console.print(summary_table)
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")


def main():
    if len(sys.argv) == 1: sys.argv.append("--help")
    app()

if __name__ == "__main__":
    main()
