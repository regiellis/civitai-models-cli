# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer",
#   "rich",
#   "httpx",
#   "shellingham",
#   "html2text",
#   "python-dotenv",
#   "ollama",
#   "openai",
#   "groq"
# ]
# ///

import typer

from typing import Optional
from civitai_models_manager.__version__ import __version__
from civitai_models_manager import (
    MODELS_DIR,
    CIVITAI_TOKEN,
    CIVITAI_MODELS,
    CIVITAI_DOWNLOAD,
    CIVITAI_VERSIONS,
    TYPES,
    FILE_TYPES,
    OLLAMA_OPTIONS,
    OPENAI_OPTIONS,
    GROQ_OPTIONS,
)
from typing import List
from pathlib import Path
import importlib.resources as pkg_resources
from .modules.helpers import feedback_message, display_readme
from .modules.tools import sanity_check_cli
from .modules.stats import inspect_models_cli
from .modules.details import get_model_details_cli
from .modules.list import list_models_cli, local_search_cli
from .modules.download import download_model_cli
from .modules.ai import explain_model_cli
from .modules.search import search_cli_sync
from .modules.remove import remove_models_cli
from .modules.create import create_image_cli

from rich.traceback import install

install()

"""
====================================================================
Civitai Model Manager - Simplified Model Retrieval and Management
====================================================================

Simple CLI tool that streamlines the process of managing AI models from the
CivitAI platform. It offers functionalities to list available models,it
view their details, search, download selected variants, and remove models from
local storage. It also provides a summary of the model description using
Ollama or OpenAI.

Usage:
$ pipx install civitai-models or pip install civitai-models [not on pip yet]
$ pip install . or pipx install . # To install the package locally (recommended)
$ civitai-model-manager [OPTIONS] [COMMAND] [ARGS]

Options:
    [stats] details INT                   Get detailed information about a specific model by ID.
    download INT                          Download a specific model variant by ID.
    [tools] explain INT                   Get a summary of a specific model by ID.
    [stats] details                       List available models along with their types and paths.
    [stats] overview                      Stats on the parent models directory.
    [tools] sanity-check                  Check to see if the app is ready to run.
    search TEXT --query                   Search for models by query, tag, or types, which are optional via the API.
    remove                                Remove specified models from local storage.
    --help                                Show this message and exit.

Examples:

$ civitai-models about [about] [readme]
$ civitai-models details 12345 [desc] [images]
$ civitai-models download 54321 [--select]
$ civitai-models remove
$ civitai-models search  "text" [--tag "tag1"] [--types "Checkpoint"] [--limit 20] [--sort "Highest Rated"] [--period "AllTime"]
$ civitai-models stats [overview] [details]
$ civitai-models tools explain 12345 [--service ollama]
$ civitai-models tools sanity-check

"""

__version__ = __version__

__all__ = ["civitai_cli"]

civitai_cli = typer.Typer()
about_group = typer.Typer()
stats_group = typer.Typer()
search_group = typer.Typer()
create_group = typer.Typer()
tools_group = typer.Typer()


civitai_cli.add_typer(
    about_group,
    name="about",
    help="Details about the civitai-model-manager.",
    no_args_is_help=True,
)

civitai_cli.add_typer(
    stats_group,
    name="stats",
    help="Functions for stats on the models directory.",
    no_args_is_help=True,
)

civitai_cli.add_typer(
    create_group,
    name="generate",
    help="Generate images or track a Job on the CivitAI platform.",
    no_args_is_help=True,
)

civitai_cli.add_typer(
    search_group,
    name="search",
    help="Functions to search for models locally or on CivitAI.",
    no_args_is_help=True,
)

civitai_cli.add_typer(
    tools_group,
    name="tools",
    help="Miscellaneous tools",
    no_args_is_help=True,
)


@search_group.command(
    "civitai",
    help="Search for models by query, tag, or types, which are optional via the API.",
)
def search_models_command(
    query: str = typer.Argument("", help="Search query"),
    tag: Optional[str] = typer.Option("", help="Filter by tag"),
    types: str = typer.Option("Checkpoint", help="Filter by model type"),
    limit: int = typer.Option(20, help="Limit the number of results"),
    sort: str = typer.Option("Highest Rated", help="Sort order for results"),
    period: str = typer.Option("AllTime", help="Time period for results"),
):
    search_cli_sync(
        query,
        tag,
        types,
        limit,
        sort,
        period,
        CIVITAI_MODELS=CIVITAI_MODELS,
        TYPES=TYPES,
    )


@search_group.command("local", help="Search for models stored on disk.")
def local_search_command(
    query: str = typer.Argument("", help="Search query"),
):
    return local_search_cli(query, MODELS_DIR=MODELS_DIR, FILE_TYPES=FILE_TYPES)


@tools_group.command(
    "explain",
    help="Get a summary of a specific model by ID using the specified service (default is Ollama).",
)
def explain_model_command(
    identifier: str = typer.Argument("", help="The ID of the model"),
    service: str = typer.Option("ollama", help="The specified service to use"),
):
    """
    Get a summary of a specific model by ID using the specified service (default is Ollama).
    :param identifier: The ID of the model.
    :param service: The specified service to use (default is "ollama").
    """
    explain_model_cli(
        identifier,
        service,
        CIVITAI_MODELS=CIVITAI_MODELS,
        CIVITAI_VERSIONS=CIVITAI_VERSIONS,
        OLLAMA_OPTIONS=OLLAMA_OPTIONS,
        OPENAI_OPTIONS=OPENAI_OPTIONS,
        GROQ_OPTIONS=GROQ_OPTIONS,
    )


@tools_group.command("sanity-check", help="Check to see if the app is ready to run.")
def sanity_check_command():
    """
    Check to see if the app is ready to run.
    :return: The result of the sanity check.
    """
    return sanity_check_cli(
        CIVITAI_MODELS=CIVITAI_MODELS,
        CIVITAI_VERSIONS=CIVITAI_VERSIONS,
        OLLAMA_OPTIONS=OLLAMA_OPTIONS,
        OPENAI_OPTIONS=OPENAI_OPTIONS,
        GROQ_OPTIONS=GROQ_OPTIONS,
    )


@create_group.command("image", help="Generate a image on the CivitAI platform.")
def create_image_command(
    model: int = typer.Argument(0, help="The ID of the model"),
):
    """
    Generate a image on the CivitAI platform.
    :return: The result of the image creation.
    """
    # create_image_cli(CIVITAI_MODELS, CIVITAI_VERSIONS, model)
    return feedback_message("Coming in v0.8.6", "info")


@create_group.command("check-jobs", help="Fetch jobs details based on token or Job ID.")
def fetch_job_command(
    token: str = typer.Argument(None, help="CivitAI token"),
    query: str = typer.Argument(None, help="Search query"),
    is_job_id: int = typer.Option(False, help="Whether the token is a Job ID"),
    cancel: bool = False,
):
    """
    Fetch jobs details based on token or Job ID.
    :return: The result of the job details.
    """
    return feedback_message("Coming in v0.8.6", "info")


@stats_group.command(
    "by-type", help="List available models along with their types and paths."
)
def list_models_command():
    """
    List available models along with their types and paths.
    :return: The list of available models.
    """
    return list_models_cli()


@stats_group.command("overview", help="Stats on the parent models directory.")
def stats_command():
    """
    Stats on the parent models directory.
    :return: The stats on the parent models directory.
    """
    return inspect_models_cli(MODELS_DIR=MODELS_DIR)


@civitai_cli.command(
    "details", help="Get detailed information about a specific model by ID."
)
def details_command(
    identifier: str = typer.Argument("", help="The ID of the model"),
    desc: bool = typer.Option(
        False, "--desc", "-d", help="The description of the model"
    ),
    images: bool = typer.Option(
        False, "--images", "-i", help="The images of the model"
    ),
):
    """
    Get detailed information about a specific model by ID.
    :param identifier: The ID of the model.
    :param desc: The description of the model.
    :param images: The images of the model.
    :return: The detailed information about the model.
    """
    return get_model_details_cli(
        identifier,
        desc,
        images,
        CIVITAI_MODELS=CIVITAI_MODELS,
        CIVITAI_VERSIONS=CIVITAI_VERSIONS,
    )


@civitai_cli.command("download", help="Download up to 3 specific model variants by ID.")
def download_model_command(
    identifiers: List[str] = typer.Argument(
        ..., help="The IDs of the models to download (up to 3)"
    ),
    select: bool = typer.Option(
        False, "--select", "-s", help="Enable version selection for each model"
    ),
):
    """
    Download up to 3 specific model variants by ID.
    :param identifiers: The IDs of the models to download (up to 3).
    :param select: Enable version selection for each model.
    :return: None
    """
    if len(identifiers) > 3:
        typer.echo(
            "You can download a maximum of 3 models at a time. Only the first 3 will be processed."
        )
        identifiers = identifiers[:3]

    typer.echo(f"Preparing to download {len(identifiers)} model(s)...")

    return download_model_cli(
        identifiers,
        select,
        MODELS_DIR=MODELS_DIR,
        CIVITAI_MODELS=CIVITAI_MODELS,
        CIVITAI_DOWNLOAD=CIVITAI_DOWNLOAD,
        CIVITAI_VERSIONS=CIVITAI_VERSIONS,
        CIVITAI_TOKEN=CIVITAI_TOKEN,
        TYPES=TYPES,
        FILE_TYPES=FILE_TYPES,
    )


@civitai_cli.command("remove", help="Remove specified models from local storage.")
def remove_models_command():
    """
    Remove specified models from local storage.
    :return: The removal of the models.
    """
    return remove_models_cli(MODELS_DIR=MODELS_DIR, TYPES=TYPES, FILE_TYPES=FILE_TYPES)


@about_group.command("version", help="Current version of the CLI.")
def version_command():
    """
    Current version of the CLI.
    :return: The current version of the CLI.
    """
    return feedback_message(f"Current version: {__version__}", "info")


@about_group.command("docs", help="Show README.md content.")
def about_command(
    readme: bool = typer.Option(
        True, "--readme", "-r", help="Show the README.md content"
    ),
    changelog: bool = typer.Option(
        False, "--changelog", "-c", help="Show the CHANGELOG.md content"
    ),
):
    """
    Show README.md and/or CHANGELOG.md content.
    """
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
