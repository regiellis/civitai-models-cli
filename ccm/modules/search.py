import httpx
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from rich import print
from rich.text import Text

from ccm.config import (MODELS_DIR, CIVITAI_TOKEN, CIVITAI_MODELS, 
                                          CIVITAI_VERSIONS, TYPES, FILE_TYPES, 
                                          OLLAMA_OPTIONS, OPENAI_OPTIONS, GROQ_OPTIONS)

from rich.table import Table
from .utils import convert_kb, clean_text

console = Console(soft_wrap=True)

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
    
    request = httpx.get(CIVITAI_MODELS, params=params)
    if request.status_code == 200:
        response = request.json()
        return response
    return []

# TODO: Fix table formatting for name and tags (emjois are breaking the table)
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