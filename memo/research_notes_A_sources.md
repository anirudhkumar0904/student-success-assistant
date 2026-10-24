# Part 3A research notes: which LLM for 50,000 students a month?

Gathered 24 Oct 2026. Research notes to write the memo from; this is not the memo.
Prices and policies change often, so re-check the official pages before submitting.

---

## 1. Cost calculation

### Assumptions (state these in the memo)

| Assumption | Value | Where it comes from |
|---|---|---|
| Students per month | 50,000 | Brief |
| Explanations per student | 1.7 | Our data: 724 explanations from 426 students |
| LLM calls per month | **85,000** | 50,000 × 1.7, one call per explanation, no cache |
| Input tokens per call | **1,884** | **Measured:** final prompt v2 on Claude Haiku 5.5, average of 76 evaluation calls (system prompt + rubric + key points + student text + output schema) |
| Output tokens per call | **448** | **Measured:** same runs; includes Haiku's thinking (on by default) + reasoning, key point checks, verdict and 3 feedback fields |
| Monthly tokens | 160.1M input, 38.1M output | 85,000 × the two figures above |
| Exchange rate | ₹95.5 per US$ | Rupee closed at 95.46 on 25 Aug 2026 (HDFC Sky) |

**Only Haiku's token counts are measured on the final prompt.** Every other row below reuses them, so those
rows are **estimates**: tokenizers differ, and each model thinks for a different length (see the Gemini
check under the table).

**Caching:** our synthetic data shrinks to 48 unique texts once filler is stripped (a 93% cut), but real students won't copy templates like this. Show the cache saving as an upper bound, not as the base case.

### Monthly cost (per 1M tokens: input price × 160.1 + output price × 38.1)

| Option | Price per 1M (input / output) | Per 1,000 explanations | Standard API / month | Batch API / month (−50%) |
|---|---|---|---|---|
| **Claude Haiku 5.5** (measured tokens; prompts under 100K tokens) | $0.10 / $0.50 | $0.41 | **$35** | $18 |
| Gemini 3.8 / 3.6 Flash, until 31 Dec 2026 *(estimate)* | $0.75 / $3.75 | $3.09 | **$263** | $131 |
| Gemini 3.8 / 3.6 Flash, from 1 Jan 2027 (price doubles) *(estimate)* | $1.50 / $7.50 | $6.19 | **$526** | $263 |
| Gemini 3.5 Flash-Lite *(estimate)* | $0.30 / $2.50 | $1.69 | **$143** | $72 |
| Claude Sonnet 5.5, premium reference *(estimate)* | $2.00 / $10.00 | $8.25 | **$701** | $351 |
| Sarvam 105B *(estimate)* | ₹15 / ₹60 | ₹55 | **₹4,687 ≈ $49** | No batch price listed |

Gemini prices are Google's official list prices, valid until 31 Dec 2026; Flash doubles from 1 Jan 2027.

**Thinking tokens (measured):** Haiku 5.5 thinks by default, and its 448 output tokens already include
that. Gemini bills thinking as output too. As a check, on the **v1** prompt `gemini-3.6-flash` averaged
**512 input + 115 output + 429 thinking** tokens over 17 calls, against Haiku's 1,217 + 260. Gemini's
own counts give less input and more output: Gemini Flash on v1 costs **$206/month** with its own counts,
against $160 with Haiku's v1 counts. So the Gemini rows above are rough, likely within about ±30%.
Lowering the thinking effort is a cost lever for both.

**Prompt v1 vs v2 cost:** the final v2 prompt costs about 58% more tokens per call than v1
(1,477 → 2,332), because of the longer rubric and the per-key-point checks. Haiku on v1 would be
$21/month.

**Key point for the memo:** every option costs between about $18 (Haiku, batch) and $700 (Sonnet)
a month. At 50,000 students that's under $0.02 per student, so **cost doesn't decide this. Quality on our
own evaluation, data privacy and Indian-language support do.**

---

## 2. Comparison of the three main options

| | Gemini 3.8 Flash (Google) | Claude Haiku 5.5 (Anthropic) | Sarvam 105B (Sarvam AI, India) |
|---|---|---|---|
| **Monthly cost** (85,000 calls, final v2 tokens) | ≈ $263 now, ≈ $526 from Jan 2027 (batch: half); estimates | **$35** (batch $18); measured tokens | ≈ $49; estimate |
| **Speed** | About 582 output tokens/s, 4.1 s median time to first token (OrcaRouter's own measurement, for 3.6 Flash). Free tier: we hit about 5 requests/min and saw 504 timeouts on 3.8 Flash. | 235 output tokens/s on Anthropic's API (Artificial Analysis, "Max" setting). AA's time-to-first-token figure (320 s) looks wrong; ignore it. | No published speed figures found |
| **Quality (general)** | Artificial Analysis Intelligence Index: 40.9 (3.8 Flash), 34.0 (3.6 Flash) | AA Intelligence Index: 43.4 | Not on the AA index; behind price-matched models on text reasoning in an independent India test (see below) |
| **Quality (our task)** | **Not evaluated.** Free-tier limits blocked it: 3.8 Flash mostly returned 504 timeouts, and 3.6 Flash is capped at 20 requests/day per model (one evaluation needs 76). 17 texts were graded before the cap and discarded. | **Evaluated (all Part 2 results):** v1 80.0% / final v2 81.7% on the 60 labelled rows (83.8% / 86.5% on 37 unique texts); 3/3 injection attempts resisted; 94.6–97.3% of verdicts identical on a re-run. | Not tested |
| **Training on data** | Free tier: **yes**, used to improve Google's products. Paid tier: no. | API: not used for training by default (Commercial Terms) | Not used to train models for *other* customers; unclear whether it improves Sarvam's own general models |
| **Retention** | Paid tier: logged "for a limited period" for abuse detection (no number of days given). Zero data retention needs Vertex AI. | Deleted within 30 days by default; up to 2 years if flagged by safety systems. Zero data retention by agreement with sales. | Configurable per customer, including an "ephemeral" mode that deletes data right after processing |
| **India data residency** | Gemini Developer API: no region controls. Vertex AI lists a Mumbai (asia-south1) column, but **we couldn't confirm** in-India processing for Flash 3.x. | Anthropic API: mainly US infrastructure. AWS Bedrock has an India-only profile (Mumbai + Hyderabad), but the 29 Sep 2026 announcement lists **Haiku 4.5, not 5.5**. | **Yes:** Azure Central India + Indian GPU providers; data doesn't leave India unless you ask. ISO 27001, SOC 2 Type II; DPDP compliance "in progress". |
| **Hindi / Tamil / Kannada** | Independent India test: best average text accuracy (99%), best Hinglish number capture (94%), best at translating into Kannada | Anthropic docs: Hindi at 92.4% of English (Haiku 4.5; Haiku 5.5 not listed). **No Tamil or Kannada figures.** Independent test: 90% average text accuracy. | Built for Indian languages. Independent test: 80% average text accuracy; Sarvam-Translate best for translating into Indian languages (8 of 10 languages); Kannada crop-advice task 92%. |

**About the "independent India test"** (sarvam-field-test on GitHub, 11 Oct 2026): it's the only head-to-head of all three on Indian-language tasks that I found, and it has real weaknesses. The test data wasn't reviewed by native speakers, the tests were written by Claude agents (and Claude was a contestant), and some scoring rules were set after seeing the outputs. Cite it with those caveats, as suggestive rather than conclusive.

---

## 3. Suggested recommendation (your decision; edit as you see fit)

> ⚠️ **Note added at merge, 24 Oct:** this draft was written while Part 2 still ran on Gemini. Two of its
> premises are now out of date: the prototype is **evaluated on Claude Haiku 5.5, not Gemini**, because
> Gemini couldn't be evaluated on the free tier, and Haiku has now been run on the same texts. The
> recommendation text below is left unchanged for you to revise.

**Draft:** use **Gemini 3.8 Flash on the paid tier through the Batch API**, which costs about $62 a month now and $124 from Jan 2027.
- Our prototype is already evaluated on it.
- Feedback doesn't need to arrive in real time, so batch processing overnight halves the cost.
- It did best on Indian languages in the one independent test.
- **Never use the free tier for student data:** Google may use it to improve its products.

**Alternative worth considering:** Claude Haiku 5.5 is about 7× cheaper and scores slightly higher on general benchmarks. But in-India processing isn't confirmed for 5.5, and its Tamil/Kannada quality isn't published. **Run Haiku on the same 37 texts before deciding.** If it matches Gemini's accuracy, the choice comes down to data residency.

**If the company must keep student data in India by law or policy:** Sarvam is the only option here with confirmed India-only processing. It is weaker on general reasoning, so it should be tested on our evaluation set first.

### Two risks
1. **Prices and models change.** Gemini Flash prices double on 1 Jan 2027, and 3.6 Flash is already marked as deprecated on Artificial Analysis. Mitigation: pin the model version, re-run the 60-row evaluation on every model change, and keep the code able to switch providers.
2. **Quality in Tamil and Kannada is unproven for this task.** No provider publishes Tamil or Kannada results, and our 60 labelled rows are English and Hinglish only. A wrong verdict tells a struggling student they're wrong when they're not. Mitigation: build a small evaluation set labelled by native speakers for each language before launch, and have a teacher spot-check a sample of "wrong" verdicts.

(Other risks you could swap in: prompt injection, since our data contains 3 attempts; and free-tier rate limits, about 5 requests/min observed, so production needs a paid tier.)

---

## 4. What I couldn't confirm (the brief asks you to say this)

- Whether **Gemini Flash 3.x can run inside India** on Vertex AI (the Mumbai column for those models was empty in what I could read).
- Whether **Claude Haiku 5.5** is available on Bedrock's India-only profile.
- Whether Sarvam uses customer data to improve its general models; also Sarvam's speed and rate limits.
- How long Google keeps paid-tier logs for abuse monitoring (it only says "limited period").
- Any **published Tamil or Kannada benchmark** for Gemini or Claude.
- Speed figures come from different sources and setups, so compare them only roughly.
- **Gemini's quality on our task**: never measured, because of the free-tier caps (see section 5).
- Token counts for any model other than Haiku on the final prompt (Gemini only has 17 calls on v1).
- Our own latency: not measured systematically; one timed Haiku smoke-test call took ~13 s end to end.

---

## 5. Measured on our task (from this repo)

Merged from the earlier `research_notes.md`. Source: `outputs/cache/usage_log.jsonl`,
`outputs/llm_eval_v1.md`, `outputs/llm_eval_v2.md`.

| Model / prompt | Calls | Avg input | Avg output (incl. thinking) | Accuracy, 60 rows / 37 unique |
|---|---|---|---|---|
| Claude Haiku 5.5, v1 | 76 | 1,217 | 260 | 80.0% / 83.8% |
| Claude Haiku 5.5, final v2 | 76 | 1,884 | 448 | 81.7% / 86.5% |
| Gemini 3.6 Flash, v1 (stopped by quota) | 17 | 512 | 115 + 429 thinking | not evaluated |
| Gemini 3.8 Flash, v1 (mostly 504 timeouts) | 4 | 514 | 124 + 268 thinking | not evaluated |

**Why Gemini couldn't be evaluated:**
- `gemini-3.8-flash` (newest Flash) was overloaded on the free tier. Most calls returned
  `504 DEADLINE_EXCEEDED`, and one run completed a single graded call in about 4.5 minutes.
- `gemini-3.6-flash` worked, at about 12 s a call, but the free tier allows about **5 requests a minute and
  20 a day per model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quota 20).
- One evaluation run needs 76 calls. The 17 results graded before the cap were discarded, so every reported
  number comes from one model (Claude Haiku 5.5).
- At 20 requests a day, the free tier would cover about 600 explanations a month, against 85,000 needed.

**Caching:** in our synthetic data, the 358 explanations by at-risk students are 47 unique texts, and grading
them took 9 new API calls. Real students won't repeat templates like this, so treat cache savings as an
upper bound (as in section 1).

**How much to trust our accuracy numbers:**
- **A feedback-only edit moved the score.** The first v2 run scored 90.0%. Changing only the wording of the
  feedback instructions (not the rubric) gave 81.7%: 4 of 37 unique texts changed verdict.
- **Re-runs alone move it too.** A plain re-run changes about 2 of 37.
- **So on these 60 rows, differences of a few points between prompts or models are within noise.**
  A real head-to-head needs a larger, fresh labelled set.

---

## Sources

**Pricing**
- [Gemini Developer API pricing, Google (official)](https://ai.google.dev/gemini-api/docs/pricing)
- [Claude API pricing, Anthropic (official): Haiku 5.5 $0.10 / $0.50 under 100K-token prompts; batch half price; `inference_geo: "us"` adds 1.1×](https://platform.claude.com/docs/en/about-claude/pricing?hsLang=en)
- [Sarvam API pricing, Sarvam AI (official)](https://www.sarvam.ai/api-pricing)
- [Rupee closes at 95.46 against US dollar, HDFC Sky](https://hdfcsky.com/news/rupee-rises-24-paise-to-close-at-95-46-against-us-dollar)

**Speed and quality**
- [Claude Haiku 5.5, Artificial Analysis](https://artificialanalysis.ai/models/claude-haiku-5-5)
- [Claude Haiku 5.5 vs Gemini 3.6 Flash, OrcaRouter](https://www.orcarouter.ai/blog/claude-haiku-5-5-vs-gemini-3-6-flash)
- [sarvam-field-test: Sarvam vs Gemini, OpenAI, Claude on Indian use cases (GitHub)](https://github.com/shivanathd/sarvam-field-test)
- [Multilingual support, Anthropic docs (official)](https://platform.claude.com/docs/en/build-with-claude/multilingual-support)

**Privacy and data residency**
- [Zero data retention in the Gemini Developer API, Google (official)](https://ai.google.dev/gemini-api/docs/zdr)
- [Data residency, Google Cloud (official)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/data-residency)
- [How long do you store my organization's data?, Anthropic Privacy Center (official)](https://privacy.claude.com/en/articles/7996866-is-my-data-used-for-model-training)
- [Anthropic LLM privacy summary, meetily.ai (secondary, quotes Anthropic's Commercial Terms)](https://meetily.ai/llm-privacy/anthropic)
- [Amazon Bedrock expands Claude availability to India, AWS (official)](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-expands-claude-model-availability-to-india-cross-region-inference/)
- [Sarvam Trust Center (official)](https://www.sarvam.ai/trust-center)
