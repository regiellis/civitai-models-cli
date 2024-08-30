import os
from pathlib import Path
from typing import Dict, List, Final
from dotenv import load_dotenv

from civitai_models_manager.modules.helpers import feedback_message


def load_environment_variables() -> None:
    """
    Load environment variables from a .env file.

    This function searches for the .env file in multiple predefined locations
    across different operating systems. If the file is not found, it provides
    informative feedback to the user about where to create the .env file.

    :raises FileNotFoundError: If the .env file is not found in any of the
                               searched locations.

    **Search Locations**:

    - Common:
      - `~/.config/civitai-model-manager/.env`
      - `~/.civitai-model-manager/.env`
      - `~/.env`
      - `./.env`

    - Windows:
      - `~/AppData/Roaming/civitai-model-manager/.env`
      - `~/Documents/civitai-model-manager/.env`

    - Linux:
      - `~/.local/share/civitai-model-manager/.env`

    - Darwin (macOS):
      - `~/Library/Application Support/civitai-model-manager/.env`
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

    # If .env file is not found, provide detailed feedback
    feedback_message(
        ".env file not found in any of the following locations:", "warning"
    )
    for path in search_paths:
        feedback_message(f"  - {Path(path).expanduser()}", "info")

    feedback_message(
        "\nPlease create a .env file in one of the above locations using the sample.env provided.",
        "warning",
    )
    feedback_message(
        "Recommended location: ~/.config/civitai-model-manager/.env", "info"
    )


# Usage
load_environment_variables()

MODELS_DIR: Final = os.getenv("MODELS_DIR", "")
CIVITAI_TOKEN: Final = os.getenv("CIVITAI_TOKEN", "")

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
