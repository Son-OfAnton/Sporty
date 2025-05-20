#!/usr/bin/env python3
"""
Sporty CLI - Main entry point for the Sporty command-line interface.
"""

import click
import logging
import sys
import os

from app.utils.config import get_api_key, set_api_key, load_config, save_config
from app.utils.error_handlers import setup_error_handling

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@click.group()
@click.option(
    "--debug/--no-debug", 
    default=False, 
    help="Enable debug logging."
)
def cli(debug):
    """Sporty CLI - Your sports companion app."""
    # Set up logging based on debug flag
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Set up error handling
    setup_error_handling()

@cli.command()
def hello():
    """Say hello to the user."""
    click.echo("Hello, Sporty user!")

@cli.group()
def config():
    """Manage Sporty configuration."""
    pass

@config.command(name="set-api-key")
@click.argument("api_key", required=True)
def set_api_key_command(api_key):
    """Set the API-Football API key."""
    set_api_key(api_key)
    click.echo(f"API key has been set successfully.")

@config.command(name="get-api-key")
def get_api_key_command():
    """Get the currently configured API key."""
    api_key = get_api_key()
    if api_key:
        masked_key = f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}" if len(api_key) > 8 else "****"
        click.echo(f"Current API key: {masked_key}")
    else:
        click.echo("No API key configured. Use 'sporty config set-api-key API_KEY' to set one.")

@config.command(name="show")
def show_config():
    """Show the current configuration."""
    config = load_config()
    
    # Mask sensitive information
    if "api_key" in config:
        api_key = config["api_key"]
        config["api_key"] = f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}" if len(api_key) > 8 else "****"
        
    for key, value in config.items():
        click.echo(f"{key}: {value}")

if __name__ == '__main__':
    cli()