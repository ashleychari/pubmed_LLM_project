import os
import re

import anthropic
import pandas as pd
from dotenv import load_dotenv

from question_llm import answer_question
from search import search

load_dotenv()

# connect to claude api
client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# Read in synthetic and my questions and set the top number of results returned to 5
TOP_K = 5
tests = pd.read_csv("results/generated_and_base_test_questions.csv", dtype=str, keep_default_na=False)

# Grades the responses to questions
def grade(question, expected, answer, question_type):
    if question_type == "unanswerable":
        labels = "DECLINED or ANSWERED"
        instructions = (
            "DECLINED means the answer says the abstracts don't answer the question. "
            "ANSWERED means it answers anyway."
        )
    else:
        labels = "CORRECT, PARTIAL, or INCORRECT"
        instructions = (
            "CORRECT means it matches the main points of the expected answer. "
            "PARTIAL means it misses important points. "
            "INCORRECT means it contradicts the expected answer or fails to answer. "
            "Extra accurate detail is fine."
        )

    # Build the message for the judge. The f-string fills in each {...}
    # with the value of that variable. These lines stay at the left edge
    # because any spaces inside the triple quotes become part of the prompt.
    prompt = f"""Grade this answer. {instructions}

    Question: {question}
    Expected answer: {expected}
    Answer to grade: {answer}

    On the first line, write only one label: {labels}.
    On the second line, give a one-sentence reason."""

    # Send the prompt to Claude in a new API call. This is separate from
    # the call that produced the answer, so Claude acts only as a judge.
    message = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
    
    # The reply comes back as a list of content blocks. Join the text
    # blocks into one string, then remove spaces from the start and end.
    text = "".join(
            block.text for block in message.content if block.type == "text"
    ).strip()

    # Split the reply into words so the label can be taken from the start.
    # Use the first word as the label:
    #   .strip("*.:") removes formatting, so "**CORRECT**" becomes "CORRECT"
    #   .upper() makes it capitals, so "Correct" becomes "CORRECT"
    verdict = text.split()[0].strip("*.:").upper()

    # Return the label for scoring, and the full reply so you can see
    # why the judge chose it. The full reply is saved as grader_notes.
    return verdict, text

# For each test question, the script checks whether search retrieved 
# the supporting abstracts, gets Claude’s answer, checks whether it
# cited them, and has Claude grade it against the expected answer.
# It saves one row per question, converts each grade to points, 
# averages the results by question type, and saves both 
# the per-question results and the summary to CSV files.
rows = []

for _, row in tests.iterrows():
    supporting = set(row["supporting_pmids"].split(";")) - {""}
    retrieved = set(search(row["question"], top_k=TOP_K)["pmid"].astype(str))

    answer = answer_question(row["question"], top_k=TOP_K)
    cited = set(re.findall(r"\b\d{7,8}\b", answer))
    verdict, grader_notes = grade(
        row["question"], row["expected_answer"], answer, row["type"]
    )

    rows.append({
        **row,
        "answer": answer,
        "n_supporting": len(supporting),
        "n_retrieved": len(supporting & retrieved),
        "any_retrieved": bool(supporting & retrieved),
        "any_cited": bool(supporting & cited),
        "verdict": verdict,
        "grader_notes": grader_notes,
    })

results = pd.DataFrame(rows)
# Flag answers that don't end like a finished sentence
results["truncated"] = ~results["answer"].str.strip().str[-1].isin([".", ")", "*", '"'])
results.to_csv("test_set_results.csv", index=False)

answerable = results[results["type"] != "unanswerable"]
print(answerable.groupby("type")[["any_retrieved", "any_cited"]].mean())
print(results.groupby(["type", "verdict"]).size())


points = {
    "CORRECT": 1,
    "PARTIAL": 0.5,
    "INCORRECT": 0,
    "DECLINED": 1,
    "ANSWERED": 0,
}

results["score"] = results["verdict"].map(points)

unexpected = results.loc[results["score"].isna(), "verdict"].unique()
if len(unexpected) > 0:
    print("Unexpected labels:", unexpected)

summary = results.groupby("type").agg(
       questions=("question", "count"),
       retrieval_rate=("any_retrieved", "mean"),
       citation_rate=("any_cited", "mean"),
       answer_score=("score", "mean"),
       truncated=("truncated", "sum"),
)

summary.to_csv("results/test_set_summary.csv")
results.to_csv("results/test_set_results.csv", index=False)  # resave with the score column
print(summary)