import httpx
import subprocess
import questionary
import asyncio
from questionary import Style
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.text import Text
from .helpers import create_table, feedback_message
from .utils import clean_text, format_file_size
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

console = Console(soft_wrap=True)

__all__ = ["search_models", "search_cli", "search_cli_sync"]

custom_style = Style([
    ("qmark", "fg:#ffff00 bold"),
    ("question", "fg:#ffffff bold"),
    ("answer", "fg:#ffff00 bold"),
    ("pointer", "fg:#ffff00 bold"),
    ("highlighted", "fg:#ffff00 bold"),
    ("selected", "fg:#ffff00"),
    ("separator", "fg:#ffff00"),
    ("instruction", "fg:#ffffff"),
    ("text", "fg:#ffffff"),
    ("disabled", "fg:#ffff00 italic"),
])

def pagination_menu(metadata: Dict[str, Any], has_previous: bool, download_function) -> Optional[str]:
    choices = []
    if has_previous:
        choices.append("Previous Page")
    if metadata.get("nextPage"):
        choices.append("Next Page")
    choices.extend(["Download Model", "Exit"])

    action = questionary.select("What would you like to do?", choices=choices, style=custom_style).ask()

    if action == "Previous Page":
        return "prev"
    elif action == "Next Page":
        return "next"
    elif action == "Download Model":
        model_id = questionary.text("Enter the Model ID you want to download:", style=custom_style).ask()
        try:
            model_id = int(model_id)
            subprocess.run(f"civitai-models download {model_id}", shell=True)
        except ValueError:
            print("Invalid Model ID. Please enter a valid number.")
    elif action == "Exit":
        return "exit"
    return None

def validate_param(key: str, value: Any, valid_values: List[str]) -> bool:
    if value not in valid_values and value is not None:
        feedback_message(f"\"{value}\" is not a valid {key}.\nPlease choose from: {', '.join(valid_values)}", "error")
        return False
    return True

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def make_api_request(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

async def search_models(query: str = "", CIVITAI_MODELS=None, TYPES=None, **kwargs) -> Dict[str, Any]:
    allowed_params = {
        "tag": None,
        "types": "Checkpoint",
        "limit": 2,
        "sort": "Highest Rated",
        "period": "AllTime",
        "page": 1,
    }
    params = {**allowed_params, **{k: v for k, v in kwargs.items() if k in allowed_params}}

    if query:
        params["query"] = query

    validations = [
        ("types", params.get("types"), TYPES.keys()),
        ("period", params.get("period"), ["AllTime", "Year", "Month", "Week", "Day"]),
        ("sort", params.get("sort"), ["Highest Rated", "Most Downloaded", "Newest"]),
    ]

    if not all(validate_param(*v) for v in validations):
        return {}

    async with httpx.AsyncClient() as client:
        try:
            return await make_api_request(client, CIVITAI_MODELS, params)
        except RetryError:
            feedback_message("Failed to connect to the API after multiple attempts.", "error")
            return {}
        except httpx.HTTPStatusError as e:
            feedback_message(f"HTTP error occurred: {e}", "error")
            return {}
        except Exception as e:
            feedback_message(f"An unexpected error occurred: {e}", "error")
            return {}

async def search_cli(query: str = "", tag=None, types="Checkpoint", limit=20, sort="Highest Rated", period="AllTime", CIVITAI_MODELS=None, TYPES=None, download_function=None) -> None:
    current_url = CIVITAI_MODELS
    has_previous = False
    page_history = []

    async with httpx.AsyncClient() as client:
        while True:
            with console.status("[yellow]Searching for models...", spinner="dots"):
                try:
                    models = await make_api_request(client, current_url, {
                        "query": query,
                        "tag": tag,
                        "types": types,
                        "limit": limit,
                        "sort": sort,
                        "period": period,
                    })
                except Exception as e:
                    feedback_message(f"Error occurred: {str(e)}", "error")
                    return

            if models.get("items") == []:
                feedback_message("No models found. Please try again.", "warning")
                return

            metadata = models.get("metadata", {})

            search_table = create_table(
                "",
                [
                    ("Model ID", "bright_yellow"),
                    ("Model Name", "white"),
                    ("Model Type", "bright_yellow"),
                    ("Model NSFW", "white"),
                    ("Model Tags", "white"),
                ],
            )

            for model in models.get("items", []):
                name = Text(clean_text(model["name"]), style="bold", overflow="ellipsis")
                tags = Text(", ".join(model["tags"]), style="italic", overflow="ellipsis")
                size = Text(format_file_size(model.get("modelVersions")[0]["files"][0]["sizeKB"]), style="yellow")
                nsfw = Text("Yes", style="green") if model["nsfw"] else Text("No", style="bright_red")
                search_table.add_row(
                    str(model["id"]),
                    f"{name} // [yellow]{size}[/yellow]",
                    model["type"],
                    nsfw,
                    tags,
                )

            console.print(search_table)

            # Run the synchronous pagination_menu in the default event loop
            action = await asyncio.get_event_loop().run_in_executor(None, pagination_menu, metadata, has_previous, download_function)

            if action == "prev":
                if page_history:
                    current_url = page_history.pop()
                    has_previous = bool(page_history)
            elif action == "next":
                if metadata.get("nextPage"):
                    page_history.append(current_url)
                    current_url = metadata["nextPage"]
                    has_previous = True
            elif action == "exit":
                break
            else:
                continue

def search_cli_sync(query: str = "", tag=None, types="Checkpoint", limit=20, sort="Highest Rated", period="AllTime", CIVITAI_MODELS=None, TYPES=None, download_function=None) -> None:
    """
    Synchronous wrapper for the asynchronous search_cli function.
    """
    asyncio.run(search_cli(query, tag, types, limit, sort, period, CIVITAI_MODELS, TYPES, download_function))