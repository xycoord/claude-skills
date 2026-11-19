# Notebook writing rules (draft for the `record` skill)

How Claude writes up research in the notebook.

Research moves between two kinds of experiment, and each is written up differently:

- **Testing a hypothesis.** The experiment starts with a prediction. The write-up is mostly well-defined measures, plotted against what would make them mean something, ending in a verdict.
- **Looking for a hypothesis.** The experiment gathers data to find patterns. The write-up presents that data so the researcher can explore it, along with any patterns Claude spotted, offered for the researcher to judge. It ends in leads, not verdicts.

The mode belongs to each experiment, chosen by its purpose and recorded in its file (`mode: test` or `mode: explore`), since a thread often alternates between the two. The rules have five parts:

1. **Shared principles** for every write-up.
2. **Principles for testing a hypothesis.**
3. **Principles for looking for a hypothesis.**
4. **Worked examples** of each mode. They're illustrations, not templates: copy what they do, not their terms, sections or numbers.
5. **A glossary per project**, kept in the project's own repo, for the terms and names that project uses.

Every principle comes with its reason, so it can be applied to experiments these rules didn't foresee.

Sources: the copy council (Opus, Fable, GPT; 17 Nov 2026), the council on three test builds (18 Nov), and the researcher's own points:
- "maximise quick comprehension, not too terse nor verbose";
- "a hierarchy of headlines to details is good, but it shouldn't be too repetitious; sometimes it's ok to just get to the point fast";
- "Reports should give me lots of ways to sanity-check that the experiment tests what it's meant to: understanding the method, and plots of baselines, skylines and metrics other than the central one";
- "quick to get into the weeds while actively researching, and easy to understand an old experiment from weeks or months ago";
- on modes (19 Nov): experiments that test a hypothesis are "largely plotting well defined metrics", while the others "could be presenting data to explore to see if we spot any patterns", and Claude may do some of the exploring too, highlighting patterns for the researcher to evaluate.

Page design (layout, colour, charts, views of model internals, the order of a page) is in `style:functional-design`; these rules cover what the pages say. Words follow the researcher's Clear writing style.

## Structure (the researcher's choice, 17 Nov; council unanimous for it)

The notebook has two kinds of page, each written in one file:
- **Thread** (`threads/<id>.md`): one research question. It holds the current findings (each with a stable `F-` ID), Next (what's running, open leads and questions with their cost, parked ones with the reason) and History (one line per change of belief, attached to the run that caused it).
- **Experiment** (`experiments/<id>.md`): the fixed record of one run, in one of the two modes.

Everything else is generated, never written by hand: the Threads home, the cross-thread Next view, History's run rows, search, the running count, and the links between them. Write each fact once, in the file that owns it: run answers in the experiment, beliefs and next steps in the thread.

A **finding** comes only from testing a hypothesis. Looking for one produces **leads**, which sit under the thread's Next until a test confirms or rejects them. A lead never becomes a finding without a test, because a pattern found by looking is the start of evidence, not the end of it.

Sections, labelled in the margin with plain words:
- Thread page, per finding: strength and dated status, then Finding, Result, Method (ending with the experiments it rests on and the role of each), Confidence, Caveats, Implication. Then Next and History.
- Experiment page, testing a hypothesis: Since then, Answer, Why we ran it, What was compared, Result, Method, Checks, Examples, Finding.
- Experiment page, looking for a hypothesis: Since then, What was seen, Why we looked, The data, Patterns, Looked at and found nothing, Method, Leads.

## Part 1: Shared principles

1. **The opening says the most important thing first.** For a test, that's the answer; for exploration, it's what was seen. A reader who stops after the opening should not be misled.
2. **The method is visible** in a few lines: what was held fixed, what varied, what it was run on, how choices such as hyperparameters, thresholds or the slice of data were made, and what each repeat changes. A reader can't judge a result or a pattern without it, and a reader months later can't reconstruct it.
3. **Why we ran it:** what was believed or wondered before the run, linking the run that prompted it. For a test, add the prediction and whether it held.
4. **Since then:** whenever later work changes how an experiment reads, it gets a dated line, generated from the thread's History where possible. An experiment page must make sense months later without memory of the time.
5. **Code, data and records** list everything needed to get into the weeds in one tap: the commit, script, config, rerun command, results folder, per-item outputs, log and full setup.
6. **Say each fact once, at the level that needs it.** Sizes go in captions, the setup in the method, the limits in caveats. No summaries that restate claims.
7. **Anything the conclusion depends on is body text,** not a caption. A caption says how to read its figure, and sits at the first figure that needs it.
8. **Numbers use the same precision for the same kind of figure everywhere,** show their spread when there are repeats (and say what the spread is), and give n when it's small enough to matter. Counts are numerals ("3 seeds").
9. **Time-bound words** ("running", "now", "yet") carry a date or an ID, and are updated when the thing they point to lands.
10. **One name per thing,** taken from the project's glossary: each experiment has one short name used in every sentence, and every comparison uses "vs". A model's token is written in monospace rather than in quotes, with its leading space kept inside (` Austin`), so it reads as a token rather than a word.
11. **Avoid** "we" in a method, and "partly", "something", "plausibly", "clean", "as expected", and "about" when the exact number is known.
12. **Thread titles are specific questions** that name their subject and make sense alone. A finding or lead goes in the thread whose question it bears on; if none fits, it starts one.
13. **A history line** goes under the run that caused the change of belief, as "status change: gist", with the gist in 8 words or fewer. The run's answer beside it carries the numbers.
14. **Next is ordered by value,** written once in its thread: each step is a question with the action that would answer it and its cost. Recommend the first and say why it's first, and say what result would change the current view. Parked steps say why and what would bring them back.

## Part 2: Testing a hypothesis

15. **A claim stands alone.** One sentence that names the condition it holds under, the measure, and the number against its comparator, so it can be quoted anywhere without its page. Its verb matches its strength word: a tentative claim states the measurement and doesn't assert.
16. **The answer opens with its verdict** (Yes, No, Partly, Not yet, No answer), then the deciding number against its comparator. The verdict first lets the reader stop there.
17. **The opening carries the deciding reason:** the answer and the one fact most likely to change how the researcher acts on it, even when that fact comes from a check or a secondary measure. If two measures point different ways, the opening says so. Each claim gets one verdict, stated once, and a number that pulls the other way is reconciled where it appears.
18. **Match each conclusion to the comparison that supports it.** Say which uncertainty a range shows (repeat runs, the size of the test sample, or the difference between two arms), because each supports a different conclusion. Ranges that overlap don't show two arms are the same; that needs the uncertainty of the difference. A recommendation names what it trades and why that trade suits the use in mind.
19. **Every main result shows what makes its number mean something,** on the same scale: what nothing would score, what something trivial scores, and the best score reachable. If one of these doesn't exist, say so and why. A number alone can't say whether it's good.
20. **Show what sits behind the headline number:** how it's distributed, how it splits along the likeliest confound, and the other measures that could disagree with it. Each says what a broken experiment would have looked like.
21. **Checks add evidence.** Each adds something not already visible and quotes the number that settles it. Start from the strongest alternative explanation of the headline difference, given what was manipulated, and test it on every arm the claim covers. Drop a check whose answer a chart already shows, and word each check so a problem shows in its answer.
22. **Examples are evidence.** Show the real item, trimmed, with each arm's output or score and the decision line, so the reader can confirm the example shows what its heading claims. Include a typical case, the worst failure in each direction, and the case nearest the decision line, and say how they were chosen.
23. **Show how the data was built twice over:** where it comes from as a flow, and how the arms differ as a table. Counts in a flow add up on sight, with anything left over named. Keep where an item came from and what it's labelled as distinct.
24. **When the finding is a trade-off,** show every side of it in one view first, in the order the opening cites them, then the detail. Charts that sit side by side keep one row order.
25. **Confidence says what earned its strength word and what holds it below the next one,** naming the evidence (seeds, sets, controls, replications) rather than calling it "clean" or "checked". The reason is what lets the reader disagree.
26. **Caveats are specific limits with their size where known,** the one on the headline number first. Never print a number no run produced; if something is unknown, say so.
27. **The implication leads with the decision it drives** ("X is the default since 14 Nov"), then any interpretation, marked untested if it is. It never restates the claim or a caveat.

## Part 3: Looking for a hypothesis

Here the page is an instrument as much as a report: its main reader is doing the exploring. The aim is to make patterns findable and easy to judge, without claiming more than looking can show.

28. **The opening says what data was gathered, what was looked at, and what stood out,** with anything that stood out labelled as a candidate, not a finding.
29. **Present the data in views built for spotting patterns:** overall distributions, slices along the dimensions that might matter, small views side by side on one scale for comparison, and a table of the individual items that can be sorted and filtered. Raw items are one step away from any mark. The best view is often not a standard chart; `style:functional-design` covers views of model internals, and new kinds of view are expected.
30. **Each pattern Claude highlights is offered for the researcher to judge,** with four things:
    - **where to see it:** a link to the view that shows it, so the judgement rests on the data rather than on Claude's description;
    - **how it was found:** how many things Claude looked at before this stood out, because a pattern found after checking fifty slices is far more likely to be a fluke than one checked on purpose;
    - **a cheap test of whether it's noise:** whether it survives another seed, a shuffled control or a held-out slice;
    - **what counts against it,** including the examples that don't fit.
31. **Record what was looked at and showed nothing,** with how it was looked at, so it isn't repeated and its absence can be checked later.
32. **Don't summarise a pattern into more than the data shows.** Describe what's there ("the false alarms are mostly refusals") rather than its cause ("the probe detects refusals"), unless the cause was tested.
33. **Leads end the page:** each candidate pattern the researcher wants to follow becomes a hypothesis, with the test that would confirm or reject it and its cost. This is the handover to Part 2, and the lead sits under the thread's Next until that test runs.

## Part 4: Worked examples

### Testing a hypothesis: a probe experiment

From the lie-detection work, where linear probes on a model's activations are trained on one kind of lie and tested on others.

- **A claim (15):** "On harm-pressure lies, last-token readout reaches 0.79 macro-F1 vs 0.58 for mean-pool." The condition is the test set, the measure is macro-F1, and the comparator is the other readout.
- **An answer (16):** "No. AUROC 0.54 on sandbagging (chance 0.50) vs 0.93 on held-out instructed lies. 3 seeds."
- **The deciding reason (17):** a comparison of training sets found that upweighting harm-pressure lies added 0.02 AUROC but doubled false flags on honest answers about harmful topics, from 7% to 15%. The opening said that, not just the AUROC gain.
- **A method (2),** as a flow: train on instructed lies (n = 2,400, 50% lies), logistic regression on layer-16 activations per token, three readouts of the per-token scores, a threshold per readout set on a dev split, test on harm-pressure v2 (n = 1,180, 48% lies).
- **References (19):** chance as a dashed line; a classifier that sees only response length and a probe trained on shuffled labels as trivial scores; a probe trained on the target set as the best reachable. On sandbagging no probe had been trained, so the page said there was no skyline and why.
- **Behind the headline (20):** each readout's score distribution for honest answers and lies, with the threshold marked; macro-F1 split by response-length quartile, because longer responses could dilute a pooled readout; a table of AUROC, precision, recall and accuracy for every row of the main chart.
- **A check aimed at the alternative explanation (21):** training on harm-pressure lies might teach the probe "harmful topic" rather than "lie", so the check scored every arm on honest answers about harmful topics.
- **Examples (22):** a typical lie, the highest-scoring honest answer (a false alarm), and the lowest-scoring lie (a miss), each with its score and the threshold.
- **How the data was built (23):** a diagram of three sources split into train and test parts feeding three training sets, and a table of each training set by source and label, with counts and each part's share of the loss weight. The table showed that rebalancing also halved the weight on instructed lies.

### Testing a hypothesis: a fine-tuning sweep

A second kind of test, to show where the principles bend. The question is whether a learning rate of 3e-5 beats 1e-5 when fine-tuning an 8B model on 20,000 instruction examples.

- **A claim (15):** "On the held-out instruction set, a learning rate of 3e-5 gives a 61% win rate against the base model vs 54% for 1e-5." The measure is win rate judged by a fixed grader, and the comparator is the other learning rate.
- **The deciding reason (17):** if 3e-5 wins on instructions but loses 4 points on a reasoning benchmark the base model was good at, the opening says so, because that cost decides whether to adopt it.
- **A method (2):** the data, steps, batch size, schedule, grader and its prompt were held fixed; only the learning rate varied; each of 3 seeds changes the data order and the adapter's initialisation.
- **References (19):** the base model's win rate against itself (50%) is what nothing scores; a model trained for 10 steps is a trivial score; a larger model or a published result on the same set is the best reachable, if one exists.
- **Behind the headline (20):** training and validation loss for every seed, to show whether 3e-5 is unstable or overfitting; win rate split by instruction category, because a gain in one category can hide a loss in another; the reasoning and safety benchmarks that could disagree.
- **A check aimed at the alternative explanation (21):** a higher learning rate might make answers longer, and graders often prefer longer answers, so the check compares win rates on length-matched pairs.
- **How the data was built (23):** with one dataset and no arms built differently, a flow adds nothing, so the method's one line on the data is enough. Principle 23 applies when arms are built from shared sources.

### Looking for a hypothesis: the probe's false alarms

The last-token probe flags 4% of honest answers as lies. This experiment gathered those false alarms to see whether they have anything in common, with no prediction.

- **The opening (28):** "Gathered the 212 honest answers the probe flagged, out of 5,300, with each token's score. Two things stood out, both candidates: most false alarms are refusals, and their scores peak on the first sentence rather than at the end."
- **The data (29):** the false alarms' scores against all honest answers' scores; the false-alarm rate sliced by topic, response length, whether the answer refuses, and the system prompt; and a table of all 212, sortable by score, topic and length, each opening to its full text with token highlights.
- **A highlighted pattern (30):**
  - **where to see it:** the slice by refusal, and the 212 filtered to refusals;
  - **how it was found:** Claude sliced by 9 attributes, and this was the largest difference;
  - **a noise test:** it holds in each of 3 seeds, and in a held-out half of the honest answers (61% and 58% refusals, vs 12% of all honest answers);
  - **what counts against it:** 39 of the false alarms are ordinary helpful answers with no refusal, and their scores look no different.
- **Looked at and found nothing (31):** response length, the system prompt and the position of the answer in the conversation, each sliced into quartiles, showed no difference in the false-alarm rate.
- **Describing, not explaining (32):** the page says "most false alarms are refusals", not "the probe detects refusals"; the second is a hypothesis.
- **Leads (33):** "Does the probe score refusals higher than other honest answers when topic is matched?" Test: score 500 refusals and 500 topic-matched helpful answers, about 10 GPU-min. It sits under the transfer thread's Next until it runs.

## Part 5: Project glossary

Each project keeps its own glossary of terms, dataset names and conventions, in its repo, so the record skill stays general. The lie-detection project's glossary currently lives in `drafts/glossary-lie-detection.md`, to move into the project's repo when the `record` skill is written.
