import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# load in cleaned dataset
pubmed_df = pd.read_csv("pubmed_cleaned_articles.csv")
pubmed_df = pubmed_df.dropna(subset=["abstract"]).reset_index(drop=True)

# Load in model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create embeddings for abstracts
embeddings = model.encode(
    pubmed_df["abstract"].tolist(),
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True,
)

print(embeddings.shape)  # (number of abstracts, 384)
np.save("abstract_embeddings.npy", embeddings)

assert len(pubmed_df) == len(embeddings)