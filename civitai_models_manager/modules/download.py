import os
import asyncio
import httpx
import typer
from typing import Any, List, Dict, Optional, Tuple
from tqdm import tqdm
from rich.console import Console
from .helpers import feedback_message, get_model_folder, create_table
from .details import get_model_details

__all__ = ["download_model_cli"]

console = Console(soft_wrap=True)

MAX_RETRIES = 3
TIMEOUT = 30  # seconds
MAX_CONCURRENT_DOWNLOADS = 3

async def select_version(
    model_name: str, versions: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    feedback_message(
        f"Please select a version to download for model {model_name}.", "info"
    )

    versions_table = create_table(
        "Available Versions",
        [
            ("Version ID", "bright_yellow"),
            ("Version Name", "cyan"),
            ("Base Model", "blue"),
        ],
    )

    for version in versions:
        versions_table.add_row(
            str(version["id"]), version["name"], version["base_model"]
        )

    console.print(versions_table)
    selected_version_id = await asyncio.to_thread(typer.prompt, "Enter the version ID to download:")

    for version in versions:
        if str(version["id"]) == selected_version_id:
            return version

    feedback_message(
        f"Version {selected_version_id} is not available for model {model_name}.",
        "error",
    )
    return None

async def check_for_upgrade(model_path: str, selected_version: Dict[str, Any]) -> bool:
    current_version = os.path.basename(model_path)
    if current_version != selected_version["file"]:
        feedback_message(
            f"A newer version '{selected_version['file']}' is available.", "info"
        )
        return await asyncio.to_thread(typer.confirm, "Do you want to upgrade?")
    return False

async def download_model(
    MODELS_DIR: str,
    CIVITAI_DOWNLOAD: str,
    CIVITAI_TOKEN: str,
    TYPES,
    model_id: int,
    model_details: Dict[str, Any],
    select: bool = False,
) -> Optional[str]:
    model_name = model_details.get("name", f"Model_{model_id}")
    model_type = model_details.get("type", "unknown")
    model_meta = model_details.get("metadata", {})
    versions = model_details.get("versions", [])

    if not versions and not model_details.get("parent_id"):
        feedback_message(f"No versions available for model {model_name}.", "warning")
        return None

    if not select and not model_details.get("parent_id"):
        selected_version = versions[0]
    elif not select and model_details.get("parent_id"):
        selected_version = {
            "id": model_id,
            "name": model_details.get("name", ""),
            "base_model": model_details.get("base_model", ""),
            "download_url": model_details.get("download_url", ""),
            "images": model_details["images"][0].get("url", ""),
            "file": model_meta.get("file", ""),
        }
    else:
        if model_details.get("parent_id"):
            feedback_message(
                f"Model {model_name} is a variant of {model_details['parent_name']} // Model ID: {model_details['parent_id']} \r Needs to be a parent model",
                "warning",
            )
            return None
        selected_version = await select_version(model_name, versions)

    if not selected_version:
        feedback_message(f"A version is not available for model {model_name}.", "error")
        return None

    model_folder = get_model_folder(MODELS_DIR, model_type, TYPES)
    model_path = os.path.join(
        model_folder,
        selected_version.get("base_model", ""),
        selected_version.get("file"),
    )

    if os.path.exists(model_path):
        if not await check_for_upgrade(model_path, selected_version):
            feedback_message(
                f"Model {model_name} already exists at {model_path}. Skipping download.",
                "warning",
            )
            return None

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    return await download_file(
        f"{CIVITAI_DOWNLOAD}/{selected_version['id']}?token={CIVITAI_TOKEN}",
        model_path,
        model_name,
    )

async def download_file(url: str, path: str, desc: str) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        for attempt in range(MAX_RETRIES):
            try:
                async with client.stream("GET", url, follow_redirects=True, timeout=TIMEOUT) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    with open(path, "wb") as f, tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        desc=f"Downloading {desc}",
                        colour="cyan",
                    ) as progress_bar:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress_bar.update(len(chunk))
                return path
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    feedback_message(f"Download failed. Retrying in {wait_time} seconds...", "warning")
                    await asyncio.sleep(wait_time)
                else:
                    feedback_message(
                        f"Failed to download the file after {MAX_RETRIES} attempts: {e} // Please check if you have permission to download files to the specified path.",
                        "error",
                    )
                    return None

async def download_multiple_models(identifiers: List[str], select: bool, **kwargs) -> List[Tuple[str, Optional[str]]]:
    tasks = []
    for identifier in identifiers[:MAX_CONCURRENT_DOWNLOADS]:
        task = asyncio.create_task(download_single_model(identifier, select, **kwargs))
        tasks.append(task)
    
    return await asyncio.gather(*tasks)

async def download_single_model(identifier: str, select: bool, **kwargs) -> Tuple[str, Optional[str]]:
    try:
        model_id = int(identifier)
        model_details = await asyncio.to_thread(
            get_model_details,
            kwargs.get("CIVITAI_MODELS"),
            kwargs.get("CIVITAI_VERSIONS"),
            model_id
        )
        types = kwargs.get("TYPES")

        if model_details:
            model_path = await download_model(
                kwargs.get("MODELS_DIR"),
                kwargs.get("CIVITAI_DOWNLOAD"),
                kwargs.get("CIVITAI_TOKEN"),
                types,
                model_id,
                model_details,
                select,
            )
            if model_path:
                feedback_message(
                    f"Model {identifier} downloaded successfully at: {model_path}", "info"
                )
                return identifier, model_path
            else:
                if model_path is not None:
                    feedback_message(f"Failed to download the model {identifier}.", "error")
        else:
            feedback_message(f"No model found with ID: {identifier}.", "error")
    except ValueError:
        feedback_message(f"Invalid model ID: {identifier}. Please enter a valid number.", "error")
    
    return identifier, None

async def download_model_cli(identifiers: List[str], select: bool = False, **kwargs) -> None:
    if not identifiers:
        feedback_message("No model identifiers provided.", "error")
        return

    await download_multiple_models(identifiers, select, **kwargs)
    



