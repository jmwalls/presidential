"""Wrap embedding methods."""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def _aggregate(df):
    """
    Aggregate paragraph embeddings within a single document as the unit norm
    vector of the weighted sum of the constituent paragraph embedding vectors.
    """
    weights = df["paragraph_length"].values / df["paragraph_length"].sum()
    emb = (weights.reshape(-1, 1) * np.vstack(df["embedding"].values)).sum(axis=0)
    return emb / np.linalg.norm(emb)


def tfidf(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build TF-IdF embeddings per text by paragraph aggregation.

    @param df: paragraph dataframe
    @returns tfidf embedding paragraph and text dataframes
    """
    vectorizer = TfidfVectorizer(
        max_features=1536,  # match OpenAI embedding dimension
    )
    X = vectorizer.fit_transform(df["paragraph_text"].values.tolist())

    df_para_emb = df[["text_id", "paragraph_id", "paragraph_length"]].assign(
        embedding=X.toarray().tolist()
    )

    df_text_emb = (
        df_para_emb.groupby("text_id")
        .apply(_aggregate, include_groups=False)
        .reset_index(drop=False)
        .rename(columns={0: "embedding"})
    )

    return df_para_emb, df_text_emb


def openai(df: pd.DataFrame) -> pd.DataFrame:
    """
    XXX

    We'll hit the OpenAI embeddings
    [endpoint](https://platform.openai.com/docs/api-reference/embeddings/create).
    A few notes on their use:

    * Accepts an input array of str or token documents.
    * Input array length must be less than 2048.
    * Each document must be less than 8192 tokens (I believe the document is
      automatically truncated otherwise).

    @param df: paragraph dataframe
    @returns OpenAI embedding paragraph and text dataframe
    """
    pass
