# Part 3B research notes: when to use a small ML model instead of an LLM

Gathered 24 Oct 2026. A draft for you to rewrite in your own words; this isn't the final memo text.
Numbers marked "(ours)" come from your repo. Update them if v2 changes anything.

---

## 1. Draft view (about half a page)

> Use a small ML model when the task is a **fixed prediction on structured data or a narrow label set**, you have (or can collect) **labelled examples**, and you need it to be **cheap, fast, explainable and stable**. Use an LLM when the task needs **understanding open-ended language, reasoning against a rubric, or generating text**, when labelled data is scarce, or when the inputs vary too much for a small model to cover (for example, mixed languages). Often the best system uses both: a small model decides *who* needs attention, and an LLM decides *what to say* to them.
>
> The evidence supports this split. On tabular data, tree-based models such as XGBoost and random forests still beat deep learning on medium-sized datasets (Grinsztajn et al., 2022, 45 datasets). And even for text classification, fine-tuned small models (BERT-style) consistently beat zero-shot GPT-4 and Claude when enough labelled data exists (Bucher & Martini, 2024). So the LLM's advantage is not that it is "more accurate". It needs **almost no labelled data**, it **generalises to new wording and languages**, and it **writes the feedback**, which no classifier can do.

---

## 2. Comparison

| | Small ML model (e.g. logistic regression, TF-IDF + LR, gradient boosting) | LLM (e.g. Claude Haiku 5.5, Gemini Flash) |
|---|---|---|
| **Cost** | Practically free to run: TF-IDF + LR predicts 1,000 explanations in about 50 ms on one CPU core (ours) | Pay per token: about $0.25 per 1,000 calls with Haiku 5.5 (ours, 1,217 input + 260 output tokens), about $21/month at 85,000 calls. Bigger models cost 10–20× more. |
| **Speed** | Milliseconds, can run anywhere | Seconds per call (network + generation); rate limits apply. The free tier capped us at about 5 requests/min and 20/day. |
| **Accuracy** | Strong when there's enough labelled data that resembles production data; weak on new wording | Strong with no training data; can be tuned with prompt and rubric changes; can be wrong on borderline cases (all 12 v1 errors were understood → partial) |
| **Explainability** | High: coefficients, feature importance, exact rules | Medium: gives a stated reason per verdict, but the reason isn't guaranteed to match how it actually decided. Not fully deterministic (97.3% stable in our test). |
| **Data needed** | Hundreds to thousands of labelled examples for text; works well on structured data from the start | Zero to a few dozen labelled examples, enough to evaluate and tune the prompt |
| **Maintenance** | Retrain when the data changes; monitor for drift; low running complexity | Vendors update and retire models (Gemini 3.6 Flash is already marked deprecated, and prices change). Re-run the evaluation on every model change; prompts need versioning; injection attacks need defending (3 in our data). |

---

## 3. Real-world examples

**Example 1: Duolingo uses both, split the same way as this task.**
- **Small ML model for prediction:** "Birdbrain" predicts whether a learner will get a given exercise right and uses that to set the difficulty. By October 2020 it was personalising over 20% of lessons, and Duolingo reports that learners given Birdbrain-built lessons were more likely to keep learning. ([Duolingo blog, 2020](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain))
- **LLM for language feedback:** Duolingo Max (March 2023), built with early access to GPT-4, added "Explain My Answer", which gives AI-written, context-specific explanations of a learner's mistakes. ([Duolingo investor news release, 2023](https://investors.duolingo.com/news-releases/news-release-details/duolingo-max-shows-future-ai-education))
- **Why it fits:** prediction at scale uses a cheap model; free-text explanation uses an LLM. That's the same split as Part 1 and Part 2.

**Example 2: Georgia State University's early-warning system, a predictive model for student dropout.**
- GSU analysed 2.5 million grades from 10 years of records to build GPS, an early-warning system with more than 700 risk flags, updated daily. Alerts go to human advisers, which led to 51,000 adviser meetings in 12 months. Graduation rates rose 6 percentage points, and students graduated about half a semester sooner. ([NPR, 2016](https://www.npr.org/sections/ed/2016/10/30/499200614/how-one-university-used-big-data-to-boost-graduation-rates))
- **Why it fits:** a structured-data model flags who is at risk, and humans (in our case, LLM feedback) carry out the intervention. Note: the article doesn't say whether GPS is rule-based or statistical, and more than 90% of the project's cost was adviser staffing, not the model.

**Supporting research (optional, if space allows):**
- Grinsztajn, Oyallon & Varoquaux (2022): tree-based models beat deep learning on medium-sized tabular data across 45 datasets. ([arXiv 2207.08815](https://arxiv.org/abs/2207.08815v1))
- Bucher & Martini (2024): fine-tuned small BERT-style models significantly beat zero-shot GPT-4 and Claude Opus at text classification. ([arXiv 2406.08660](https://arxiv.org/abs/2406.08660v1))

---

## 4. Applied to this task

**Part 1 (predicting dropout): a small ML model, clearly.**
- Structured data (quiz scores, attempt counts, dates) for 500 students.
- Logistic regression reached AUC 0.77 and recall 0.80 at a chosen threshold (ours). Training and scoring take milliseconds.
- Coefficients and permutation importance show *why* a student is flagged ("reached 2+ lessons in 14 days without retrying"). An adviser can act on that, and you can audit it for fairness.
- An LLM would add cost and latency, and take away explainability, with nothing gained on tabular data.

**Part 2 (judging explanations): an LLM, for now.**
- Only 60 labelled rows (37 unique texts). TF-IDF + LR scored 73% on a random split but **19% when whole templates were held out** (a most-frequent-label baseline scores 12% on the same folds), so it was memorising templates rather than learning to grade (ours).
- The LLM reached 83.8% on unique texts with **no training data** (v1, ours), handled Hinglish, resisted all 3 injection attempts, and writes the feedback, which a classifier can't do at all.
- Cost is about $21/month at 50,000 students. Not a concern.

**Being honest about 60 rows:** 60 rows (37 unique, a few templates per lesson) is far too few to train or fairly judge a text classifier. The 73% vs 19% gap shows that. Neither model's accuracy here would hold for real, varied student writing.

**What would change the answer:**
- Once a few thousand LLM-graded explanations have been checked by teachers, a small fine-tuned classifier could do the **verdict** cheaply.
- The LLM would then only write the **feedback**, or handle the low-confidence cases. This follows Bucher & Martini's finding that fine-tuned small models win once enough labelled data exists.

---

## Sources

- [Learning how to help you learn: introducing Birdbrain, Duolingo blog (2020)](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain)
- ["Duolingo Max" shows the future of AI education, Duolingo investor relations (2023)](https://investors.duolingo.com/news-releases/news-release-details/duolingo-max-shows-future-ai-education)
- [How one university used big data to boost graduation rates, NPR (2016)](https://www.npr.org/sections/ed/2016/10/30/499200614/how-one-university-used-big-data-to-boost-graduation-rates)
- [Why do tree-based models still outperform deep learning on tabular data?, Grinsztajn et al. (2022)](https://arxiv.org/abs/2207.08815v1)
- [Fine-tuned "small" LLMs (still) significantly outperform zero-shot generative AI models in text classification, Bucher & Martini (2024)](https://arxiv.org/abs/2406.08660v1)
