import os
import typer
import questionary
from questionary import Style
from typing import List, Tuple

from rich.console import Console
from .helpers import feedback_message, get_model_folder, create_table
from .utils import format_file_size
from .list import list_models


console = Console(soft_wrap=True)


def group_models_alphabetically(models: List[Tuple[str, str, str, str]]) -> dict:
    grouped = {}
    for model in models:
        first_letter = model[0][0].upper()
        if first_letter not in grouped:
            grouped[first_letter] = []
        grouped[first_letter].append(model)
    return grouped


def select_models_to_delete(
    models_in_folder: List[Tuple[str, str, str, str]]
) -> List[Tuple[str, str, str, str]]:
    custom_style = Style(
        [
            ("qmark", "fg:#ffff00 bold"),  # Yellow question mark
            ("question", "fg:#ffffff bold"),  # White bold question text
            ("answer", "fg:#ffff00 bold"),  # Yellow bold answer text
            ("pointer", "fg:#ffff00 bold"),  # Yellow bold pointer
            (
                "highlighted",
                "fg:#000000 bg:#00FFFF bold",
            ),  # black text on cyan background for highlighted items
            ("selected", "fg:#ffff00"),  # Yellow for selected items
            ("separator", "fg:#ffff00"),  # Yellow separator
            ("instruction", "fg:#ffffff"),  # White instruction text
            ("text", "fg:#ffffff"),  # White general text
            ("disabled", "fg:#ffff00 italic"),  # Yellow italic for disabled items
        ]
    )

    # Ask if the user needs to delete more than one model
    multiple_delete = questionary.confirm(
        "Do you need to delete more than one model?", style=custom_style
    ).ask()

    if multiple_delete:
        # If yes, provide checkbox options
        grouped_models = group_models_alphabetically(models_in_folder)

        choices = []
        for letter, models in sorted(grouped_models.items()):
            choices.append({"name": f"--- {letter} ---", "disabled": True})
            choices.extend(
                [{"name": model[0], "value": model} for model in sorted(models)]
            )

        selected_models = questionary.checkbox(
            "Select models to delete", choices=choices, style=custom_style
        ).ask()

        return selected_models
    else:
        # If no, let the user enter a single model name
        model_name = questionary.text(
            "Enter the name of the model to delete:", style=custom_style
        ).ask()

        # Find the first model that starts with the user's input (case-insensitive)
        matching_model = next(
            (
                model
                for model in models_in_folder
                if model[0].lower().startswith(model_name.lower())
            ),
            None,
        )

        # If a match is found, return it in a list; otherwise, return None or handle the error as needed
        return [matching_model] if matching_model else []


def remove_model(model_path: str) -> bool:
    if os.path.exists(model_path):
        if not os.access(model_path, os.W_OK):
            feedback_message(
                f"You do not have permission to remove the model at {model_path}.",
                "warning",
            )
            return False

        total_size = os.path.getsize(model_path)
        try:
            os.remove(model_path)
            feedback_message(
                f"Model at {model_path} removed successfully. Freed up {format_file_size(total_size)}",
                "info",
            )
            return True
        except OSError as e:
            feedback_message(
                f"Failed to remove the model at {model_path} // {e}.", "error"
            )
            return False
    else:
        feedback_message(f"No model found at {model_path}.", "warning")
    return False


def remove_models_cli(**kwargs):
    model_types_list = list(kwargs.get("TYPES").keys())

    console.print("Available model types for deletion:")
    for index, model_type in enumerate(model_types_list, start=1):
        console.print(f"{index}. {model_type}")

    model_type_index = typer.prompt(
        "Enter the number corresponding to the type of model you would like to delete"
    )

    try:
        model_type = model_types_list[int(model_type_index) - 1]
    except (IndexError, ValueError):
        feedback_message(
            f"Invalid selection. Please enter a valid number. // {str(ValueError)}",
            "error",
        )
        return

    model_folder = get_model_folder(
        kwargs.get("MODELS_DIR"), model_type, kwargs.get("TYPES")
    )
    models_in_folder = list_models(model_folder, kwargs.get("FILE_TYPES"))

    if not models_in_folder:
        feedback_message(f"No models found for type {model_type}.", "warning")
        return

    remove_table = create_table(
        "",
        [
            ("Model Name", "cyan"),
            ("Model Type", "bright_yellow"),
            ("Path", "bright_yellow"),
        ],
    )
    for model in models_in_folder:
        remove_table.add_row(model[0], model[1], model[2])

    console.print(remove_table)

    # model_version_ids = typer.prompt("Enter the model name you wish to delete (comma-separated):")

    selected_models = select_models_to_delete(models_in_folder)

    if selected_models:
        # No need to filter models_in_folder, as selected_models already contains full tuples
        models_to_delete = selected_models

        if not models_to_delete:
            console.print("No matching model found for deletion.", style="bright_red")
            return
        feedback_message(
            "This is a destructive operation and cannot be undone. Please proceed with caution.",
            "warning",
        )
        confirmation = typer.confirm(
            f"Are you sure you want to remove the model at {model[0]}? ", abort=True
        )
        if confirmation:
            for model in models_to_delete:
                remove_model(model[2])
    else:
        console.print("No model selected for deletion.", style="bright_red")
