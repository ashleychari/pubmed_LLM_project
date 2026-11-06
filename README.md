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

## Environment setup
Required packages can be found in requirements.txt. User will also need access to Claude API and NCBI_EMAIL to get access to PubMed articles.

## Method

Each test question is run through the full system, then scored automatically:

- **Hit rate at 5:** The share of answerable questions where at least one supporting abstract appeared in the top 5 search results.
- **Citation rate:** The share of answerable questions where Claude's answer cited at least one supporting PMID.
- **Answer score:** A separate Claude call grades each answer against its expected answer.
  - Answerable questions are graded CORRECT (1 point), PARTIAL (0.5), or INCORRECT (0).
  - Unanswerable questions are graded DECLINED (1) or ANSWERED (0).
- **Cut-off answers:** Answers that don't end with a finished sentence are flagged.


## Test set

The test set (`results/generated_and_base_test_questions.csv`) has 35 questions in three types:

| Type | Count | What it tests |
|---|---|---|
| Specific | 10 | One abstract answers the question, which is reworded to avoid that abstract's exact terms |
| Broad | 15 | Several abstracts are relevant, and the answer needs to combine them |
| Unanswerable | 10 | The abstracts don't answer the question, so the system should decline |

The unanswerable questions include close but uncovered topics (such as zuranolone and yoga), off-topic questions (such as how butterflies fly), and traps that share words with a real abstract but ask something it doesn't study.

The specific and broad questions, and 5 of the unanswerable questions (U1 to U5), were AI-generated from the dataset, along with their expected answers and supporting PMIDs. I wrote the other 5 unanswerable questions (U6 to U10).

Each row includes the question, its type, an expected answer, and the PMIDs of the supporting abstracts. Unanswerable questions have no supporting PMIDs. Expected answers for broad questions may not list every relevant abstract in the dataset.

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

## Limitations of the test set

- **Small test set:** 35 questions show patterns, but not precise rates.
- **Mostly synthetic questions:** 30 of the 35 questions were AI-generated, so they may be easier or more uniform than real user questions.
- **Incomplete answer keys:** Broad questions may have relevant abstracts that aren't listed as supporting, which can lower both the hit rate and the answer score.
- **Lenient metric:** Hit rate at 5 counts one supporting abstract as a hit, even when a broad question needs several.

## Data

- **Source:** Article data was retrieved from PubMed, provided by the U.S. National Library of Medicine.
- **Search term:** The search term "Depression" also matches non-clinical uses of the word, such as inbreeding depression and respiratory depression. This is why the dataset includes some unrelated papers, such as a study of black soldier flies that search returned for "How do butterflies fly?"
- **Not included in the repo:** The abstract files aren't included, because publishers often hold the copyright to abstracts. Run `grab_pubmed_docs.py` and `clean_abstracts.py` to rebuild them. Results may differ slightly, since the search returns the most recent articles at the time it runs.
- **Per-question results:** These aren't included, because the answers quote the abstracts. Run `evaluate_test_set.py` to regenerate them. Answers can vary between runs.

## Next steps

1. Raise `max_tokens` in `question_llm.py`, and flag any answer that stops because it hit the limit.
2. Improve retrieval for broad questions, for example by raising `top_k`, rewriting queries before searching, or adding keyword search (hybrid search).
3. Measure recall for broad questions (the share of supporting abstracts retrieved), not just hit rate.
4. Narrow the PubMed search to clinical depression, for example with `"Depressive Disorder"[MeSH Terms]`.
5. Check faithfulness, for example by scoring a sample of answers against their cited abstracts.
6. Add real user questions to the test set.