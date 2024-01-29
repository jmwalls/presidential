## Presidential Similarity

Vector databases are all the rage these days--in particular to support retrieval
augmented generation (RAG) applications.

We'd like to look at vector similarity between presidential addresses
(state-of-the-unions, and inaugurals).

Project layout:

* [eda/]("eda/") includes Python code used to scrape the raw data, generate
  embeddings, and evaluate simularity.
* [visualization/]() contains front-end javascript to present the results.

### Vector embeddings

* tf-idf
* OpenAI adav2
* HuggingFace embeddings?
    * [Sentence-BERT](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
    * Max token size may be ~512...

### Data Exploration

We'll split each speech into it's constituent paragraphs, then form an embedding
per paragraph.

Interestingly enough, paragraph length is pretty neatly distributed. See [Log
normal paragraph
length](https://epjdatascience.springeropen.com/articles/10.1140/epjds14)...

At this point we can look at similarity of a particular paragraph from one
speech and the nearest paragraphs from other speeches... Since tf-idf doesn't
capture any semantics, it would be interesting to look at intro sentences, i.e.,
do learned embeddings capture salutations whereas tf-idf will only find similar
wordings?

(Would be interesting to see what words are in the tf-idf vocabulary...)

We can also aggregate the embeddings across paragraphs to determine a single
document embedding (try weighted average?). With a full-document embedding, we
can look for similarities and differences between elements of the corpus.


* Pairwise cosine similarity matrix
    * Sort temporally
    * Sort based on hierarchical clusters
* For a query speech, return
    * k-nearest
    * k-farthest

### Run this code...

The scraped "raw" addresses are stored [in this repo](data/raw/). They have been
scrubbed to some extent, e.g., removing `[Applause]` annotations. To scrape
addresses directly from wikisource run

```
$ python cli.py scrape-speeches /path/to/write/data
```

In order to process the addresses, we store both the full text and paragraphs as
a set of dataframes / tables. New tables are created for each different
embedding type. To generate processed data run

```
$ python cli.py write-text-tables /path/to/addresses /path/to/tables
$ python cli.py write-tfidf-embeddings /path/to/tables
```

Note that to create OpenAI embeddings, the `OPENAI_API_KEY` must be set as an
environment variable.
