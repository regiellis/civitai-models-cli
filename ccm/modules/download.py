import os
import requests
import typer
from typing import Any, List, Dict, Optional
from tqdm import tqdm
from rich.console import Console
from .helpers import feedback_message, get_model_folder, create_table
from .details import get_model_details

__all__ = ["download_model_cli"]


console = Console(soft_wrap=True)


def select_version(model_name: str, versions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    feedback_message(f"Please select a version to download for model {model_name}.", "info")
    
    versions_table = create_table(
        "Available Versions",
        [
            ("Version ID", "bright_yellow"),
            ("Version Name", "cyan"),
            ("Base Model", "blue")
        ]
    )

    for version in versions:
        versions_table.add_row(str(version["id"]), version["name"], version["base_model"])
    
    console.print(versions_table)
    selected_version_id = typer.prompt("Enter the version ID to download:")

    for version in versions:
        if str(version["id"]) == selected_version_id:
            return version

    feedback_message(f"Version {selected_version_id} is not available for model {model_name}.", "error")
    return None

def download_model(MODELS_DIR: str, CIVITAI_DOWNLOAD: str, CIVITAI_TOKEN: str, 
                   TYPES, model_id: int, model_details: Dict[str, Any], select: bool = False) -> Optional[str]:
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
        # Assume the model is a variant
        selected_version = {
            "id": model_id,
            "name": model_details.get("name", ""),
            "base_model": model_details.get("base_model", ""),
            "download_url": model_details.get("download_url", ""),
            "images": model_details["images"][0].get("url", ""),
            "file": model_meta.get("file", "")
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
    model_folder = get_model_folder(MODELS_DIR, model_type, TYPES)
    model_path = os.path.join(model_folder, selected_version.get('base_model', ''), f"{selected_version.get('file')}")
    

    if os.path.exists(model_path):
        feedback_message(f"Model {model_name} already exists at {model_path}. Skipping download.", "warning")
        return None
    

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    return download_file(download_url, model_path, model_name)


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
    
# TODO: Look into dealing with partial downloads and resuming downloads
def download_model_cli(identifier: str, select: bool = False, **kwargs) -> None:
    try:
        model_id = int(identifier)
        model_details = get_model_details(kwargs.get("CIVITAI_MODELS"), kwargs.get("CIVITAI_VERSIONS"), model_id)
        types = kwargs.get("TYPES")

        if model_details:
            model_path = download_model(kwargs.get("MODELS_DIR"), kwargs.get("CIVITAI_DOWNLOAD"), kwargs.get("CIVITAI_TOKEN"), 
                                        types, model_id, model_details, select)
            if model_path:
                feedback_message(f"Model downloaded successfully at: {model_path}", "info")
            else:
                if model_path is not None:
                    feedback_message("Failed to download the model.", "error")
        else:
            feedback_message(f"No model found with ID: {identifier}.", "error")
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")