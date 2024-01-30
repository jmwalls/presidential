"""CLI tools to scrape and process data."""
import json
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

import pandas as pd

import dataframes
import embeddings
import scrape


app = typer.Typer(help=__doc__)
console = Console()


@app.command()
def scrape_speeches(output_path: Path):
    """
    Scrape speeches and save to OUTPUT_PATH.
    """
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
    """
    Print speeches contained in DATA_PATH.
    """
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
def write_text_tables(input_path: Path, authors_path: Path, output_path: Path):
    """
    Create dataframe tables from speeches contained and INPUT_PATH and save to
    the OUTPUT_PATH dir.

    This function will create the OUTPUT_PATH dir if it does not already exist.
    """
    output_path.mkdir(exist_ok=True)

    console.print(f"building tables from {input_path}...")
    df_auth = dataframes.author(authors_path)
    df_text = dataframes.text(input_path, df_auth)
    df_para = dataframes.paragraph(df_text)

    console.print(f"saving tables to {output_path}...")
    df_auth.to_parquet(output_path / "author.parquet")
    df_text.to_parquet(output_path / "text.parquet")
    df_para.to_parquet(output_path / "paragraph.parquet")


@app.command()
def write_embeddings(
    input_path: Path, model: embeddings.EmbeddingType = typer.Option()
):
    """
    Create OpenAI embeddings from the dataframe tables contained in INPUT_PATH.
    Embedding tables are also written to this same dir.
    """
    assert (
        input_path / "paragraph.parquet"
    ).exists(), "Input paragraph dataframe does not exist!"

    console.print(f"building {model.value} embedding table from {input_path}...")
    df_para = pd.read_parquet(input_path / "paragraph.parquet")

    match model:
        case embeddings.EmbeddingType.TFIDF:
            df_para_emb, df_text_emb = embeddings.tfidf(df_para)
        case embeddings.EmbeddingType.OPENAI_ADA_002:
            df_para_emb, df_text_emb = embeddings.openai(df_para, model)
        case embeddings.EmbeddingType.OPENAI_3_SMALL:
            df_para_emb, df_text_emb = embeddings.openai(df_para, model)

    console.print(f"saving para/text tables to {input_path}")
    df_text_emb.to_parquet(input_path / f"{model.value}.text.parquet")
    df_para_emb.to_parquet(input_path / f"{model.value}.paragraph.parquet")


if __name__ == "__main__":
    app()
