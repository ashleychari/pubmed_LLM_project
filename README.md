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


The evaluation checks three things:

1. **Retrieval:** Does search find the right abstracts?
2. **Answers:** Are the answers faithful to the abstracts, and do they answer the question?
3. **Failures:** Where and why does the system go wrong?

## Test set

The test set has 35 questions in three types:

| Type | Count | What it tests |
|---|---|---|
| Specific | 10 | One abstract answers the question, which is reworded to avoid that abstract's exact terms |
| Broad | 15 | Several abstracts are relevant, and the answer needs to combine them |
| Unanswerable | 10 | The abstracts don't answer the question, so the system should decline |

The unanswerable questions include close but uncovered topics (such as zuranolone and yoga), off-topic questions (such as how butterflies fly), and traps that share words with a real abstract but ask something it doesn't study.

The specific and broad questions, expected answers, and supporting PMIDs were AI-generated from the dataset and reviewed by hand. None of their supporting abstracts appear in an earlier 20-question test, on which retrieval and citation were both 100%.

## Method

- **Hit rate at 5:** The share of answerable questions where at least one supporting abstract appeared in the top 5 search results.
- **Faithful (1 to 3):** Does the answer say only what the cited abstracts support?
  - 3: Every claim is supported.
  - 2: Mostly supported, with a minor error or overstatement.
  - 1: Includes an unsupported or contradicted claim.
- **Helpful (1 to 3):** Does the answer actually answer the question?
  - 3: Answers directly with the key points.
  - 2: Partly answers, or misses important points.
  - 1: Doesn't answer.
  - For unanswerable questions, 3 means it clearly declined and 1 means it answered anyway.

Faithfulness and helpfulness were scored by hand against the cited abstracts, starting from AI-drafted scores that were reviewed and corrected. A separate Claude grader comparing each answer with the expected answer was used as a secondary check.

## Results

| Metric | Specific | Broad | Unanswerable | Overall |
|---|---|---|---|---|
| Questions | 10 | 15 | 10 | 35 |
| Hit rate at 5 | 10 of 10 | 14 of 15 | n/a | 24 of 25 |
| Faithful (1 to 3) | 3.00 | 2.93 | 3.00 | 2.97 |
| Helpful (1 to 3) | 3.00 | 2.53 | 3.00 | 2.80 |

**Key findings:**

- **Answers are highly faithful.** In 34 of 35 answers, every checked claim was supported by the cited abstracts. Answers also regularly pointed out study limitations, such as observational designs and small samples.
- **The system declines when it should.** It declined all 10 unanswerable questions, including the traps, and didn't fill gaps from general knowledge.
- **Broad questions are the weak spot.** Hit rate at 5 only checks for at least one supporting abstract. Many broad questions retrieved only some of theirs, so answers were accurate but incomplete.

## Failure cases

### 1. Retrieval missed the relevant abstracts (B7)

**Question:** "Do online or app-based mental health programs reduce depression?"

- **What happened:** Search retrieved none of the 6 supporting abstracts. The answer relied on internet-based exercise and feasibility studies, then concluded the evidence on other online programs was limited.
- **Why:** The question's wording ("online or app-based") didn't match the abstracts' terms, such as "digital health interventions" and "e-Health". Many similar digital-health abstracts also competed for only 5 spots.
- **Takeaway:** The answer stayed faithful to what it received, so the failure was in retrieval, not generation. Similar but smaller gaps appeared in B5, B8, and B14.

### 2. Answers were cut off (B2, B3, B9, B10, and B14)

- **What happened:** 5 of 35 answers ended mid-sentence. In B14, most of the treatment discussion was lost.
- **Why:** The response length limit (`max_tokens`) was too low for longer broad answers.
- **Takeaway:** The Claude grader didn't flag these, which shows why reading answers by hand matters.

### 3. Small factual slip (B12)

- **What happened:** The answer said "the other nine dietary exposures" showed no link to depression, but the study lists 11, so it should have said ten.
- **Takeaway:** This was the only answer that misstated its source. Small counting errors can slip past citation checks.

## Automated grader compared with hand scores

The Claude grader often marked broad answers `PARTIAL` because they missed points from the expected answer, even when they fully answered the question. Expected answers for broad questions are not exhaustive, so the grader can be too strict. It also missed the cut-off answers. My manual review caught both problems.

## Limitations

- **Small test set:** 35 questions show patterns, but not precise rates.
- **Some synthetic questions:** The some of the questions were AI-generated, so they may be easier or more uniform than real user questions. The human made questions were primarily in the unanswerable section.
- **Incomplete answer keys:** Broad questions may have relevant abstracts that aren't listed as supporting.
- **Lenient metric:** Hit rate at 5 counts one supporting abstract as a hit, even when a broad question needs several.
- **One reviewer:** Scores were reviewed by one person, with no second rater to check agreement.

## Next steps

1. Raise `max_tokens` and flag any answer that stops because it hit the limit.
2. Improve retrieval for broad questions, for example by raising `top_k`, rewriting queries before searching, or adding keyword search (hybrid search).
3. Measure recall for broad questions (the share of supporting abstracts retrieved), not just hit rate.
4. Add more real user questions to the test set.