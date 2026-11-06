import anthropic
from dotenv import load_dotenv
from search import search
import os
import pandas as pd
from question_llm import answer_question
import re

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ['CLAUDE_API_KEY'])

questions = []
df = pd.read_csv("pubmed_cleaned_articles.csv")
sample = df.sample(20, random_state=42)
for _, row in sample.iterrows():
    prompt = f"Write one question a researcher might ask that this abstract answers. Paraphrase; don't reuse its exact phrases.\n\nAbstract: {row['abstract']}"

    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    question = "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()

    questions.append(question)

sample['question'] = questions
TOP_K = 5
results = []

for _, row in sample.iterrows():
    target_pmid = str(row["pmid"])
    question = row["question"]

    # Did search find the source abstract?
    retrieved = search(question, top_k=TOP_K)
    was_retrieved = target_pmid in retrieved["pmid"].astype(str).values

    # Did Claude cite it?
    answer = answer_question(question, top_k=TOP_K)
    was_cited = re.search(rf"\b{target_pmid}\b", answer) is not None

    results.append({
        "pmid": target_pmid,
        "question": question,
        "answer": answer,
        "retrieved": was_retrieved,
        "cited": was_cited,
    })

results_df = pd.DataFrame(results)
results_df.to_csv("evaluation_results.csv", index=False)

print(f'Retrieval hit rate: {results_df["retrieved"].mean():.1%}')
print(f'Citation rate: {results_df["cited"].mean():.1%}')