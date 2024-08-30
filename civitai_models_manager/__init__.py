import os
from pathlib import Path
from typing import Dict, List, Final
from dotenv import load_dotenv, set_key

from civitai_models_manager.modules.helpers import feedback_message

def get_required_input(prompt: str) -> str:
    """
    Prompt the user for input and ensure a non-empty response.

    :param prompt: The prompt to display to the user.
    :return: The non-empty user input.
    """
    while True:
        response = input(prompt).strip()
        if response:
            return response
        feedback_message("This field is required. Please enter a value.", "warning")

def validate_directory(path: str) -> str:
    """
    Validate that the given path is a directory and create it if it doesn't exist.

    :param path: The directory path to validate.
    :return: The validated directory path.
    """
    dir_path = Path(path).expanduser().resolve()
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True)
            feedback_message(f"Created directory: {dir_path}", "info")
        except Exception as e:
            feedback_message(f"Error creating directory: {e}", "error")
            return validate_directory(get_required_input("Please enter a valid directory path: "))
    elif not dir_path.is_dir():
        feedback_message(f"{dir_path} is not a directory.", "error")
        return validate_directory(get_required_input("Please enter a valid directory path: "))
    return str(dir_path)

def create_env_file(env_path: Path) -> None:
    """
    Create a new .env file with user input for required environment variables.

    :param env_path: Path where the .env file will be created.
    """
    feedback_message(f"Creating new .env file at {env_path}", "info")

    # Ask for CIVITAI_TOKEN
    civitai_token = get_required_input(
        "Enter your CIVITAI_TOKEN (https://developer.civitai.com/docs/getting-started/setup-profile#create-an-api-key): "
    )
    set_key(env_path, "CIVITAI_TOKEN", civitai_token)

    # Ask for MODELS_DIR
    models_dir = validate_directory(get_required_input("Enter the path to your models directory: "))
    set_key(env_path, "MODELS_DIR", models_dir)

    feedback_message(f".env file created successfully at {env_path}", "info")

def load_environment_variables() -> None:
    """
    Load environment variables from a .env file or create one if not found.

    This function searches for the .env file in multiple predefined locations
    across different operating systems. If the file is not found, it provides
    the option to create a new .env file.

    :raises FileNotFoundError: If the .env file is not found in any of the
                               searched locations and user chooses not to create one.
    """
    # Define potential .env file locations
    env_locations: Dict[str, List[str]] = {
        "common": [
            "~/.config/civitai-model-manager/.env",
            "~/.civitai-model-manager/.env",
            "~/.env",
            "./.env",
        ],
        "Windows": [
            "~/AppData/Roaming/civitai-model-manager/.env",
            "~/Documents/civitai-model-manager/.env",
        ],
        "Linux": [
            "~/.local/share/civitai-model-manager/.env",
        ],
        "Darwin": [
            "~/Library/Application Support/civitai-model-manager/.env",
        ],
    }

    # Get the current operating system
    system_platform = os.name

    # Combine common locations with OS-specific locations
    search_paths = env_locations["common"] + env_locations.get(system_platform, [])

    # Search for .env file
    for path in search_paths:
        env_path = Path(path).expanduser().resolve()
        if env_path.is_file():
            load_dotenv(env_path)
            # feedback_message(f"Loaded environment variables from {env_path}", "info")
            return

    # If .env file is not found, provide option to create one
    feedback_message(
        ".env file not found in any of the following locations:", "warning"
    )
    for path in search_paths:
        feedback_message(f"  - {Path(path).expanduser()}", "info")

    create_new = (
        input("Would you like to create a new .env file? (y/n): ").lower().strip()
    )
    if create_new == "y":
        default_path = Path("~/.config/civitai-model-manager/.env").expanduser()
        custom_path = input(
            f"Enter path for new .env file (default: {default_path}): "
        ).strip()
        env_path = Path(custom_path).expanduser() if custom_path else default_path
        env_path.parent.mkdir(parents=True, exist_ok=True)
        create_env_file(env_path)
        load_dotenv(env_path)
    else:
        raise FileNotFoundError("No .env file found and user chose not to create one.")

# Usage
load_environment_variables()

# Set environment variables
os.environ["MODELS_DIR"] = os.getenv("MODELS_DIR", "")
os.environ["CIVITAI_TOKEN"] = os.getenv("CIVITAI_TOKEN", "")
os.environ["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "")
os.environ["OLLAMA_API_BASE"] = os.getenv("OLLAMA_API_BASE", "")
os.environ["TEMP"] = os.getenv("TEMP", "0.4")
os.environ["TOP_P"] = os.getenv("TOP_P", "0.3")
os.environ["HTML_OUT"] = os.getenv("HTML_OUT", "False")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL", "")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
os.environ["GROQ_MODEL"] = os.getenv("GROQ_MODEL", "")

# Define constants
MODELS_DIR: Final = os.environ["MODELS_DIR"]
CIVITAI_TOKEN: Final = os.environ["CIVITAI_TOKEN"]
OLLAMA_MODEL: Final = os.environ["OLLAMA_MODEL"]
OLLAMA_API_BASE: Final = os.environ["OLLAMA_API_BASE"]
TEMP: Final = float(os.environ["TEMP"])
TOP_P: Final = float(os.environ["TOP_P"])
HTML_OUT: Final = os.environ["HTML_OUT"].lower() == "true"
OPENAI_API_KEY: Final = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL: Final = os.environ["OPENAI_MODEL"]
GROQ_API_KEY: Final = os.environ["GROQ_API_KEY"]
GROQ_MODEL: Final = os.environ["GROQ_MODEL"]

CIVITAI_MODELS: Final = "https://civitai.com/api/v1/models"
CIVITAI_IMAGES: Final = "https://civitai.com/api/v1/images"
CIVITAI_VERSIONS: Final = "https://civitai.com/api/v1/model-versions"
CIVITAI_DOWNLOAD: Final = "https://civitai.com/api/download/models"

TYPES: Final = {
    "Checkpoint": "checkpoints",
    "TextualInversion": "embeddings",
    "Hypernetwork": "hypernetworks",
    "AestheticGradient": "aesthetic_embeddings",
    "LORA": "loras",
    "LoCon": "models/Lora",
    "Controlnet": "controlnet",
    "Poses": "poses",
    "Upscaler": "esrgan",
    "MotionModule": "motion_module",
    "VAE": "VAE",
    "Wildcards": "wildcards",
    "Workflows": "workflows",
    "Other": "other",
}

FILE_TYPES = (".safetensors", ".pt", ".pth", ".ckpt")
MODEL_TYPES: Final = [
    "SDXL 1.0",
    "SDXL 0.9",
    "SD 1.5",
    "SD 1.4",
    "SD 2.0",
    "SD 2.0 768",
    "SD 2.1",
    "SD 2.1 768",
    "Other",
]

OLLAMA_OPTIONS: Final = {
    "model": os.getenv("OLLAMA_MODEL", ""),
    "api_base": os.getenv("OLLAMA_API_BASE", ""),
    "temperature": os.getenv("TEMP", 0.9),
    "top_p": os.getenv("TOP_P", 0.3),
    "html_output": os.getenv("HTML_OUT", False),
    "system_template": (
        "You are an expert in giving detailed explanations of description you are provided. Do not present it "
        "like an update log. Make sure to explains the full description in a clear and concise manner. "
        "The description is provided by the CivitAI API and not written by the user, so don't make recommendations "
        "on how to improve the description, just be detailed, clear and thorough about the provided content. "
        "Include information on recommended settings and tip if they appear in the description:\n "
        "- Tips on Usage\n"
        "- Sampling method\n"
        "- Schedule type\n"
        "- Sampling steps\n"
        "- CFG Scale\n"
        "DO NOT OFFER ADVICE ON HOW TO IMPROVE THE DESCRIPTION!!"
        "Return the description in Markdown format.\n\n"
        "You will find the description below: \n\n"
    ),
}

OPENAI_OPTIONS = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"],
}

GROQ_OPTIONS = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"],
}