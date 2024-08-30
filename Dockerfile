FROM debian:bullseye-slim

RUN apt update && apt autoremove -y \
    libncurses5-dev \
    libzstd-dev \
    zlib1g-dev 

# Install Python 3 and pip
RUN apt install -y --no-install-recommends python3-pip python3-setuptools

# Set default shell to bash for pip commands
ENV LC_ALL=C.UTF-8
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH


# Install required packages with pip
RUN pip install --upgrade pip setuptools wheel typer \
    rich httpx shellingham html2text \
    python-dotenv questionary ollama openai \
    groq asyncio tenacity

WORKDIR /home/civitaiuser
COPY ./.env /home/.config/civitai-model-manager/
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -ms /bin/bash civitaiuser
USER civitaiuser

ENV PATH=$PATH:/home/civitaiuser/.local/bin

CMD ["bash"]