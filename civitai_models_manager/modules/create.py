import os
import civitai 
from pathlib import Path
import enum as Enum
from typing import Dict, List, Final
from questionary import prompt, select, confirm, autocomplete

from civitai_models_manager.modules.helpers import feedback_message
from details import get_model_details_cli


SCHEDULERS: Final[List[str]] = [
    "EulerA", 
    "Euler", 
    "LMS", 
    "Heun", 
    "DPM2", 
    "DPM2A", 
    "DPM2SA", 
    "DPM2M", 
    "DPMSDE", 
    "DPMFast", 
    "DPMAdaptive", 
    "LMSKarras", 
    "DPM2Karras", 
    "DPM2AKarras", 
    "DPM2SAKarras", 
    "DPM2MKarras", 
    "DPMSDEKarras", 
    "DDIM", 
    "PLMS", 
    "UniPC", 
    "Undefined", 
    "LCM", 
    "DDPM", 
    "DEIS"
]

class CreateOptions(Enum):
    MODEL = "What model would you like to use? [Required]"
    PROMPT = "Positive Prompt [Required]"
    NEGATIVE = "Neegative Prompt [Optional]"
    SCHEDULER = "Scheduler [Optional]"
    STEPS = "Steps [Optional]"
    CFG_SCALE = "CFG Scale [Optional]"
    WIDTH_HEIGHT = "Width x Height [Required]"
    CANCEL = "Cancel"


def save_generated_image():
    """
    Save the generated image.
    """
    feedback_message("Saving the generated image...", "info")
    # Save the generated image
    feedback_message("Generated image saved successfully.", "info")


def generate_image(air: str = None, pos_prompt: str = None, width_hieight: str = None):
    """
    Generate the image.
    """
    feedback_message("Generating the image...", "info")
    # Generate the image
    save_generated_image()


def fetch_job_details():
    """
    Fetch job details.
    """
    feedback_message("Fetching job details...", "info")
    # Fetch job details
    feedback_message("Job details fetched successfully.", "info")