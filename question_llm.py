import anthropic
from dotenv import load_dotenv
from search import search
import os
import sys

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ['CLAUDE_API_KEY'])

def answer_question(question, top_k=5):
    results = search(question, top_k=top_k)

    results = results[results["score"] >= 0.3]

    if results.empty:
        return "I couldn't find any relevant abstracts for that question."

    context = "\n\n".join(
        f'PMID: {row["pmid"]}\nTitle: {row["title"]}\nAbstract: {row["abstract"]}'
        for _, row in results.iterrows()
    )

    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        system=(
            "Answer using only the provided abstracts. Cite the PMID for each "
            "claim. If the abstracts don't answer the question, say so."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Abstracts:\n{context}\n\nQuestion: {question}",
            }
        ],
    )

    return "".join(block.text for block in message.content if block.type == "text")

if __name__ == "__main__":
    print(answer_question(sys.argv[1]))
