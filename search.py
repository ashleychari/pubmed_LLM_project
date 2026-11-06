import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import sys

# Load your saved data
pubmed_df = pd.read_csv("pubmed_cleaned_articles.csv")
embeddings = np.load("abstract_embeddings.npy")
assert len(pubmed_df) == len(embeddings)

# Load the same model used to create the embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

def search(query, top_k=5):
    query_embedding = model.encode([query], normalize_embeddings=True)
    # Use consine similarity to determine which articles are most
    # similar to the search query
    scores = (embeddings @ query_embedding.T).squeeze(axis=1)
    top_indices = scores.argsort()[::-1][:top_k]

    # Take note of cosine similarity score
    results = pubmed_df.iloc[top_indices].copy()
    results["score"] = scores[top_indices]
    return results

if __name__ == "__main__":
    search(sys.argv[1], sys.argv[2])


    