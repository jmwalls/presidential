"""CLI tools to scrape and process data."""
import json
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_distances

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


@app.command()
def build_post_data(input_path: Path):
    """
    Write data artifacts that are used for the viz scripts.

    We're assuming here that input path includes all the embedding types
    (tf-idf, ada002, 3-small)... This function is a bit of a hodge podge...
    """
    dfs_emb = {
        "tfidf": pd.read_parquet(input_path / "tfidf.text.parquet"),
        "openai-ada-002": pd.read_parquet(input_path / "openai-ada-002.text.parquet"),
        "openai-3-small": pd.read_parquet(input_path / "openai-3-small.text.parquet"),
    }

    df_text = pd.read_parquet(input_path / "text.parquet")
    df_auth = pd.read_parquet(input_path / "author.parquet")

    df_text_auth = (
        df_text[["text_id"]]
        .merge(df_text[["text_id", "author_id", "year"]], how="inner", on="text_id")
        .merge(
            df_auth[["author_id", "author"]].drop_duplicates(keep="first"),
            how="inner",
            on="author_id",
        )
    )

    def _scale(X):
        x_ptp = X.ptp(axis=0)
        x_min = X.min(axis=0)
        return (1.0 / x_ptp.max()) * (X - x_min - 0.5 * x_ptp) + 0.5

    def _dim_reduction(df):
        X = np.vstack(df["embedding"].values)
        X_pca = _scale(PCA(n_components=2).fit_transform(X))
        X_tsne = _scale(TSNE(n_components=2).fit_transform(X))
        return pd.DataFrame(
            data={
                "text_id": df["text_id"],
                "x_pca": X_pca[:, 0],
                "y_pca": X_pca[:, 1],
                "x_tsne": X_tsne[:, 0],
                "y_tsne": X_tsne[:, 1],
            }
        )

    dfs_feat = {k: _dim_reduction(v) for k, v in dfs_emb.items()}
    (
        pd.concat(
            [
                v.set_index("text_id").add_suffix(f"_{k.replace('-', '_')}")
                for k, v in dfs_feat.items()
            ],
            axis=1,
        )
        .reset_index(drop=False)
        .merge(df_text_auth, how="inner", on="text_id")
    ).to_csv("presidential_1.csv", index=False)

    def _find_nearest(key, df):
        X = np.vstack(df["embedding"].values)
        dist = cosine_distances(X)
        return (
            pd.DataFrame(data=dist.tolist(), index=df["text_id"])
            .reset_index(drop=False)
            .melt(["text_id"], var_name=f"{key}_text_id", value_name=f"{key}_distance")
            .sort_values(by=f"{key}_distance")
            .groupby("text_id")
            .head(20)
            .reset_index(drop=True)
            .sort_values(by=["text_id", f"{key}_distance"])
            .merge(
                df_text_auth.add_prefix(f"{key}_"),
                on=f"{key}_text_id",
            )
            .drop(columns=[f"{key}_author_id", f"{key}_text_id"])
            .set_index("text_id")
        )

    (
        pd.concat(
            [_find_nearest(k, v) for k, v in dfs_emb.items()],
            axis=1,
            join="outer",
        )
        .reset_index(drop=False)
        .merge(
            df_text_auth,
            on="text_id",
        )
        .drop(columns="author_id")
        .groupby("text_id")
        .apply(lambda g: g.to_dict("records"), include_groups=False)
        .to_json("presidential_2.json", indent=2)
    )


if __name__ == "__main__":
    app()
