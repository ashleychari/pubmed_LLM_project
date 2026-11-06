import time
from Bio import Entrez, Medline
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()  # reads .env into environment variables

Entrez.email = os.environ["NCBI_EMAIL"] 

handle = Entrez.esearch(db="pubmed", term="Depression", usehistory="y")
results = Entrez.read(handle)
handle.close()

count = min(int(results["Count"]), 600)  # cap for this example
batch_size = 200
records = []

# Grab 600 articles with the depression keyword
for start in range(0, count, batch_size):
    handle = Entrez.efetch(
        db="pubmed",
        rettype="medline",
        retmode="text",
        retstart=start,
        retmax=batch_size,
        webenv=results["WebEnv"],
        query_key=results["QueryKey"],
    )
    records.extend(Medline.parse(handle))
    handle.close()
    time.sleep(0.5)  # optional extra pause between batches

print(f"Fetched {len(records)} records")


articles = []

# Extract information from records
for record in records:
    date = record.get("DP", "")
    articles.append({
        "pmid": record.get("PMID"),
        "title": record.get("TI"),
        "abstract": record.get("AB"),
        "year": date[:4] if date else None,
        "journal": record.get("JT"),
    })

# convert list of dictionaries into a table
pubs_df = pd.DataFrame(articles)

pubs_df.to_csv("pubmed_articles_info.csv", index=False)
