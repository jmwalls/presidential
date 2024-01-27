"""CLI tools to scrape data."""
import json
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

import pandas as pd

import dataframes
import embeddings
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


@app.command()
def write_text_tables(input_path: Path, output_path: Path):
    output_path.mkdir(exist_ok=True)

    console.print(f"building tables from {input_path}...")
    df_text = dataframes.text(input_path)
    df_para = dataframes.paragraph(df_text)

    console.print(f"saving tables to {output_path}...")
    df_text.to_parquet(output_path / "text.parquet")
    df_para.to_parquet(output_path / "paragraph.parquet")


@app.command()
def write_tfidf_embeddings(input_path: Path):
    assert (
        input_path / "paragraph.parquet"
    ).exists(), "Input paragraph dataframe does not exist!"

    console.print(f"building TF-IdF embedding table from {input_path}...")
    df_para = pd.read_parquet(input_path / "paragraph.parquet")
    df_para_emb, df_text_emb = embeddings.tfidf(df_para)

    console.print(f"saving para/text tables to {input_path}")
    df_text_emb.to_parquet(input_path / "tfidf.text.parquet")
    df_para_emb.to_parquet(input_path / "tfidf.paragraph.parquet")


if __name__ == "__main__":
    app()
