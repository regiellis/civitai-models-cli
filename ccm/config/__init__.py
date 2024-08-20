import os
from platform import system
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Final
from rich.console import Console
from dotenv import load_dotenv

from ccm.modules.helpers import feedback_message


def load_environment_variables(console: Console = Console()) -> None:
    """
    Load environment variables from .env file.
    
    If the file is not found in the default location, it will be searched in the current directory.
    If still not found, a warning message will be printed to create the file using the sample.env provided.
    """
    env_paths = {
        "Windows": os.path.join(os.path.expanduser("~"), ".env"),
        "Linux": os.path.join(os.path.expanduser("~"), ".config", "civitai-model-manager", ".env"),
        "Darwin": os.path.join(os.path.expanduser("~"), ".config", "civitai-model-manager", ".env")
    }
    
    system_platform = system()
    dotenv_path = env_paths.get(system_platform, ".env")
    
    for path in [Path(dotenv_path), Path(".env")]:
        if path.exists():
            load_dotenv(str(path))
            return
    
    feedback_message(".env file is missing. Please create one using the sample.env provided.", "warning")

load_environment_variables(Console())

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
    "Other": "other"
}

FILE_TYPES = (".safetensors", ".pt", ".pth", ".ckpt")
MODEL_TYPES: Final = ["SDXL 1.0", "SDXL 0.9", "SD 1.5", "SD 1.4", "SD 2.0", "SD 2.0 768", "SD 2.1", "SD 2.1 768", "Other"]

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
    )
}

OPENAI_OPTIONS = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"]
}

GROQ_OPTIONS = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", ""),
    "system_template": OLLAMA_OPTIONS["system_template"]
}
