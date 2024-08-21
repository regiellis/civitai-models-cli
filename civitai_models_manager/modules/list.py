import os
import questionary
from questionary import Style

from typing import List, Tuple, Dict, Optional
from rich.console import Console
from .helpers import (feedback_message, get_model_folder, 
                      create_table, add_rows_to_table)
from .utils import format_file_size, sort_models
from civitai_models_manager import (MODELS_DIR, FILE_TYPES, TYPES)

__all__ = [
    "list_models_cli",
    "display_models_table",
    "list_models",
    "select_model_type",
]

console = Console(soft_wrap=True)

custom_style = Style([
    ('qmark', 'fg:#ffff00 bold'),        # Yellow question mark
    ('question', 'fg:#ffffff bold'),     # White bold question text
    ('answer', 'fg:#ffff00 bold'),       # Yellow bold answer text
    ('pointer', 'fg:#ffff00 bold'),      # Yellow bold pointer
    ('highlighted', 'fg:#000000 bg:#00FFFF bold'),  # black text on cyan background for highlighted items
    ('selected', 'fg:#ffff00'),          # Yellow for selected items
    ('separator', 'fg:#ffff00'),         # Yellow separator
    ('instruction', 'fg:#ffffff'),       # White instruction text
    ('text', 'fg:#ffffff'),              # White general text
    ('disabled', 'fg:#ffff00 italic')    # Yellow italic for disabled items
])


def list_models(model_dir: str, file_types: List[str]) -> List[Tuple[str, str, str]]:
    """List models in a given directory."""
    models = []
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith(tuple(file_types)):
                model_path = os.path.join(root, file)
                model_name = os.path.splitext(file)[0]
                model_type = os.path.basename(root)
                model_size = format_file_size(os.path.getsize(model_path))
                models.append((model_name, model_type, model_path, model_size))
    return sort_models(models)


def display_models_table(models: List[Tuple[str, str, str]], model_type: str) -> None:
    """Display a table of models."""
    if not models:
        feedback_message(f"No models found for type {model_type}.", "warning")
        return

    list_table = create_table(title="",
                         columns=[(f"{model_type}s", "bright_yellow"), ("Path", "white")])
    for model_name, _, model_path, model_size in models:
        add_rows_to_table(list_table, {model_name: f"{model_path} [bold][yellow]{model_size}[/yellow][/bold]"})
        
    console.print(list_table)


def select_model_type(types: Dict[str, str]) -> Optional[str]:
    """Prompt user to select a model type."""
    choices = list(types.keys()) + ["Exit"]
    selected = questionary.select(
        "Select the type of model you would like to list (or 'Exit' to quit):",
        choices=choices,
        style=custom_style
    ).ask()
    return selected if selected != "Exit" else None


def list_models_cli() -> None:
    """List available models along with their types and paths."""
    while True:
        model_type = select_model_type(TYPES)
        if model_type is None:
            return

        model_folder = get_model_folder(MODELS_DIR, model_type, TYPES)
        models_in_folder = list_models(model_folder, FILE_TYPES)
        display_models_table(models_in_folder, model_type)

        if not questionary.confirm(
            "Would you like to list another type of model?"
        ).ask():
            return
