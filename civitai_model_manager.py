"""
==========================================================
Civitai Model Downloader - Simplified Model Retrieval
==========================================================

Simple CLI tool streamlines the process of managing AI models from the
CivitAI platform. It offers functionalities to list available models,
view their details, download selected variants, and remove models from
local storage and provides a summary of the model description using
Ollama or OpenAI.

Usage:
$ pipx run file:civitai_model_manager.py [OPTIONS]

Options:
  list               List available models along with their types and paths.
  inspect            Count models per model type.
  details INT        Get detailed information about a specific model by ID.
  download INT       Download a specific model variant by ID.
  remove             Remove specified models from local storage.
  summarize INT      Get a summary of a specific model by ID using Ollama.
  --help             Show this message and exit.

Examples:
$ python civitai_model_manager.py --list
$ python civitai_model_manager.py --inspect
$ python civitai_model_manager.py --details 12345
$ python civitai_model_manager.py --download 54321
$ python civitai_model_manager.py --download 54321 --version 12322
$ python civitai_model_manager.py --remove
$ python civitai_model_manager.py --summarize 12345
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer",
#   "rich",
#   "requests",
#   "shellingham",
#   "tqdm",
#   "civitai",
#   "python-dotenv",
#   "ollama",
#   "openai"
# ]
# ///

import os
import platform
from typing import Any, Dict, List, Optional, Tuple
import requests
import typer
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from ollama import Client  # Verify the correct package name and import
from openai import OpenAI  # Verify the correct package name

from civitai import models, tags  # Adjust according to actual usage

def load_environment_variables():
    # Determine the platform
    system_platform = platform.system()
    
    # Define the location to search based on the platform
    if system_platform == "Windows":
        dotenv_path = os.path.join(os.path.expanduser("~"), ".env")  # User's home directory on Windows
    elif system_platform == "Linux":
        # For Ubuntu or other Linux distributions, look in the .config/cmm/ directory
        dotenv_path = os.path.join(os.path.expanduser("~"), ".config", "cmm", ".env")
    else:
        # For other platforms, default to the current directory
        dotenv_path = ".env"
    
    # Load the environment variables from the determined .env file
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        # If .env file not found, look in the current directory
        current_dir_dotenv_path = ".env"
        if os.path.exists(current_dir_dotenv_path):
            load_dotenv(current_dir_dotenv_path)
        else:
            # Warn the user about the missing .env file
            print("Warning: .env file is missing. Please create one using the sample.env provided.")


load_environment_variables()
MODELS_DIR = os.getenv("MODELS_DIR", "")
CIVITAI_TOKEN = os.getenv("CIVITAI_TOKEN", "")

# Initialize constants
CIVITAI_URL = f"https://civitai.com/api/v1/models?token={CIVITAI_TOKEN}"
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
    "system_template": (
        "You are an expert in giving detailed explanations of information you are provided. Do not present it "
        "like an update log. Make sure it is clear, concise, and explains the information in a way that is easy to understand. "
        "The information is not provided by the user and comes from the CivitAI API, so don't make recommendations on how to "
        "improve the description, just be detailed about the provided content. Include recommended settings if in the information:\n"
        "- Sampling method\n"
        "- Schedule type\n"
        "- Sampling steps\n"
        "- CFG Scale\n"
        "DO NOT OFFER ADVICE ON HOW TO IMPROVE THE DESCRIPTION. DO NOT OFFER ADVICE ON HOW TO IMPROVE THE DESCRIPTION!!!"
    )
}

CHATGPT_OPTIONS = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"]
}

Ollama = Client(OLLAMA_OPTIONS["api_base"]) if OLLAMA_OPTIONS["api_base"] else None
ChatGPT = OpenAI(api_key=CHATGPT_OPTIONS["api_key"]) if CHATGPT_OPTIONS["api_key"] else None

console = Console()
app = typer.Typer()


def list_models(model_dir: str) -> List[Tuple[str, str, str]]:
    models = []
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith((".safetensors", ".ckpt")):
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
            if file.endswith((".safetensors", ".pt", ".pth", ".ckpt")):
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
            if file.endswith((".safetensors", ".pt", ".pth")):
                model_path = os.path.join(root, file)
                size_in_bytes = os.path.getsize(model_path)
                size_in_mb = size_in_bytes / (1024 * 1024)
                size_in_gb = size_in_bytes / (1024 * 1024 * 1024)

                size_str = f"{size_in_mb:.2f} MB ({size_in_gb:.2f} GB)" if size_in_gb >= 1 else f"{size_in_mb:.2f} MB"

                model_name = os.path.basename(file)
                model_sizes[model_name] = size_str
    return model_sizes


def get_model_details(model_id: int) -> Dict[str, Any]:
    try:
        model = models.get_model(model_id)
        if not model:
            return {}
        
        versions = [{
            "id": version.id,
            "name": version.name,
            "base_model": version.baseModel,
            "download_url": version.files[0].get("downloadUrl", ""),
            "images": version.images[0].get('url', "")
        } for version in model.modelVersions]

        return {
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "type": model.type,
            "versions": versions,
            "tags": model.tags,
        }
    except Exception as e:
        table = Table(title="Error fetching model details:", style="red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(e))
        console.print(table)
        return {}


def download_model(model_id: int, model_details: Dict[str, Any], version: str) -> Optional[str]:
    model_name = model_details.get("name", f"Model_{model_id}")
    model_type = model_details.get("type", "unknown")
    versions = model_details.get("versions", [])

    if not versions:
        console.print(f"No versions available for model {model_name}.", style="red")
        return None

    if version == "latest":
        selected_version = versions[0]
    else:
        selected_version = next((v for v in versions if str(v["id"]) == str(version)), None)

    if not selected_version:
        console.print(f"Version {version} is not available for model {model_name}.", style="red")
        return None

    model_name = f"{model_name}_{selected_version['name'].replace('.', '')}"
    download_url = f"{CIVITAI_DOWNLOAD}/{selected_version['id']}?token={CIVITAI_TOKEN}"
    model_folder = get_model_folder(model_type)
    model_path = os.path.join(model_folder, selected_version.get('base_model', ''), f"{model_name}.safetensors")

    if os.path.exists(model_path):
        console.print(f"Model {model_name} already exists at {model_path}. Skipping download.", style="yellow")
        return model_path

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    return download_file(download_url, model_path, model_name)


def select_version(model_name: str, versions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    console.print(f"Please select a version to download for model {model_name}.", style="yellow")
    
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

    console.print(f"Version {selected_version_id} is not available for model {model_name}.", style="red")
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
        table = Table(title="Download Error", style="red", border_style="bright_red", title_justify="left")
        table.add_column("Error Message", style="white")
        table.add_row(str(e))
        console.print(table)
        console.print("Please check if you have permission to download files to the specified path.", style="red")
        return None


def remove_model(model_path: str) -> bool:
    """Remove the specified model file after user confirmation, checking for permissions."""
    if os.path.exists(model_path):
        
        if not os.access(model_path, os.W_OK):
            console.print(f"You do not have permission to remove the model at {model_path}.", style="red")
            return False

        confirmation = input(f"Are you sure you want to remove the model at {model_path}? (Y/N): ")
        if confirmation.lower() == "y":
            console.print(f"Removing model at {model_path}...", style="yellow")
            total_size = os.path.getsize(model_path)  
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Removing Model", colour="magenta") as progress_bar:
                # Attempt to delete the model
                try:
                    os.remove(model_path)
                    progress_bar.update(total_size)
                    console.print(f"Model at {model_path} removed successfully.", style="green")
                    return True
                except OSError as e:
                    console.print(f"Failed to remove the model: {e}", style="red")
                    return False
        else:
            console.print("Operation aborted.", style="yellow")
            return False
    else:
        console.print(f"No model found at {model_path}.", style="yellow")
    return False


def summarize_model_description(model_id: int, service: str) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = get_model_details(model_id)
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and Ollama:

            response = Ollama.chat(
                model=OLLAMA_OPTIONS["model"],
                messages=[
                    {"role": "system", "content": OLLAMA_OPTIONS["system_template"]},
                    {"role": "user", "content": description} 
                    # consider adding the system template
                    # to the prompt since not all models follow the system template
                ],
                options={"temperature": 0.7},
                keep_alive=0 # Free up the VRAM
            )
            return response['message']['content']
        elif service == "openai" and ChatGPT:
            response = ChatGPT.chat.completions.create(
                model=CHATGPT_OPTIONS["model"],
                messages=[
                    {"role": "system", "content": CHATGPT_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        table = Table(style="red")
        table.add_column("Error Message")
        table.add_row(str(e))
        console.print(table)
        return None
    
    
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
        table = Table(title="Invalid selection. Please enter a valid number.", style="red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)
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


@app.command("inspect")
def inspect_models_cli():
    """Count models per model type in the specified directory."""
    model_counts = count_models(MODELS_DIR)
    
    if not model_counts:
        console.print("No models found.", style="yellow")
        return

    total_count = sum(model_counts.values())

    table = Table(title="Model Counts", title_justify="left")
    table.add_column("Model Type", style="cyan")
    table.add_column("Count", style="magenta")

    for model_type, count in model_counts.items():
        table.add_row(model_type, str(count))
    
    console.print(table)
    console.print("""Warning: This is an overall count of files in a location and not based on model types. 
                  i.e. SDXL models and 1.5/2.1 will not be seperated in the count""", style="yellow")
    console.print(f"Total Model Count: {total_count}", style="green")

    # Get top 10 largest models
    model_sizes = get_model_sizes(MODELS_DIR)

    table = Table(title="Top 10 Largest Models", title_justify="left")
    table.add_column("Model Name", style="cyan")
    table.add_column("Size", style="magenta")

    for model_name, size in sorted(model_sizes.items(), key=lambda x: float(x[1].split()[0]), reverse=True)[:10]:
        table.add_row(model_name, size)

    console.print(table)


@app.command("details")
def get_model_details_cli(identifier: str):
    """Get detailed information about a specific model by ID."""
    try:
        model_id = int(identifier)
        model_details = get_model_details(model_id)

        if model_details:
            model_table = Table(title="Model Details", title_justify="left")
            model_table.add_column("Attribute", style="green")
            model_table.add_column("Value", style="cyan")

            model_table.add_row("Model ID", str(model_details["id"]))
            model_table.add_row("Name", model_details["name"])
            model_table.add_row("Type", model_details["type"])
            model_table.add_row("Tags", ", ".join(model_details.get("tags", [])))

            version_table = Table(title="Model Versions", title_justify="left")
            version_table.add_column("Version ID", style="green")
            version_table.add_column("Name", style="cyan")
            version_table.add_column("Base Model", style="blue")
            version_table.add_column("Download URL", style="blue")
            version_table.add_column("Images", style="blue")

            versions = model_details.get("versions", [])
            for version in versions:
                version_table.add_row(
                    str(version["id"]),
                    version["name"],
                    version["base_model"],
                    version["download_url"],
                    version["images"]
                )

            console.print(model_table)
            console.print(version_table)
        else:
            console.print(f"No model found with ID: {identifier}.", style="red")
    except ValueError:
        table = Table(title="Invalid model ID. Please enter a valid number", style="red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)

        
@app.command("download")
def download_model_cli(identifier: str, version: str = "latest"):
    """Download a specific model variant by ID."""
    try:
        model_id = int(identifier)
        model_details = get_model_details(model_id)

        if model_details:
            model_path = download_model(model_id, model_details, version)
            if model_path:
                console.print(f"Model downloaded successfully at: {model_path}", style="green")
            else:
                console.print("Failed to download the model.", style="red")
        else:
            console.print(f"No model found with ID: {identifier}.", style="red")
    except ValueError:
        table = Table(title="Invalid model ID. Please enter a valid number", style="red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)


@app.command("remove")
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
        table = Table(title="Invalid selection. Please enter a valid number.", style="red", title_justify="left")
        table.add_column("Error Message")
        table.add_row(str(ValueError))
        console.print(table)
        return

    model_folder = get_model_folder(model_type)
    models_in_folder = list_models(model_folder)

    if not models_in_folder:
        console.print(f"No models found for type {model_type}.", style="yellow")
        return

    table = Table(title=f"Models of Type: {model_type}", title_justify="left")
    table.add_column("Model Name", style="cyan")
    table.add_column("Model Type", style="cyan")
    table.add_column("Path", style="green")
    

    for model in models_in_folder:
        table.add_row(model[0], model[1], model[2])

    console.print(table)

    model_version_ids = typer.prompt("Enter the model names you wish to delete (comma-separated):")
    model_version_ids = [id_.strip() for id_ in model_version_ids.split(",")]

    models_to_delete = [model for model in models_in_folder if model[0] in model_version_ids]

    if not models_to_delete:
        console.print("No matching models found for deletion.", style="red")
        return

    with console.status("Deleting models..."):
        for model in tqdm(models_to_delete, desc="Removing Models", unit="model"):
            if remove_model(model[2]):
                console.print(f"Model {model[0]} has been deleted successfully.", style="green")
            else:
                console.print(f"Failed to delete model {model[0]}.", style="red")


@app.command("summarize")
def summarize_model_cli(identifier: str, service: str = "ollama"):
    """Get a summary of a specific model by ID using the specified service (default is Ollama)."""
    try:
        model_id = int(identifier)
        summary = summarize_model_description(model_id, service)
        console.print("Model Summary:", style="yellow")
        console.print(summary, style="cyan")
    except ValueError:
        table = Table(style="red")
        table.add_column("Error Message")
        table.add_row("Invalid model ID. Please enter a valid number.")
        console.print(table)

if __name__ == "__main__":
    app()