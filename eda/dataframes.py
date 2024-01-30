"""Build text and paragram tables from speeches."""
import json
from pathlib import Path

import pandas as pd


def authors(path: Path) -> pd.DataFrame:
    """
    Build table mapping author name / author id to author aliases.

    @param path: path to author.json file
    @returns author dataframe
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return pd.DataFrame.from_records(
        [
            {
                "author_id": i,
                "author": list(d.keys())[0],
                "alias": alias,
            }
            for i, d in enumerate(data)
            for alias in list(d.values())[0]
        ]
    )


def text(data_path: Path, authors_map_path: Path) -> pd.DataFrame:
    """
    Build text table from directory of speeches.

    @param data_path: directory containing speech JSONs
    @returns text dataframe
    """
    df_authors = authors(authors_map_path)

    def _load(p: Path) -> dict:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**data, **{"text_length": len(data["text"])}}

    # Note: replace below is to clean up documents with fixed line widths.
    return (
        pd.DataFrame.from_records([_load(p) for p in data_path.glob("*.json")])
        .sort_values(by="year")
        .reset_index(drop=True)
        .assign(
            text=lambda df: df.apply(lambda r: r["text"].replace(" \n", " "), axis=1)
        )
        .assign(text_id=lambda df: df.index)
        .merge(df_authors, how="inner", left_on="author", right_on="alias")
        .drop(columns=["author_x", "alias"])
        .rename(columns={"author_y": "author"})
    )[["year", "author_id", "author", "title", "text_id", "text", "text_length"]]


def paragraph(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build paragraph table from text table.

    @param df: text dataframe
    @returns paragraph dataframe
    """
    return (
        df[["text_id", "text"]]
        .assign(
            paragraph_text=lambda df: df.apply(lambda r: r["text"].split("\n"), axis=1)
        )
        .drop(columns=["text"])
        .explode("paragraph_text")
        .assign(
            paragraph_text=lambda df: df.apply(
                lambda r: r["paragraph_text"].strip().replace("  ", " "), axis=1
            )
        )
        .assign(paragraph_length=lambda df: df["paragraph_text"].str.len())
        .loc[lambda df: df["paragraph_length"] > 0]
        .reset_index(drop=True)
        .assign(paragraph_id=lambda df: df.groupby("text_id").cumcount())
    )
