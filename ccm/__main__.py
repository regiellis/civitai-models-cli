import sys
from ccm import cli

def main():
    if len(sys.argv) == 1: sys.argv.append("--help")
    cli.civitai_cli()