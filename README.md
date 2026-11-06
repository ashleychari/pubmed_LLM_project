# PubMed LLM Project

## Overview

This project answers questions about depression research using retrieval-augmented generation (RAG). It searches 581 PubMed abstracts with sentence embeddings, sends the top 5 matches to Claude (`claude-sonnet-5-5`), and asks it to answer only from those abstracts and cite PMIDs.

### Code setup
1. `grab_pubmed_docs.py`: Uses Biopython to fetch 600 PubMed articles for the query "Depression" and saves their PMID, title, abstract, year, and journal to a table.
2. `clean_abstracts.py`: Plots a histogram of abstract word counts to choose a cutoff, then removes articles with empty abstracts or abstracts of 10 or fewer words.
3. `create_embeddings.py`: Uses sentence-transformers (`all-MiniLM-L6-v2`) to create an embedding for each abstract.
4. `search.py`: Embeds the question and uses cosine similarity to find the top k most similar abstracts.
5. `question_llm.py`: Sends the top k abstracts (those with a similarity score of at least 0.3) to Claude, which answers the question using only those abstracts and cites their PMIDs.
6. `evaluate_llm.py`: An initial test that has Claude write one question for each of 20 sampled abstracts, then checks whether search retrieves the source abstract and whether Claude cites it.
7. `evaluate_test_set.py`: Runs the 35-question test set through the system, records each answer, checks retrieval and citations, and uses a separate Claude call to grade each answer against its expected answer.
8. `make_eval_table.py`: Builds the results table from the hand-scored `scoring_sheet.csv`.


## Method

Each test question is run through the full system, then scored automatically:

- **Hit rate at 5:** The share of answerable questions where at least one supporting abstract appeared in the top 5 search results.
- **Citation rate:** The share of answerable questions where Claude's answer cited at least one supporting PMID.
- **Answer score:** A separate Claude call grades each answer against its expected answer.
  - Answerable questions are graded CORRECT (1 point), PARTIAL (0.5), or INCORRECT (0).
  - Unanswerable questions are graded DECLINED (1) or ANSWERED (0).
- **Cut-off answers:** Answers that don't end with a finished sentence are flagged.

## Results

| Metric | Specific | Broad | Unanswerable | Overall |
|---|---|---|---|---|
| Questions | 10 | 15 | 10 | 35 |
| Hit rate at 5 | 10 of 10 | 14 of 15 | n/a | 24 of 25 |
| Citation rate | 10 of 10 | 14 of 15 | n/a | 24 of 25 |
| Grader labels | 10 correct | 4 correct, 10 partial, 1 incorrect | 10 declined | |
| Answer score | 1.00 | 0.60 | 1.00 | 0.83 |
| Cut-off answers | 0 | 5 | 0 | 5 |

**Key findings:**

- **Specific questions work well.** Search found and Claude cited the right abstract every time, and all 10 answers were graded correct.
- **The system declines when it should.** It declined all 10 unanswerable questions, including the trap questions.
- **Broad questions are the weak spot.** Most broad answers were graded partial, because search often found only some of the relevant abstracts and 5 answers were cut off.

## Failure cases

### 1. Retrieval missed the relevant abstracts (B7)

**Question:** "Do online or app-based mental health programs reduce depression?"

- **What happened:** Search retrieved none of the 6 supporting abstracts, so the answer was graded incorrect.
- **Why:** The question's wording ("online or app-based") didn't match the abstracts' terms, such as "digital health interventions" and "e-Health". Many similar digital-health abstracts also competed for only 5 spots.
- **Takeaway:** The answer stayed within the abstracts it received, so the failure was in retrieval, not generation.

### 2. Answers were cut off (B2, B3, B9, B10, and B14)

- **What happened:** 5 of the 15 broad answers ended mid-sentence.
- **Why:** The response limit (`max_tokens=1024` in `question_llm.py`) was too low for longer answers.
- **Takeaway:** The grader still marked some of these correct, so the cut-off check is needed alongside it.

## Limitations of the automated grader

- **It can be too strict.** It compares answers with expected answers that may not list every relevant abstract, so a complete answer can be marked partial.
- **It doesn't check faithfulness.** It doesn't confirm that every claim is supported by the cited abstracts.
- **It's an AI model judging another AI's answers**, so its labels are not verified by a person.