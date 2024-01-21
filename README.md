## Presidential Similarity

Vector databases are all the rage these days--in particular to support retrieval
augmented generation (RAG) applications.

We'd like to look at vector similarity between presidential addresses
(state-of-the-unions, and inaugurals).


(1) Build dataset: scrape addresses
(2) Compute embeddings for each address
(3) Visualization

### Vector embeddings

* TF-IdF
* OpenAI adav2

### Data Exploration

* Pairwise cosine similarity matrix
    * Sort temporally
    * Sort based on hierarchical clusters
* For a query speech, return
    * k-nearest
    * k-farthest
