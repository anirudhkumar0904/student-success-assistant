# Research memo

Prices were checked on 24 October 2026. Where I say "in my runs", the number comes from this repo.

## A. Which LLM should we use for 50,000 students a month?

### How I worked out the cost

In our data, 426 students wrote 724 explanations, so about 1.7 each. For 50,000 students that is 85,000 LLM calls a month. If every student explained all 3 lessons it would be 150,000 calls, so the real cost could be up to 1.76 times what I show below.

For tokens, I used what I measured with my final prompt on Claude Haiku 5.5: on average 1,884 input and 448 output tokens per call, thinking included. So:

monthly cost = 85,000 × (1,884 × input price + 448 × output price) / 1,000,000

I only have token counts for Haiku, so the other rows reuse them and are estimates. On my first prompt, Gemini used fewer input tokens and more output tokens than Haiku, so I would treat the Gemini rows as roughly ±30%. For Sarvam I converted rupees at ₹95.5 per dollar [10].

| Model | Price per 1M tokens (in / out) | Per month | With batch (half price) |
|---|---|---|---|
| Claude Haiku 5.5 [1] | $0.10 / $0.50 | $35 | $18 |
| Gemini 3.8 Flash [2] | $0.75 / $3.75, doubling on 1 Jan 2027 | $263, then $526 | $131, then $263 |
| Gemini 3.5 Flash-Lite [2] | $0.30 / $2.50 | $143 | $72 |
| Sarvam 105B [3] | ₹15 / ₹60 | ₹4,687 (about $49) | no batch price listed |

Even the most expensive option is about a cent per student per month, so I don't think price should decide this. I also cached repeated answers. In our data that cut 724 explanations down to 48 unique texts, but that is because the dataset is built from templates. Real students won't repeat each other this much, so I wouldn't count on that saving.

### Comparing the options

| | Claude Haiku 5.5 | Gemini 3.8 Flash | Sarvam 105B |
|---|---|---|---|
| Quality on our task | 81–87% agreement with the human labels on the 37 unique texts (two runs). Ignored all 3 prompt-injection attempts. 95–97% of verdicts the same when re-run. | I couldn't measure it. On the free tier 3.8 Flash timed out, and 3.6 Flash stopped me after 20 requests a day. | Not tested |
| General benchmark | Artificial Analysis index 43 [4] | 41 [5] | Behind similarly priced models on text reasoning [6] |
| Speed | 235 output tokens/s [4]. My full cold run of 161 calls took 10.4 minutes. | About 582 output tokens/s, 4.1 s to the first token (3.6 Flash) [5] | No numbers found |
| Student data | Not used for training; deleted within 30 days; zero retention possible by agreement [7]. Runs mainly in the US. AWS has an India-only option, but it lists Haiku 4.5, not 5.5 [8]. | On the free tier Google can use the data to improve its products; on the paid tier it can't [2]. I couldn't confirm India-only processing. | Hosted in India (Azure Central India), retention can be configured, ISO 27001 and SOC 2. DPDP compliance is "in progress" [9]. |
| Hindi, Tamil, Kannada | Hindi scores 92% of English (Haiku 4.5) [11]. Nothing published for Tamil or Kannada. 90% in an independent India test [6]. | Best in that test: 99% on text tasks, and best on Hinglish and on translating into Kannada [6] | Made for Indian languages. Best at translating into them (8 of 10 languages), 80% on text tasks [6] |

The independent India test [6] was the only comparison of all three I could find, and I don't fully trust it. Native speakers didn't check it, and Claude both wrote the tests and took part in them.

### My recommendation

I would go with Claude Haiku 5.5, sent through the Batch API once a night, for about $18–35 a month. It is the only model I could actually test on our data: it agreed with the human labels 81–87% of the time and wasn't fooled by any of the injection attempts. It is also the cheapest. Students don't need their feedback instantly, so overnight batches are fine and halve the cost. If the company decides student data has to stay in India, I would run Sarvam on the same 60 labelled rows before switching to it.

### Two risks

1. **Where the data goes.** Haiku 5.5 runs mostly in the US, and I couldn't confirm an India-only option for this version. Someone should check this against the DPDP Act before launch. Sarvam is the backup if the data must stay in India.
2. **Indian languages are untested.** My labelled data is only English and Hinglish, and no provider publishes Tamil or Kannada results. A wrong "wrong" verdict hurts most, because it discourages a student who is already struggling. Before launch I would get native speakers to label a small test set per language, and have teachers check a sample of "wrong" verdicts.

### What I couldn't confirm

How well Gemini does on our task, because of the free-tier limits. Whether Gemini Flash can run inside India on Vertex AI, or Haiku 5.5 on AWS in India. How long Google keeps paid-tier logs. Whether Sarvam uses customer data to improve its own models, and how fast it is. I also couldn't find any published Tamil or Kannada results. The speed numbers come from different sources and setups, so they are only rough comparisons.

## B. When should a company use a small ML model instead of an LLM?

### My view

I would use a small ML model when the job is a fixed prediction from structured data or a short list of labels, there are enough labelled examples, and it needs to be cheap, fast and easy to explain. I would use an LLM when it has to understand free text, judge it against a rubric or write something back, especially when there are only a few labels or the inputs vary a lot, like mixed languages.

I don't think LLMs win on raw accuracy. Tree-based models still beat deep learning on medium-sized tables of data [12], and small language models fine-tuned on enough labels beat GPT-4 and Claude at text classification [13]. Where the LLM helps is that it works with very few labels and can write the feedback itself.

### Two real examples

- **Duolingo uses both, split the way this task is.** A model called Birdbrain predicts whether a learner will get an exercise right and sets the difficulty [14]. GPT-4 powers "Explain My Answer", which tells learners why their answer was wrong [15].
- **Georgia State University** built an early-warning system with 700+ risk flags from ten years of grades. The alerts led to 51,000 adviser meetings in a year, and graduation rates went up 6 points. Most of the money went on advisers, not on the model [16].

| | Small ML model | LLM |
|---|---|---|
| Cost | Almost nothing: 1,000 predictions in about 50 ms on one CPU (my TF-IDF model) | About $0.41 per 1,000 calls with Haiku 5.5 (my runs) |
| Speed | Milliseconds | Seconds per call, with rate limits |
| Accuracy | Good with enough similar labelled data, bad on new wording | Good with no training, less sure on borderline answers |
| Explainability | Coefficients and feature importance | Gives a reason, but that may not be how it really decided |
| Data needed | Hundreds to thousands of labelled examples | A few dozen, mainly to test it |
| Maintenance | Retrain when the data changes | Models and prices change under you; prompts need versions; it needs defending against injection |

### For this task

**Part 1, predicting dropout: a small model.** The data is a table of scores and dates. My logistic regression reached AUC 0.77 ± 0.04 and caught 80% of dropouts at the threshold I chose, against F1 0.46 for a one-rule baseline. It runs in milliseconds, and its coefficients tell an adviser why a student was flagged, for example "reached 2+ lessons in 14 days without retrying".

**Part 2, judging explanations: an LLM, for now.** I tried TF-IDF with logistic regression on the 60 labelled rows. It scored 73% with a random split, but only 19% when I held out whole answer templates, against 12% for always guessing the most common label. So it was memorising templates rather than learning to grade. Haiku reached 81–87% with no training, handled Hinglish, and also writes the feedback, which a classifier can't do. Sixty rows (37 unique) is too few to judge either approach properly. Once teachers have checked a few thousand LLM-graded answers, I would train a small classifier for the verdict and keep the LLM only for writing the feedback.

## Sources

1. [Anthropic: API pricing](https://platform.claude.com/docs/en/about-claude/pricing?hsLang=en)
2. [Google: Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
3. [Sarvam: API pricing](https://www.sarvam.ai/api-pricing)
4. [Artificial Analysis: Claude Haiku 5.5](https://artificialanalysis.ai/models/claude-haiku-5-5)
5. [OrcaRouter: Haiku 5.5 vs Gemini 3.6 Flash](https://www.orcarouter.ai/blog/claude-haiku-5-5-vs-gemini-3-6-flash)
6. [sarvam-field-test on GitHub (11 Oct 2026)](https://github.com/shivanathd/sarvam-field-test)
7. [Anthropic: data retention](https://privacy.claude.com/en/articles/7996866-is-my-data-used-for-model-training) and [summary of Anthropic's commercial terms](https://meetily.ai/llm-privacy/anthropic)
8. [AWS: Claude models in India on Bedrock](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-expands-claude-model-availability-to-india-cross-region-inference/)
9. [Sarvam: Trust Center](https://www.sarvam.ai/trust-center)
10. [HDFC Sky: rupee at 95.46 per dollar](https://hdfcsky.com/news/rupee-rises-24-paise-to-close-at-95-46-against-us-dollar)
11. [Anthropic: multilingual support](https://platform.claude.com/docs/en/build-with-claude/multilingual-support)
12. [Grinsztajn et al. (2022), tree models vs deep learning on tabular data](https://arxiv.org/abs/2207.08815v1)
13. [Bucher and Martini (2024), fine-tuned small models vs zero-shot LLMs](https://arxiv.org/abs/2406.08660v1)
14. [Duolingo: introducing Birdbrain](https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain)
15. [Duolingo: Duolingo Max](https://investors.duolingo.com/news-releases/news-release-details/duolingo-max-shows-future-ai-education)
16. [NPR: how Georgia State used data to raise graduation rates](https://www.npr.org/sections/ed/2016/10/30/499200614/how-one-university-used-big-data-to-boost-graduation-rates)
