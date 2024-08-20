# -*- coding: utf-8 -*-

import html2text
from typing import Optional
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console

from ollama import Client as OllamaClient
from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient
from .details import get_model_details
from .helpers import feedback_message

console = Console(soft_wrap=True)

h2t = html2text.HTML2Text()

# TODO: Fix the markdown output
def summarize_model_description(model_id: int, service: str, **kwargs) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = get_model_details(kwargs.get("CIVITAI_MODELS"), kwargs.get("CIVITAI_VERSIONS"), model_id)
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and kwargs.Ollama:
            response = kwargs.Ollama.chat(
                model=kwargs.OLLAMA_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.OLLAMA_OPTIONS["system_template"]},
                    {"role": "user", "content": f"{kwargs.OLLAMA_OPTIONS['system_template']} {description}"}
                    # consider adding the system template
                    # to the prompt since not all models follow it
                ],
                options={"temperature": float(kwargs.OLLAMA_OPTIONS["temperature"]), "top_p": float(kwargs.OLLAMA_OPTIONS["top_p"])},
                keep_alive=0 # Free up the VRAM
            )
            if 'message' in response and 'content' in response['message']:
                if not kwargs.OLLAMA_OPTIONS["html_output"]:
                    return h2t.handle(response['message']['content'])
                else:
                    return Markdown(response['message']['content'], justify="left")

        elif service == "openai" and kwargs.OpenAI:
            response = kwargs.OpenAI.chat.completions.create(
                model=kwargs.OPENAI_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.OPENAI_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

        elif service == "groq" and kwargs.Groq:
            response = kwargs.Groq.chat.completions.create(
                model=kwargs.GROQ_OPTIONS["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.GROQ_OPTIONS["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

    except Exception as e:
        feedback_message(f"Failed to summarize the model description using {service} // {e}", "error")
        return None


def explain_model_cli(identifier: str, service: str = "ollama", **kwargs) -> None:
    """Get a summary of a specific model by ID using the specified service (default is Ollama)."""

    Ollama = OllamaClient(kwargs.get("OLLAMA_OPTIONS")["api_base"]) if kwargs.get("OLLAMA_OPTIONS")["api_base"] else None
    OpenAI = OpenAIClient(api_key=kwargs.get("OPENAI_OPTIONS")["api_key"]) if kwargs.get("OPENAI_OPTIONS")["api_key"] else None
    Groq = GroqClient(api_key=kwargs.get("GROQ_OPTIONS")["api_key"]) if kwargs.get("GROQ_OPTIONS")["api_key"] else None

    try:
        model = get_model_details(kwargs.get("CIVITAI_MODELS"), kwargs.get("CIVITAI_VERSIONS"), int(identifier))
        model_id = model.get("id", "")
        model_name = model.get("name", "")
        summary = summarize_model_description(model_id, service, Ollama=Ollama, OpenAI=OpenAI, Groq=Groq, 
                                              OLLAMA_OPTIONS=kwargs.get("OLLAMA_OPTIONS"), OPENAI_OPTIONS=kwargs.get("OPENAI_OPTIONS"), 
                                              GROQ_OPTIONS=kwargs.get("GROQ_OPTIONS"))

        summary_table = Table(title_justify="left")
        summary_table.add_column(f"Explaination of model {model_name}/{model_id} using {service}:", style="cyan")
        summary_table.add_row(summary)

        console.print(summary_table)
    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")