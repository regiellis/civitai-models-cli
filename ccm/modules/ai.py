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
def summarize_model_description(model, model_id: int, service: str, **kwargs) -> Optional[str]:
    """Summarize the model description using the specified API service."""
    model_details = model
    description = model_details.get("description", "No description available.")

    try:
        if service == "ollama" and kwargs.get("Ollama"):
            response = kwargs.get("Ollama").chat(
                model=kwargs.get("OLLAMA_OPTIONS")["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.get("OLLAMA_OPTIONS")["system_template"]},
                    {"role": "user", "content": f"{kwargs.get(\"OLLAMA_OPTIONS\")[\"system_template\"]} : {description}"}
                    # consider adding the system template
                    # to the prompt since not all models follow it
                ],
                options={"temperature": float(kwargs.get("OLLAMA_OPTIONS")["temperature"]), 
                         "top_p": float(kwargs.get("OLLAMA_OPTIONS")["top_p"])},
                keep_alive=0 # Free up the VRAM
            )
            if 'message' in response and 'content' in response['message']:
                if not kwargs.get("OLLAMA_OPTIONS")["html_output"]:
                    return h2t.handle(response['message']['content'])
                else:
                    return Markdown(response['message']['content'], justify="left")

        elif service == "openai" and kwargs.get("OpenAI"):
            
            feedback_message("OpenAI may not display due to content censorship\nconsider using a uncensored local model", "warning")
            
            response = kwargs.get("OpenAI").chat.completions.create(
                model=kwargs.get("OPENAI_OPTIONS")["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.get("OPENAI_OPTIONS")["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

        elif service == "groq" and kwargs.get("Groq"):
            
            feedback_message("OpenAI may not display due to content censorship \n consider using a uncensored local model", "warning")
            response = kwargs.get("Groq").chat.completions.create(
                model=kwargs.get("GROQ_OPTIONS")["model"],
                messages=[
                    {"role": "assistant", "content": kwargs.get("GROQ_OPTIONS")["system_template"]},
                    {"role": "user", "content": description}
                ],
            )
            return Markdown(response.choices[0].message.content, justify="left")

    except Exception as e:
        feedback_message(f"Failed to summarize the model description using {service} // {e}", "error")
        return None


def explain_model_cli(identifier: str, service: str = "ollama", **kwargs) -> None:
    Ollama = OllamaClient(kwargs.get("OLLAMA_OPTIONS")["api_base"]) if kwargs.get("OLLAMA_OPTIONS")["api_base"] else None
    OpenAI = OpenAIClient(api_key=kwargs.get("OPENAI_OPTIONS")["api_key"]) if kwargs.get("OPENAI_OPTIONS")["api_key"] else None
    Groq = GroqClient(api_key=kwargs.get("GROQ_OPTIONS")["api_key"]) if kwargs.get("GROQ_OPTIONS")["api_key"] else None

    try:
        model = get_model_details(kwargs.get("CIVITAI_MODELS"), kwargs.get("CIVITAI_VERSIONS"), identifier)
        model_id = model.get("id", "")
        model_name = model.get("name", "")
        
        with console.status(f"[yellow]Asking {service} to explain model description", spinner="dots") as status:
            summary = summarize_model_description(
                model, model_id, service, 
                Ollama=Ollama, OpenAI=OpenAI, Groq=Groq,
                OLLAMA_OPTIONS=kwargs.get("OLLAMA_OPTIONS"),
                OPENAI_OPTIONS=kwargs.get("OPENAI_OPTIONS"),
                GROQ_OPTIONS=kwargs.get("GROQ_OPTIONS")
            )
            status.update(f"[green]Summary completed for {model_name}")

        summary_table = Table(title_justify="left")
        summary_table.add_column(f"Explanation of model {model_name} // {model_id} using {service}:", style="cyan")
        summary_table.add_row(summary or "No summary available.")

        console.print(summary_table)

    except ValueError:
        feedback_message("Invalid model ID. Please enter a valid number.", "error")
