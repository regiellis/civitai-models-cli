from setuptools import setup, find_packages

setup(
    name='civitai_model_manager',
    python_requires='>=3.10',
    version='0.1',
    packages=find_packages(),
    py_modules=['civitai_model_manager'],
    install_requires=[
        "typer",
        "rich",
        "requests",
        "shellingham",
        "html2text",
        "tqdm",
        "civitai",
        "python-dotenv",
        "ollama",
        "openai"
    ],
    entry_points={
        'console_scripts': [
            'civitai_model_manager = civitai_model_manager:app'
        ]
    }
)
