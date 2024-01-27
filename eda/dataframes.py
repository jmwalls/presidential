"""Build text and paragram tables from speeches."""
import json
from pathlib import Path

import pandas as pd


def text(path: Path) -> pd.DataFrame:
    """
    Build text table from directory of speeches.

    @param path: directory containing speech JSONs
    @returns text dataframe
    """

    def _load(p: Path) -> dict:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**data, **{"text_length": len(data["text"])}}

    # Note: replace below is to clean up documents with fixed line widths.
    return (
        pd.DataFrame.from_records([_load(p) for p in path.glob("*.json")])
        .sort_values(by="year")
        .reset_index(drop=True)
        .assign(
            text=lambda df: df.apply(lambda r: r["text"].replace(" \n", " "), axis=1)
        )
        .assign(text_id=lambda df: df.index)
    )


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
