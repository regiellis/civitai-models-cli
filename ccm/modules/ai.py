# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Tuple, Final

import html2text
from rich.markdown import Markdown

from ollama import Client as OllamaClient
from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient

from ccm.config import (MODELS_DIR, CIVITAI_TOKEN, CIVITAI_MODELS, 
                                          CIVITAI_VERSIONS, TYPES, FILE_TYPES, 
                                          OLLAMA_OPTIONS, OPENAI_OPTIONS, GROQ_OPTIONS)

from .details import get_model_details_cli, get_model_details
from .helpers import feedback_message, get_model_folder
from rich.table import Table
from rich.text import Text
from rich.console import Console

console = Console(soft_wrap=True)

Ollama = OllamaClient(OLLAMA_OPTIONS["api_base"]) if OLLAMA_OPTIONS["api_base"] else None
OpenAI = OpenAIClient(api_key=OPENAI_OPTIONS["api_key"]) if OPENAI_OPTIONS["api_key"] else None
Groq = GroqClient(api_key=GROQ_OPTIONS["api_key"]) if GROQ_OPTIONS["api_key"] else None

h2t = html2text.HTML2Text()

# TODO: Fix the markdown output
def summarize_model_description(model_id: int, service: str) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = get_model_details(CIVITAI_MODELS, CIVITAI_VERSIONS, model_id)
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and Ollama:
            response = Ollama.chat(
                model=OLLAMA_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": OLLAMA_OPTIONS["system_template"]},
                    {"role": "user", "content": f"{OLLAMA_OPTIONS['system_template']} {description}"}
                    # consider adding the system template
                    # to the prompt since not all models follow it
                ],
                options={"temperature": float(OLLAMA_OPTIONS["temperature"]), "top_p": float(OLLAMA_OPTIONS["top_p"])},
                keep_alive=0 # Free up the VRAM
            )
            if 'message' in response and 'content' in response['message']:
                if not OLLAMA_OPTIONS["html_output"]:
                    return h2t.handle(response['message']['content'])
                else:
                    return Markdown(response['message']['content'], justify="left")
                
        elif service == "openai" and OpenAI:
            response = OpenAI.chat.completions.create(
                model=OPENAI_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": OPENAI_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

        elif service == "groq" and Groq:
            response = Groq.chat.completions.create(
                model=GROQ_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": GROQ_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

    except Exception as e:
        feedback_message(f"Failed to summarize the model description using {service} // {e}", "error")
        return None


def explain_model_cli(identifier: str, service: str = "ollama"):
    """Get a summary of a specific model by ID using the specified service (default is Ollama)."""
    try:
        model = get_model_details(CIVITAI_MODELS, CIVITAI_VERSIONS, int(identifier))
        model_id = model.get("id", "")
        model_name = model.get("name", "")
        summary = summarize_model_description(model_id, service)
        
        summary_table = Table(title_justify="left")
        summary_table.add_column(f"Summary of model {model_name}/{model_id} using {service}:", style="cyan")
        summary_table.add_row(summary)
        
        console.print(summary_table)
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")