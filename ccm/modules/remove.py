import os
import typer

from rich.console import Console
from rich import print

from .helpers import feedback_message, get_model_folder, create_table, add_rows_to_table
from .utils import convert_kb, clean_text, safe_get

from ccm.config import (MODELS_DIR, CIVITAI_TOKEN, CIVITAI_MODELS, 
                                          CIVITAI_VERSIONS, TYPES, FILE_TYPES, 
                                          OLLAMA_OPTIONS, OPENAI_OPTIONS, GROQ_OPTIONS)

from .list import list_models_cli, list_models
from rich.table import Table

console = Console(soft_wrap=True)

def remove_model(model_path: str) -> bool:
    """Remove the specified model file after user confirmation, checking for permissions."""
    if os.path.exists(model_path):
        
        if not os.access(model_path, os.W_OK):
            feedback_message(f"You do not have permission to remove the model at {model_path}.", "warning")
            return False

        feedback_message(f"This is a desctructive operation and cannot be undone. Please proceed with caution.", "warning")
        confirmation = typer.confirm(f"Are you sure you want to remove the model at {model_path}? (Y/N): ", abort=True)
        if confirmation:
            feedback_message(f"Removing model at {model_path}...", "info")
            total_size = os.path.getsize(model_path)
            with Console.status(f"[pulse] Removing {model_path}") as status:
                try:
                    os.remove(model_path)
                    status.update(f"[green]Model removed successfully. Freed up {convert_kb(total_size)}",
                                  spinner="aesthetic",
                                  spinner_style="bright_yellow")
                    feedback_message(f"Model at {model_path} removed successfully.", "info")
                    return True
                except OSError as e:
                    feedback_message(f"Failed to remove the model at {model_path} // {e}.", "error")
                    return False
        else:
            return False
        
    else:
        feedback_message(f"No model found at {model_path}.", "warning")
    return False


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

    remove_table = create_table("", 
                                [("Model Name", "cyan"), 
                                 ("Model Type", "bright_yellow"), 
                                 ("Path", "bright_yellow")])
    for model in models_in_folder:
        add_rows_to_table(remove_table, {
            "Model Name": model[0],
            "Model Type": model[1],
            "Path": model[2],
        })

    console.print(remove_table)

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