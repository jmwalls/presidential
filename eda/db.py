"""
Playing around with pgvector...

Note that we're modifying the schema from how data is represented in dataframes
to keep things simple.
"""
import typer
from pathlib import Path
from rich.console import Console

import pandas as pd
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, DDL, event, Float, ForeignKey, Integer, String
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


app = typer.Typer(help=__doc__)
console = Console()


class Base(DeclarativeBase):
    pass


class Paragraph(Base):
    """Paragraph table"""

    __tablename__ = "paragraph"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    text_id: Mapped[int] = mapped_column(Integer)
    paragraph_index: Mapped[int] = mapped_column(Integer)

    paragraph_text: Mapped[str] = mapped_column(String, nullable=True)
    paragraph_length: Mapped[int] = mapped_column(Integer, nullable=True)


class ParagraphEmbedding(Base):
    """Embedding table"""

    __tablename__ = "paragraph_embedding"
    paragraph_id: Mapped[int] = mapped_column(
        ForeignKey("paragraph.id"), primary_key=True
    )
    embedding_type: Mapped[str] = mapped_column(String, primary_key=True)

    embedding: Mapped[list[float]] = mapped_column(Vector(1536))


@event.listens_for(ParagraphEmbedding.__table__, "before_create")
def _add_vector_extension(target, connection, **kw):
    connection.execute(DDL("CREATE EXTENSION IF NOT EXISTS vector"))


def _get_engine():
    url = URL.create(
        drivername="postgresql",
        username="postgres",
        password="postgres",
        host="localhost",
        port="5432",
    )

    return create_engine(url)


@app.command()
def startup():
    """Create database tables."""
    engine = _get_engine()

    console.print("creating tables...")
    Base.metadata.create_all(engine)


@app.command()
def shutdown():
    """Create database tables."""
    engine = _get_engine()

    console.print("dropping tables...")
    Base.metadata.drop_all(engine)


@app.command()
def push(path: Path):
    """Push data to tables."""
    engine = _get_engine()

    console.print("pushing paragraph data...")
    df_paragraph = pd.read_parquet(path / "paragraph.parquet")
    with engine.begin() as connection:
        (
            df_paragraph.reset_index(drop=False, names="id")
            .rename(columns={"paragraph_id": "paragraph_index"})
            .to_sql("paragraph", con=connection, index=False, if_exists="append")
        )

    def _push_embeddings(key):
        console.print(f"pushing {key} embedding data...")
        df = pd.read_parquet(path / f"{key}.paragraph.parquet")
        with engine.begin() as connection:
            (
                df[["embedding"]]
                .reset_index(drop=False, names="paragraph_id")
                .assign(
                    embedding=lambda df: df.apply(
                        lambda r: r["embedding"].tolist(), axis=1
                    )
                )
                .assign(embedding_type=key)
                .to_sql(
                    "paragraph_embedding",
                    con=connection,
                    index=False,
                    if_exists="append",
                )
            )

    _push_embeddings("tfidf")
    _push_embeddings("openai-ada-002")
    _push_embeddings("openai-3-small")


if __name__ == "__main__":
    app()
