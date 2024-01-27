"""CLI tools to scrape data."""
import json
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

import scrape


app = typer.Typer()
console = Console()


@app.command()
def scrape_speeches(output_path: Path):
    console.print("scraping inaugural addresses...")
    out = output_path / "inaugural"
    out.mkdir(exist_ok=False, parents=True)
    scrape.inaugural(out)

    console.print("scraping sotu addresses...")
    out = output_path / "sotu"
    out.mkdir(exist_ok=False, parents=True)
    scrape.sotu(out)


@app.command()
def view_text(data_path: Path):
    speech_paths = sorted([p for p in data_path.glob("*.json")])
    for s in speech_paths:
        with open(s, "r", encoding="utf-8") as f:
            data = json.load(f)

        t = Table()
        t.add_column(f"{data['year']} -- {data['author']}")
        t.add_row(data["text"])

        console.print(t)
        key = console.input("enter cmd:")
        console.print(f"you entered {key}")
        if key == "q":
            break


if __name__ == "__main__":
    app()
