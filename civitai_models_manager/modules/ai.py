import os
import warnings
import html2text
from pathlib import Path
from typing import Optional
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console

from ollama import Client as OllamaClient
from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient
from .details import get_model_details
from .helpers import feedback_message

# from transformers import pipeline

console = Console(soft_wrap=True)

h2t = html2text.HTML2Text()

current_dir = Path(__file__).resolve().parent
cache_dir = current_dir / "models" / ".cache"
cache_dir.mkdir(parents=True, exist_ok=True)
cache_dir_str = str(cache_dir.resolve())

os.makedirs(f"{cache_dir_str}/transformers", exist_ok=True)
os.makedirs(f"{cache_dir_str}/datasets", exist_ok=True)

os.environ["HF_HOME"] = str(cache_dir_str)
os.environ["TRANSFORMERS_CACHE"] = f"{cache_dir_str}/transformers"
os.environ["HF_DATASETS_CACHE"] = f"{cache_dir_str}/datasets"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

warnings.filterwarnings(
    "ignore", message=".*`clean_up_tokenization_spaces` was not set.*"
)

# explainer = pipeline("summarization", model="google-t5/t5-large", device="cuda:0", clean_up_tokenization_spaces=True)

# TODO: Fix download for every command
# def explain_model_description(desc: str) -> Optional[str]:

#     if not desc:
#         feedback_message("No description available to summarize", "warning")
#         return None

#     try:
#         desc = html2text.html2text(desc)
#         summary = explainer(desc, max_length=len(desc), min_length=30, early_stopping=False)
#         return summary[0]["summary_text"]
#     except Exception as e:
#         feedback_message(f"Failed to summarize the model description // {e}", "error")
#         return None


# TODO: Fix the markdown output
def summarize_model_description(
    model, model_id: int, service: str, **kwargs
) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = model
    description = model_details.get("description", "No description available.")

    # explanation = explain_model_description(description)
    # print(explanation)
    # return

    try:
        if service == "ollama" and kwargs.get("Ollama"):
            response = kwargs.get("Ollama").chat(
                model=kwargs.get("OLLAMA_OPTIONS")["model"],
                messages=[
                    {
                        "role": "assistant",
                        "content": kwargs.get("OLLAMA_OPTIONS")["system_template"],
                    },
                    {
                        "role": "user",
                        "content": f"{kwargs.get('OLLAMA_OPTIONS')['system_template']} : {description}",
                    },
                    # consider adding the system template
                    # to the prompt since not all models follow it
                ],
                options={
                    "temperature": float(kwargs.get("OLLAMA_OPTIONS")["temperature"]),
                    "top_p": float(kwargs.get("OLLAMA_OPTIONS")["top_p"]),
                },
                keep_alive=0,  # Free up the VRAM
            )
            if "message" in response and "content" in response["message"]:
                if not kwargs.get("OLLAMA_OPTIONS")["html_output"]:
                    return h2t.handle(response["message"]["content"])
                else:
                    return Markdown(response["message"]["content"], justify="left")

        elif service == "openai" and kwargs.get("OpenAI"):
            feedback_message(
                "OpenAI may not display due to content censorship\nconsider using a uncensored local model",
                "warning",
            )

            response = kwargs.get("OpenAI").chat.completions.create(
                model=kwargs.get("OPENAI_OPTIONS")["model"],
                messages=[
                    {
                        "role": "assistant",
                        "content": kwargs.get("OPENAI_OPTIONS")["system_template"],
                    },
                    {"role": "user", "content": description},
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

        elif service == "groq" and kwargs.get("Groq"):
            feedback_message(
                "OpenAI may not display due to content censorship \n consider using a uncensored local model",
                "warning",
            )
            response = kwargs.get("Groq").chat.completions.create(
                model=kwargs.get("GROQ_OPTIONS")["model"],
                messages=[
                    {
                        "role": "assistant",
                        "content": kwargs.get("GROQ_OPTIONS")["system_template"],
                    },
                    {"role": "user", "content": description},
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

    except Exception as e:
        feedback_message(
            f"Failed to summarize the model description using {service} // {e}", "error"
        )
        return None


def explain_model_cli(identifier: str, service: str = "ollama", **kwargs) -> None:
    Ollama = (
        OllamaClient(kwargs.get("OLLAMA_OPTIONS")["api_base"])
        if kwargs.get("OLLAMA_OPTIONS")["api_base"]
        else None
    )
    OpenAI = (
        OpenAIClient(api_key=kwargs.get("OPENAI_OPTIONS")["api_key"])
        if kwargs.get("OPENAI_OPTIONS")["api_key"]
        else None
    )
    Groq = (
        GroqClient(api_key=kwargs.get("GROQ_OPTIONS")["api_key"])
        if kwargs.get("GROQ_OPTIONS")["api_key"]
        else None
    )

    try:
        model = get_model_details(
            kwargs.get("CIVITAI_MODELS"), kwargs.get("CIVITAI_VERSIONS"), identifier
        )
        model_id = model.get("id", "")
        model_name = model.get("name", "")

        with console.status(
            f"[yellow]Asking {service} to explain model description", spinner="dots"
        ) as status:
            summary = summarize_model_description(
                model,
                model_id,
                service,
                Ollama=Ollama,
                OpenAI=OpenAI,
                Groq=Groq,
                OLLAMA_OPTIONS=kwargs.get("OLLAMA_OPTIONS"),
                OPENAI_OPTIONS=kwargs.get("OPENAI_OPTIONS"),
                GROQ_OPTIONS=kwargs.get("GROQ_OPTIONS"),
            )
            status.update(f"[green]Summary completed for {model_name}")

        summary_table = Table(title_justify="left")
        summary_table.add_column(
            f"Explanation of model {model_name} // {model_id} using {service}:",
            style="cyan",
        )
        summary_table.add_row(summary or "No summary available.")

        console.print(summary_table)

    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")
