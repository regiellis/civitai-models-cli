import os
import typer
import httpx
import importlib.resources as pkg_resources

from pathlib import Path
from typing import Any, Dict, List
from .helpers import create_table, feedback_message, display_readme
from rich.console import Console
import time

from civitai_models_manager import (
    OLLAMA_OPTIONS,
)
from ollama import Client as OllamaClient

Ollama = (
    OllamaClient(OLLAMA_OPTIONS["api_base"]) if OLLAMA_OPTIONS["api_base"] else None
)

console = Console()


def check_models_dir() -> Dict[str, Any]:
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
    token = os.environ.get("CIVITAI_TOKEN")
    if not token:
        return {
            "status": False,
            "message": "CIVITAI_TOKEN environment variable not set",
        }
    return {"status": True, "message": "CivitAI token check passed"}


def check_api_availability() -> Dict[str, Any]:
    civitai_models_url = os.environ.get(
        "CIVITAI_MODELS", "https://civitai.com/api/v1/models"
    )
    try:
        response = httpx.get(civitai_models_url, timeout=10)
        if response.status_code == 200:
            return {"status": True, "message": "API is accessible"}
        else:
            return {
                "status": False,
                "message": f"API returned status code {response.status_code}",
            }
    except httpx.RequestError as e:
        return {"status": False, "message": f"Failed to connect to API: {str(e)}"}


def check_ollama() -> Dict[str, Any]:
    try:
        response = Ollama.chat(
            model=OLLAMA_OPTIONS["model"],
            messages=[
                {"role": "user", "content": "What is your purpose?"},
            ],
            keep_alive=0,  # Free up the VRAM
        )
        print(response)
        return {"status": True, "message": "Ollama is accessible"}
    except Exception as e:
        return {"status": False, "message": f"Failed to connect to Ollama: {str(e)}"}


def sanity_check_cli(**kwargs) -> None:
    CHECKS = {
        "REQUIRED": {
            "MODELS_DIR": check_models_dir,
            "CIVITAI_TOKEN": check_civitai_token,
            "API_AVAILABILITY": check_api_availability,
        },
        "OPTIONAL": {
            "OLLAMA": check_ollama,
        },
    }

    results = {}

    with console.status("[yellow]Running sanity checks...", spinner="dots") as status:
        for check, func in CHECKS["REQUIRED"].items():
            status.update(f"[yellow]Checking {check}...")
            results[check] = func()
            time.sleep(0.25)

        if CHECKS["OPTIONAL"]:
            for check, func in CHECKS["OPTIONAL"].items():
                if func is not None:
                    status.update(f"[yellow]Checking optional: {check}...")
                    results[check] = func()
                    time.sleep(0.25)

    sanity_table = create_table(
        title="",
        columns=[
            ("Check", "white"),
            ("Status", "bright_yellow"),
            ("Message", "bright_yellow"),
        ],
    )

    for check, result in results.items():
        status = "Pass" if result["status"] else "Fail"
        style = "green" if result["status"] else "bright_red"
        message = result["message"]
        sanity_table.add_row(check, status, message, style=style)

    console.print(sanity_table)
    

def about_cli(readme: bool, changelog: bool) -> None:
    documents: List[str] = []
    if readme:
        documents.append("README.md")
    if changelog:
        documents.append("CHANGELOG.md")
    if not documents:
        feedback_message(
            "No document specified. please --readme [-r] or --changelog [-c]", "warning"
        )

    for document in documents:
        try:
            # Try to get the file content from the package resources
            content = pkg_resources.read_text("civitai_models_manager", document)
            # Create a temporary file to pass to display_readme
            with Path(document).open("w", encoding="utf-8") as temp_file:
                temp_file.write(content)
            display_readme(document)
            # Remove the temporary file
            Path(document).unlink()
        except FileNotFoundError:
            # If not found in package resources, try the current directory
            local_path = Path(document)
            if local_path.exists():
                display_readme(str(local_path))
            else:
                typer.echo(f"{document} not found.")