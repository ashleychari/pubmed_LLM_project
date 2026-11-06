import pandas as pd

# Read in data
pubmed_df = pd.read_csv("pubmed_articles_info.csv")

# Remove articles with empty abstracts
pubmed_df = pubmed_df[pubmed_df['abstract'] != '[]']
pubmed_df = pubmed_df.dropna(subset=["abstract"])

# Create a histogram of the length of the abstract to determine
# a cutoff for minimum word length
pubmed_df["n_words"] = pubmed_df["abstract"].fillna("").str.split().str.len()
print(pubmed_df["n_words"].describe())
pubmed_df["n_words"].hist(bins=50)

# Read the lowest top 20
for _, row in pubmed_df.sort_values("n_words").head(20).iterrows():
    print(row["n_words"], "|", row["title"], "|", row["abstract"][:200])

# Based on the histogram cutoff is abstracts less than 10 words
pubmed_df = pubmed_df[pubmed_df['n_words'] > 10]

pubmed_df.to_csv("pubmed_cleaned_articles.csv", index=False)
