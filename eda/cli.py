"""CLI tools to scrape data."""
import typer
from pathlib import Path

import scrape


app = typer.Typer()


@app.command()
def scrape_inaugural(output_path: Path):
    output_path.mkdir(exist_ok=False)
    scrape.inaugural(output_path)


@app.command()
def scrape_sotu(output_path: Path):
    output_path.mkdir(exist_ok=False)
    scrape.sotu(output_path)


if __name__ == "__main__":
    app()
