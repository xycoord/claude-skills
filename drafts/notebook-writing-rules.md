# Notebook writing rules (draft for the `record` skill)

How Claude writes up research in the notebook. It has three parts:

1. **Principles** that hold for any experiment, each with the reason it exists. These are the rules.
2. **Worked examples** that show one way to meet each principle, from two kinds of experiment. They're illustrations, not templates: copy what they do, not their terms, sections or numbers.
3. **A glossary per project**, kept in the project's own repo, for the terms and names that project uses.

Sources: the copy council (Opus, Fable, GPT; 17 Nov 2026), the council on three test builds (18 Nov), and the researcher's own points:
- "maximise quick comprehension, not too terse nor verbose";
- "a hierarchy of headlines to details is good, but it shouldn't be too repetitious; sometimes it's ok to just get to the point fast";
- "Reports should give me lots of ways to sanity-check that the experiment tests what it's meant to: understanding the method, and plots of baselines, skylines and metrics other than the central one";
- "quick to get into the weeds while actively researching, and easy to understand an old experiment from weeks or months ago."

Page design (layout, colour, charts, the order of a results page) is in `style:functional-design`; these rules cover what the pages say. Words follow the researcher's Clear writing style.

## Structure (the researcher's choice, 17 Nov; council unanimous for it)

The notebook has two kinds of page, each written in one file:
- **Thread** (`threads/<id>.md`): one research question. It holds the current findings (each with a stable `F-` ID), Next (what's running, open questions with their cost, parked ones with the reason) and History (one line per change of belief, attached to the run that caused it).
- **Experiment** (`experiments/<id>.md`): the fixed record of one run.

Everything else is generated, never written by hand: the Threads home, the cross-thread Next view, History's run rows, search, the running count, and the links between them. Write each fact once, in the file that owns it: run answers in the experiment, beliefs and next steps in the thread.

Sections, labelled in the margin with plain words:
- Thread page, per finding: strength and dated status, then Finding, Result, Method (ending with the experiments it rests on and the role of each), Confidence, Caveats, Implication. Then Next and History.
- Experiment page: Since then, Answer, Why we ran it, What was compared, Result, Method, Checks, Examples, Finding. What was compared comes before the results because it introduces the things compared and their colours.

## Part 1: Principles

### Claims and answers

1. **A claim stands alone.** One sentence that names the condition it holds under, the measure, and the number against its comparator, so it can be quoted anywhere without its page. Its verb matches its strength word: a tentative claim states the measurement and doesn't assert.
2. **An experiment's answer opens with its verdict** (Yes, No, Partly, Not yet, No answer), then the deciding number against its comparator, in a sentence or two. The verdict first lets the reader stop there.
3. **The opening carries the deciding reason.** State the answer and the one fact most likely to change how the researcher acts on it, even when that fact comes from a check or a secondary measure rather than the headline number. If two measures point different ways, the opening says so. Each claim gets one verdict, stated once, and a number that pulls the other way is reconciled where it appears. A reader who stops after the opening should not be misled.
4. **Confidence says what earned its strength word and what holds it below the next one,** naming the evidence (seeds, sets, controls, replications) rather than calling it "clean" or "checked". The reason is what lets the reader disagree.
5. **Caveats are specific limits with their size where known,** the one on the headline number first. Never print a number no run produced; if something is unknown, say so.
6. **The implication leads with the decision it drives** ("X is the default since 14 Nov"), then any interpretation, marked untested if it is. It never restates the claim or a caveat.

### Evidence

7. **Match each conclusion to the comparison that supports it.** Say which uncertainty a range shows (repeat runs, the size of the test sample, or the difference between two arms), because each supports a different conclusion. Ranges that overlap don't show two arms are the same; that needs the uncertainty of the difference. A recommendation names what it trades and why that trade suits the use in mind.
8. **The method is visible on every results page,** in a few lines: what was held fixed, what varied between the arms, what it was tested on, how choices such as hyperparameters and thresholds were made, and what each repeat changes. A reader can't judge a result without it, and a reader months later can't reconstruct it.
9. **Every main result shows what makes its number mean something,** on the same scale: what nothing would score, what something trivial scores, and the best score reachable. If one of these doesn't exist, say so and why. A number alone can't say whether it's good.
10. **Show what sits behind the headline number:** how it's distributed, how it splits along the likeliest confound, and the other measures that could disagree with it. Each says what a broken experiment would have looked like.
11. **Checks add evidence.** Each check adds something not already visible on the page and quotes the number that settles it. Start from the strongest alternative explanation of the headline difference, given what was manipulated, and test it on every arm the claim covers. Drop a check whose answer a chart already shows, and word each check so a problem shows in its answer.
12. **Examples are evidence.** Show the real item, trimmed, with each arm's output or score and the decision line, so the reader can confirm the example shows what its heading claims. Include a typical case, the worst failure in each direction, and the case nearest the decision line, and say how they were chosen.
13. **Show how the data was built twice over:** where it comes from as a flow, and how the arms differ as a table. Counts in a flow add up on sight, with anything left over named. Keep where an item came from and what it's labelled as distinct.
14. **When the finding is a trade-off,** show every side of it in one view first, in the order the opening cites them, then the detail. Charts that sit side by side keep one row order.
15. **Anything the result depends on is body text,** not a caption. A caption says how to read its figure, and sits at the first figure that needs it.

### Context, for reading it later

16. **Why we ran it:** what was believed before the run and what result would change it, linking the run that prompted it, then the prediction and whether it held.
17. **Since then:** whenever later work changes how an experiment reads, it gets a dated line, generated from the thread's History where possible. An experiment page must make sense months later without memory of the time.
18. **Code, data and records** list everything needed to get into the weeds in one tap: the commit, script, config, rerun command, results folder, per-item outputs, log and full setup.

### Words and bookkeeping

19. **Say each fact once, at the level that needs it.** Sizes go in captions, the setup in the method, the limits in caveats. No summaries that restate claims.
20. **Numbers use the same precision for the same kind of figure everywhere,** show their spread when there are repeats (and say what the spread is), and give n when it's small enough to matter. Counts are numerals ("3 seeds").
21. **Time-bound words** ("running", "now", "yet") carry a date or an ID, and are updated when the thing they point to lands.
22. **One name per thing,** taken from the project's glossary: each experiment has one short name used in every sentence, and every comparison uses "vs".
23. **Avoid** "we" in a method, and "partly", "something", "plausibly", "clean", "as expected", and "about" when the exact number is known.
24. **Thread titles are specific questions** that name their subject and make sense alone. A finding goes in the thread whose question it answers; if none fits, it starts one.
25. **A history line** goes under the run that caused the change of belief, as "status change: gist", with the gist in 8 words or fewer. The run's answer beside it carries the numbers.
26. **Next is ordered by value,** written once in its thread: each step is a question with the action that would answer it and its cost. Recommend the first and say why it's first, and say what result would change the current conclusion. Parked steps say why and what would bring them back.

## Part 2: Worked examples

### A probe experiment

From the lie-detection work, where linear probes on a model's activations are trained on one kind of lie and tested on others.

- **A claim (1):** "On harm-pressure lies, last-token readout reaches 0.79 macro-F1 vs 0.58 for mean-pool." The condition is the test set, the measure is macro-F1, and the comparator is the other readout.
- **An answer (2):** "No. AUROC 0.54 on sandbagging (chance 0.50) vs 0.93 on held-out instructed lies. 3 seeds."
- **The deciding reason (3):** a comparison of training sets found that upweighting harm-pressure lies added 0.02 AUROC but doubled false flags on honest answers about harmful topics, from 7% to 15%. The opening said that, not just the AUROC gain.
- **A method (8),** as a flow: train on instructed lies (n = 2,400, 50% lies), logistic regression on layer-16 activations per token, three readouts of the per-token scores, a threshold per readout set on a dev split, test on harm-pressure v2 (n = 1,180, 48% lies).
- **References (9):** chance as a dashed line; a classifier that sees only response length and a probe trained on shuffled labels as trivial scores; a probe trained on the target set as the best reachable. On sandbagging no probe had been trained, so the page said there was no skyline and why.
- **Behind the headline (10):** each readout's score distribution for honest answers and lies, with the threshold marked; macro-F1 split by response-length quartile, because longer responses could dilute a pooled readout; a table of AUROC, precision, recall and accuracy for every row of the main chart.
- **A check aimed at the alternative explanation (11):** training on harm-pressure lies might teach the probe "harmful topic" rather than "lie", so the check scored every arm on honest answers about harmful topics.
- **Examples (12):** a typical lie, the highest-scoring honest answer (a false alarm), and the lowest-scoring lie (a miss), each with its score and the threshold.
- **How the data was built (13):** a diagram of three sources split into train and test parts feeding three training sets, and a table of each training set by source and label, with counts and each part's share of the loss weight. The table showed that rebalancing also halved the weight on instructed lies.

### A fine-tuning sweep

A second kind of experiment, to show where the principles bend. The question is whether a learning rate of 3e-5 beats 1e-5 when fine-tuning an 8B model on 20,000 instruction examples.

- **A claim (1):** "On the held-out instruction set, a learning rate of 3e-5 gives a 61% win rate against the base model vs 54% for 1e-5." The condition is the held-out set, the measure is win rate judged by a fixed grader, and the comparator is the other learning rate.
- **The deciding reason (3):** if 3e-5 wins on instructions but loses 4 points on a reasoning benchmark the base model was good at, the opening says so, because that cost decides whether to adopt it.
- **A method (8):** the data, steps, batch size, schedule, grader and its prompt were held fixed; only the learning rate varied; each of 3 seeds changes the data order and the adapter's initialisation.
- **References (9):** the base model's win rate against itself (50%) is what nothing scores; a model trained for 10 steps is a trivial score; a larger model or a published result on the same set is the best reachable, if one exists.
- **Behind the headline (10):** training and validation loss for every seed, to show whether 3e-5 is unstable or overfitting; win rate split by instruction category, because a gain in one category can hide a loss in another; the reasoning and safety benchmarks that could disagree.
- **A check aimed at the alternative explanation (11):** a higher learning rate might make answers longer, and graders often prefer longer answers, so the check compares win rates on length-matched pairs.
- **Examples (12):** a typical win, the clearest loss, and a case the grader scored as a near tie, each with both models' outputs side by side.
- **How the data was built (13):** with one dataset and no arms built differently, a flow adds nothing, so the method's one line on the data is enough. Principle 13 applies when arms are built from shared sources.

## Part 3: Project glossary

Each project keeps its own glossary of terms, dataset names and conventions, in its repo, so the record skill stays general. The lie-detection project's glossary currently lives in `drafts/glossary-lie-detection.md`, to move into the project's repo when the `record` skill is written.
