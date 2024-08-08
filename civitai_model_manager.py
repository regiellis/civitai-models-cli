"""
==========================================================
Civitai Model Downloader - Simplified Model Retrieval
==========================================================

Simple CLI tool that streamlines the process of managing AI models from the
CivitAI platform. It offers functionalities to list available models,
view their details, search, download selected variants, and remove models from
local storage. It also provides a summary of the model description using
Ollama or OpenAI.

Usage:
$ pipx run file:civitai_model_manager.py [OPTIONS] [COMMAND] [ARGS]
$ python civitai_model_manager.py [OPTIONS] [COMMAND] [ARGS]

Options:
  list               List available models along with their types and paths.
  stats              Stats on the parent models directory.
  details INT        Get detailed information about a specific model by ID.
  download INT       Download a specific model variant by ID.
  remove             Remove specified models from local storage.
  explain INT        Get a summary of a specific model by ID using Ollama.
  --help             Show this message and exit.

Examples:
$ python civitai_model_manager.py --list
$ python civitai_model_manager.py --stats
$ python civitai_model_manager.py --details 12345 [--desc] [--images]
$ python civitai_model_manager.py --download 54321 [--select]
$ python civitai_model_manager.py --remove
$ python civitai_model_manager.py --explain 12345 [--service ollama]
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
from typing import Any, Dict, List, Optional, Tuple
import requests
import typer
import html2text
from platform import system
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from rich import print
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.traceback import install
install()

from tqdm import tqdm

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
MODELS_DIR = os.getenv("MODELS_DIR", "")
CIVITAI_TOKEN = os.getenv("CIVITAI_TOKEN", "")

CIVITAI_MODELS = "https://civitai.com/api/v1/models"
CIVITAI_IMAGES = "https://civitai.com/api/v1/images"
CIVITAI_VERSIONS = "https://civitai.com/api/v1/model-versions"
CIVITAI_DOWNLOAD = "https://civitai.com/api/download/models"

TYPES = {
    "Checkpoint": "checkpoints",
    "TextualInversion": "textual_inversions",
    "Hypernetwork": "hypernetworks",
    "AestheticGradient": "aesthetic_gradients",
    "LORA": "loras",
    "Controlnet": "controlnets",
    "Poses": "poses"
}

OLLAMA_OPTIONS = {
    "model": os.getenv("OLLAMA_MODEL", ""),
    "api_base": os.getenv("OLLAMA_API_BASE", ""),
    "temperature": os.getenv("TEMP", 0.9),
    "top_p": os.getenv("TOP_P", 0.3),
    "html_output": os.getenv("HTML_OUT", False),
    "system_template": (
        "You are an expert in giving detailed explanations of description you are provided. Do not present it"
        "like an update log. Make sure to explains the full description in a way that is easy to understand. "
        "The description is not provided by the user but comes from the CivitAI API, so don't make recommendations on how to "
        "improve the description, just be detailed, clear and thorough about the provided content. "
        "Include recommended settings and tip if it appears in the description:\n"
        " - Tips on Usage\n"
        "- Sampling method\n"
        "- Schedule type\n"
        "- Sampling steps\n"
        "- CFG Scale\n"
        "DO NOT OFFER ADVICE ON HOW TO IMPROVE THE DESCRIPTION!!!\n"
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
FILE_TYPES=(".safetensors", ".pt", ".pth", ".ckpt")

# TODO: More robust logic checks...this is just a basic check
def sanity_check() -> None:
    CHECKS = {
        "REQUIRED": {
            "MODELS_DIR": False,
            "CIVITAI_TOKEN": False,
            "WRITE_PERMISSION": False,
            "API_AVAILABILITY": False,
        },            
        "OPTIONAL": {
            "OLLAMA_ACCESSIBLE": False,
            "OPENAI_ACCESSIBLE": False,
            "MODEL_AVAILABILITY": False,
        }
    }
    
    if MODELS_DIR:
        CHECKS["REQUIRED"]["MODELS_DIR"] = True
        if os.path.exists(MODELS_DIR):
            CHECKS["REQUIRED"]["WRITE_PERMISSION"] = os.access(MODELS_DIR, os.W_OK)
        else:
            CHECKS["REQUIRED"]["WRITE_PERMISSION"] = False
    else:
        CHECKS["REQUIRED"]["MODELS_DIR"] = False
        
    if CIVITAI_TOKEN:
        CHECKS["REQUIRED"]["CIVITAI_TOKEN"] = True
    else:
        CHECKS["REQUIRED"]["CIVITAI_TOKEN"] = False
        
    # 200 status code indicates that the API is accessible
    response = requests.get(CIVITAI_MODELS)
    if response.status_code == 200:
        CHECKS["REQUIRED"]["API_AVAILABILITY"] = True
    else:
        CHECKS["REQUIRED"]["API_AVAILABILITY"] = False

    table = Table(title="Sanity Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Message", style="green")
    
    for check, status in CHECKS["REQUIRED"].items():
        if status:
            table.add_row(check, "Pass", "Good to go!", style="green")
        else:
            table.add_row(check, "Fail", f"{check} Failed, Required to run CMM", style="bright_red")
            
    console.print(table)
    return None


def clean_text(text: str) -> str:
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()


def convert_kb(kb: float) -> str:
    if kb <= 0:
        raise ValueError("Input must be a positive number.")
    units = ["KB", "MB", "GB"]
    i = 0
    while kb >= 1024 and i < len(units) - 1: 
        kb /= 1024.0  
        i += 1

    return f"{round(kb, 2)} {units[i]}"


def feedback_message(message: str, type: str = "info") -> None:
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

def list_models(model_dir: str) -> List[Tuple[str, str, str]]:
    models = []
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith(FILE_TYPES):
                model_path = os.path.join(root, file)
                model_name = os.path.splitext(file)[0]
                model_type = os.path.basename(root)
                models.append((model_name, model_type, model_path))
    return models


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
            table = Table(style="yellow")
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


def get_model_details(model_id: int) -> Dict[str, Any]:
    
    try:
        if not model_id:
            feedback_message("Please provide a valid model ID.", "error")
            return {}
        
        request = requests.get(f"{CIVITAI_MODELS}/{model_id}")
        if request.status_code == 200:
            response = request.json()

            versions = [{
                "id": version.get("id", ""),
                "name": version.get("name", ""),
                "base_model": version.get("baseModel", ""),
                "download_url": version.get("files")[0].get("downloadUrl", ""),
                "images": version.get("images")[0].get('url', ""),
                "file": version.get("files")[0].get("name", "")
            } for version in response["modelVersions"]]
            
            return {
                "id": response.get("id", ""),
                "name": response.get("name", ""),
                "description": response.get("description", ""),
                "type": response.get("type", ""),
                "download_url": response["modelVersions"][0].get("downloadUrl", ""),
                "tags": response.get("tags", []),
                "creator": response["creator"].get("username", ""),
                "trainedWords": response["modelVersions"][0].get("trainedWords", "None"),
                "nsfw": Text("Yes", style="green") if response.get("nsfw", False) else Text("No", style="bright_red"),
                "metadata": {
                  "stats": f"{response["stats"].get("downloadCount", "")} downloads, {response["stats"].get('thumbsUpCount', '')} likes, {response["stats"].get('thumbsDownCount', '')} dislikes",
                  "size": convert_kb(response["modelVersions"][0].get("files")[0].get("sizeKB", "")),
                  "format": response["modelVersions"][0].get("files")[0].get("metadata", "").get("format", ".safetensors"),
                  "file": response["modelVersions"][0].get("files")[0].get("name", ""),
                },
                "versions": versions,
                "images": response["modelVersions"][0]["images"]
            }
        else:
            request = requests.get(f"{CIVITAI_VERSIONS}/{model_id}")
            if request.status_code == 200:
                response = request.json()
                
                # TODO: Refactor to not make a second request(unnecessary) or place in a function
                # TODO: to avoid code duplication. Maybe sort the data from the versions dict
                parent_model_request = requests.get(f"{CIVITAI_MODELS}/{response.get('modelId')}")
                parent_model_response = parent_model_request.json()
                version_data = parent_model_response['modelVersions']
                
                #search for the version data for an id
                for version in version_data:
                    if version.get("id") == response.get("id", ""):
                        version_data = version
                        break

                return {
                    "id": response.get("id", ""),
                    "parent_id": response.get("modelId", "None"),
                    "parent_name": response["model"].get("name", "None"),
                    "name": response.get("name", "None"),
                    "description": parent_model_response.get("description", "None"),
                    "type": response["model"].get("type", "None"),
                    "base_model": response.get("baseModel", ""),
                    "tags": parent_model_response.get("tags", []),
                    "creator": parent_model_response['creator'].get("username", "None"),
                    "trainedWords": response.get("trainedWords", "None"),
                    "nsfw": Text("Yes", style="green") if response.get("nsfw", False) else Text("No", style="bright_red"),
                    "download_url": response.get("downloadUrl", ""),
                    "metadata": {
                        "stats": f"{response["stats"].get("downloadCount", "")} downloads, {response["stats"].get('thumbsUpCount', '')} likes, {version_data["stats"].get('thumbsDownCount', '')} dislikes",
                        "size": convert_kb(response["files"][0].get("sizeKB", "")),
                        "format": response["files"][0].get("metadata").get("format", ".safetensors"),
                        "file": response["files"][0].get("name", ""),
                    },
                    "versions": [],
                    "images": version_data.get("images", [])
                }
    except requests.RequestException as e:
        feedback_message(f"Failed to get model details for model ID: {model_id} // {e}", "error")
        return {}
    
    return
    

def download_model(model_id: int, model_details: Dict[str, Any], select: bool = False) -> Optional[str]:
    model_name = model_details.get("name", f"Model_{model_id}")
    model_type = model_details.get("type", "unknown")
    model_meta = model_details.get("metadata", {})
    versions = model_details.get("versions", [])

    if versions == [] and not model_details.get("parent_id"):
        feedback_message(f"No versions available for model {model_name}.", "warning")
        return None

    if not select and not model_details.get("parent_id"):
        selected_version = versions[0]
    elif not select and model_details.get("parent_id"):
        # TODO: Do a better job of handling this case
        # Assume the model is a variant
        selected_version = {
            "id": model_id,
            "name": model_details.get("name", ""),
            "base_model": model_details.get("base_model", ""),
            "download_url": model_details.get("download_url", ""),
            "images": model_details["images"][0].get("url", "")
        }
    else:
        if model_details.get("parent_id"):
            feedback_message(f"Model {model_name} is a variant of {model_details['parent_name']} // Model ID: {model_details['parent_id']} \r Needs to be a parent model", "warning")
            return None
        # prompt user to select a version
        selected_version = select_version(model_name, versions)
    
    if not selected_version:
        feedback_message(f"A version is not available for model {model_name}.", "error")
        return None

    # model_name = f"{model_name}_{selected_version['name'].replace('.', '')}"
    download_url = f"{CIVITAI_DOWNLOAD}/{selected_version['id']}?token={CIVITAI_TOKEN}"
    model_folder = get_model_folder(model_type)
    model_path = os.path.join(model_folder, selected_version.get('base_model', ''), f"{selected_version.get('file')}")

    if os.path.exists(model_path):
        feedback_message(f"Model {model_name} already exists at {model_path}. Skipping download.", "warning")
        return None

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    return download_file(download_url, model_path, model_name)


def select_version(model_name: str, versions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    feedback_message(f"Please select a version to download for model {model_name}.", "info")
    
    table = Table(title="Available Versions", title_justify="left")
    table.add_column("Version ID", style="green")
    table.add_column("Version Name", style="cyan")
    table.add_column("Base Model", style="blue")

    for version in versions:
        table.add_row(str(version["id"]), version["name"], version["base_model"])
    
    console.print(table)
    selected_version_id = typer.prompt("Enter the version ID to download:")

    for version in versions:
        if str(version["id"]) == selected_version_id:
            return version

    feedback_message(f"Version {selected_version_id} is not available for model {model_name}.", "error")
    return None


def get_model_folder(model_type: str) -> str:
    if model_type not in TYPES:
        console.print(f"Model type '{model_type}' is not mapped to any folder. Please select a folder to download the model.")
        selected_folder = typer.prompt("Enter the folder name to download the model:", default="unknown")
        return os.path.join(MODELS_DIR, selected_folder)
    return os.path.join(MODELS_DIR, TYPES[model_type])


def download_file(url: str, path: str, desc: str) -> Optional[str]:
    """Download a file from a given URL and save it to the specified path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        with open(path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {desc}", colour="cyan") as progress_bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))
        return path
    except requests.RequestException as e:
        feedback_message(f"Failed to download the file: {e} // Please check if you have permission to download files to the specified path.", "error")
        return None


def remove_model(model_path: str) -> bool:
    """Remove the specified model file after user confirmation, checking for permissions."""
    if os.path.exists(model_path):
        
        if not os.access(model_path, os.W_OK):
            console.print(f"You do not have permission to remove the model at {model_path}.", style="bright_red")
            return False

        feedback_message(f"This is a desctructive operation and cannot be undone. Please proceed with caution.", "warning")
        confirmation = typer.confirm(f"Are you sure you want to remove the model at {model_path}? (Y/N): ", abort=True)
        if confirmation:
            console.print(f"Removing model at {model_path}...", style="yellow")
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
    model_details = get_model_details(model_id)
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and Ollama:
            response = Ollama.chat(
                model=OLLAMA_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": OLLAMA_OPTIONS["system_template"]},
                    {"role": "user", "content": f"{OLLAMA_OPTIONS["system_template"]} {description}"}
                    # consider adding the system template
                    # to the prompt since not all models follow the system template
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


@app.command("sanity")
def sanity_check_cli():
    """Check if the script is ready to run by verifying the required environment variables. BASIC!!!"""
    sanity_check()


@app.command("list")
def list_models_cli():
    """List available models along with their types and paths."""
    model_types_list = list(TYPES.keys())

    console.print("Available model types:")
    for index, model_type in enumerate(model_types_list, start=1):
        console.print(f"{index}. {model_type}")

    model_type_index = typer.prompt("Enter the number corresponding to the type of model you would like to list")

    try:
        model_type = model_types_list[int(model_type_index) - 1]
    except (IndexError, ValueError):
        # TODO: restart the function if the user enters an invalid number
        feedback_message("Invalid selection. Please enter a valid number.", "error")
        return

    model_folder = get_model_folder(model_type)
    models_in_folder = list_models(model_folder)

    if not models_in_folder:
        console.print(f"No models found for type {model_type}.", style="yellow")
        return

    table = Table(title=f"Models of Type: {model_type}", title_justify="left")
    table.add_column("Model Name", style="cyan")
    table.add_column("Path", style="green")

    for model in models_in_folder:
        table.add_row(model[0], model[2])

    console.print(table)


@app.command("stats", help="Stats on the parent models directory.")
def inspect_models_cli():
    """Stats on the parent models directory."""
    model_counts = count_models(MODELS_DIR)
    
    if not model_counts:
        console.print("No models found.", style="yellow")
        return

    total_count = sum(model_counts.values())

    table = Table(title_justify="left")
    table.add_column("Model Type", style="cyan")
    table.add_column(f"Model Per // Total Model Count: {total_count}", style="yellow")

    for model_type, count in model_counts.items():
        table.add_row(model_type, str(count))
    
    console.print(table)

    # Get top 10 largest models
    model_sizes = get_model_sizes(MODELS_DIR)

    table = Table(title_justify="left")
    table.add_column("Top 10 Largest Models // Model Name", style="cyan")
    table.add_column("Size on Disk", style="yellow")

    for model_name, size in sorted(model_sizes.items(), key=lambda x: float(x[1].split()[0]), reverse=True)[:10]:
        table.add_row(model_name, size)

    console.print(table)
    feedback_message("""Warning: This is an overall count of files in a location and not based on model types. 
                i.e. SDXL models and 1.5/2.1 will not be seperated in the count""", "warning")


@app.command("details", help="Get detailed information about a specific model by ID.")
def get_model_details_cli(identifier: str, desc: bool = False, images: bool = False):
    """Get detailed information about a specific model by ID."""
    try:
        model_id = int(identifier)
        model_details = get_model_details(model_id)

        if model_details:
            model_table = Table(title_justify="left")
            model_table.add_column("Attributes", style="green")
            model_table.add_column("Values", style="cyan")
            model_table.add_row("Model ID", str(model_details["id"]))
            model_table.add_row("Name", model_details["name"])
            model_table.add_row("Type", model_details["type"])
            model_table.add_row("Tags", ", ".join(model_details.get("tags", [])))
            model_table.add_row("Creator", model_details["creator"])
            model_table.add_row("NSFW", model_details["nsfw"])

            if desc:
                desc_table = Table(title_justify="left", width=200)
                desc_table.add_column("Description", style="cyan")
                desc_table.add_row(h2t.handle(model_details["description"]))
            
            versions = model_details.get("versions", [])
            
            if versions != []:
                version_table = Table(title_justify="left")
                version_table.add_column("Version ID", style="green")
                version_table.add_column("Name", style="cyan")
                version_table.add_column("Base Model", style="blue")
                version_table.add_column("Download URL", style="blue")
                version_table.add_column("Images", style="blue")

                for version in versions:
                    version_table.add_row(
                        str(version["id"]),
                        version["name"],
                        version["base_model"],
                        version["download_url"],
                        version["images"]
                    )

                    
            if model_details.get("images"):
                images_table = Table(title_justify="left")
                images_table.add_column("NSFW Lvl", style="bright_red")
                images_table.add_column("URL", style="green")

                
                for image in model_details.get("images"):
                    images_table.add_row(str(image.get("nsfwLevel")), image.get("url"))

            console.print(model_table)
            if desc:
                console.print(desc_table)
            if versions != []:
                console.print(version_table)
            if images and not model_details.get("parent_id"):
                console.print(images_table)
            if model_details.get("parent_id"):
                console.print(images_table)
                feedback_message(f"{model_details['name']} is a variant of {model_details['parent_name']} // Model ID: {model_details['parent_id']}", "warning")
                
            if images == []:
                feedback_message(f"No images available for model {model_details['name']}.", "warning")
                
            if versions == [] and not model_details.get("parent_id"):
                feedback_message(f"No versions available for model {model_details['name']}.", "warning")
                
            # Prompt for model id to download
            model_id = typer.prompt("Enter the model ID to download model or \"search\" for a quick search by tags; \"cancel\" to cancel", default="")
            if model_id == "cancel":
                return
            
            if model_id == "search":
                # Ask user for args to search
                query = typer.prompt("Enter a query or tag to search for a models, seperate tags by ','", default="")
                search_cli(query=query, tags=query.split(","))
                return
            else:
                download_model_cli(model_id)
                return
        else:
            table = Table(style="bright_red")
            table.add_column("Error Message")
            table.add_row(f"No model found with ID: {identifier}.")
            console.print(table)
    except ValueError:
        table = Table(title="Invalid model ID. Please enter a valid number", style="bright_red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)


@app.command("download", help="Download a specific model variant by ID.")
def download_model_cli(identifier: str, select: bool = False):
    """Download a specific model variant by ID."""
    try:
        model_id = int(identifier)
        model_details = get_model_details(model_id)

        if model_details:
            model_path = download_model(model_id, model_details, select)
            if model_path:
                feedback_message(f"Model downloaded successfully at: {model_path}", "info")
            else:
                if model_path is not None:
                    feedback_message("Failed to download the model.", "error")
        else:
            feedback_message(f"No model found with ID: {identifier}.", "error")
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")


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

    model_folder = get_model_folder(model_type)
    models_in_folder = list_models(model_folder)

    if not models_in_folder:
        feedback_message(f"No models found for type {model_type}.", "warning")
        return

    table = Table(title=f"Models of Type: {model_type}", title_justify="left")
    table.add_column("Model Name", style="cyan")
    table.add_column("Model Type", style="cyan")
    table.add_column("Path", style="green")
    

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
        console.print("No models found.", style="yellow")
        return

    table = Table(title_justify="left")
    table.add_column("ID", style="green")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="blue", )
    table.add_column("NSFW", style="magenta"),
    table.add_column("Tags", style="magenta")

    for model in models.get("items"):
        name = Text(clean_text(model["name"]), style="bold", overflow="ellipsis")
        tags = Text(", ".join(model["tags"]), style="italic", overflow="ellipsis")
        nsfw = Text("Yes", style="green ") if model["nsfw"] else Text("No", style="bright_red")
        table.add_row(str(model["id"]), name, model["type"], nsfw, tags)
        
    console.print(table)
    
    # Prompt for model it to get more details
    model_id = typer.prompt("Enter the Model ID for details or type \"next\" to get more models; \"cancel\" to cancel", default="")
    if model_id == "cancel":
        return
    
    if model_id == "next":
        feedback_message(f"Paging not yet functional, pass --limit \\[n] to get more models", "warning")
        return
    else:
        get_model_details_cli(model_id)
        return

@app.command("explain", help="Get a summary of a specific model by ID using the specified service (default is Ollama).")
def summarize_model_cli(identifier: str, service: str = "ollama"):
    """Get a summary of a specific model by ID using the specified service (default is Ollama)."""
    try:
        model_id = int(identifier)
        summary = summarize_model_description(model_id, service)
        
        summary_table = Table(title_justify="left")
        summary_table.add_column(f"Summary of model {model_id} using {service}:", style="cyan")
        summary_table.add_row(summary)
        
        console.print(summary_table)
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")

if __name__ == "__main__":
    sys.argv.append("--help") if len(sys.argv) == 1 else None
    app()

