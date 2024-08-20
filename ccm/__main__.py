import sys
from . import cli

def main():
    if len(sys.argv) == 1: sys.argv.append("--help")
    cli.civitai_cli()

if __name__ == "__main__":
    cli.civitai_cli.main()