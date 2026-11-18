# Notebook writing rules (draft for the `record` skill)

Agreed by the copy council (Opus, Fable, GPT; 17 Nov 2026), plus the researcher's own points:
- "maximise quick comprehension, not too terse nor verbose";
- "a hierarchy of headlines to details is good, but it shouldn't be too repetitious; sometimes it's ok to just get to the point fast".

## Structure (the researcher's choice, 17 Nov; council unanimous for it)
The notebook has two kinds of page, each written in one file:
- **Thread** (`threads/<id>.md`): one research question. It holds the current findings (each with a stable `F-` ID), Next (what's running, open questions with their cost, parked ones with the reason) and History (one line per change of belief, attached to the run that caused it).
- **Experiment** (`experiments/<id>.md`): the fixed record of one run.

Everything else is generated, never written by hand: the Threads home, the cross-thread Next view, History's run rows (question and answer, from each experiment), search, the running count, and the links between them. Write each fact once, in the file that owns it: run answers in the experiment, beliefs and next steps in the thread.

## Section labels (in the margin, plain words)
Thread page, per finding: [strength and dated status] Finding · Result · Method (ending with the experiments it rests on, each with its role) · Confidence · Caveats · Implication. Then Next · History.
Experiment page: Since then · Answer · Why we ran it · What was compared · Result · Method · Checks · Examples · Finding. This follows the results-page order in `style:functional-design`: what was compared comes before the results because it introduces the things compared and their colours.

## Rules
1. **Claim:** one sentence, 25 words or fewer, that stands alone. It names:
   - the condition (test set, model);
   - the metric;
   - the number vs its comparator ("0.79 vs 0.58 for mean-pool", "0.54 vs chance 0.50").

   Its verb matches the strength word. Tentative claims state the measurement and don't assert.
2. **Say each fact once, at the level that needs it.**
   - n goes in the caption, the setup in Method, the limits in Caveats.
   - The Scope line is the only place that may repeat.
   - No thread summaries that restate claims.
3. **Method:** 1–3 sentences, with no "we". In order:
   - model and layer;
   - training data;
   - test data;
   - what was compared;
   - seeds;
   - where the threshold was set.

   Don't gloss terms the researcher knows.
4. **Confidence reason:** says what earned the strength word and what holds it below the next one. Name the seeds, sets and controls. Never write "clean", "baselines" or "checked" without saying which.
5. **Caveats:** a specific limit on the claim, with its size if known (a 95% interval, n). The first caveat addresses the headline number. Never print a number no run produced; if something is unknown, say so.
6. **Implication:** at most 2 sentences. Lead with the decision it drives ("X is the default since 14 Nov"), then any interpretation, marked untested if it is. It never restates the claim or a caveat.
7. **Next:** each next step is written once, in its thread's Next section, as a question with the step that would answer it and its cost in GPU-minutes. A running experiment is named by its question and dated. Parked steps say why and what would bring them back.
8. **Experiment answer:** opens with Yes, No, Partly, Not yet or No answer. Then the deciding number vs its comparator, then seeds. At most 2 sentences and 30 words.
9. **History line:** a change of belief goes under the run that caused it, as "status change: gist" ("New finding, moderate: last-token beats pooling."), with the gist in 8 words or fewer. The run's answer beside it carries the numbers, so the gist doesn't repeat them.
10. **One term per thing:**
    - readout (last-token, mean-pool, max-pool);
    - "set" for a dataset, "split" only for train, dev and test;
    - dataset names exactly as in the glossary;
    - "vs" for every comparison.
11. **Numbers:** 2 decimals. Show the spread (and say what ± is) when there are 2 or more seeds, and n when it's under 500. Write counts as numerals ("3 seeds").
12. **Time-bound words** ("running", "waiting", "now", "yet") carry a date or an ID, and are updated when the thing they point to lands.
13. **Words to avoid:** "we" in Method, "partly", "something", "plausibly", "clean", "as expected", and "about" when the exact number is known.
14. **Experiment short names:** each experiment has one short name ("the readout sweep"), used wherever a sentence mentions it.
15. **Thread titles** are specific questions that name their subject and make sense on their own ("Does a probe trained on instructed lies catch other kinds of lie?", not "Does it transfer?"). A finding goes in the thread whose question it answers; if none fits, it starts a new thread.

## Verification and context (the researcher's points, 17 Nov)
"Reports should give me lots of ways to sanity-check that the experiment tests what it's meant to: understanding the method, and plots of baselines, skylines and metrics other than the central one." Also: "quick to get into the weeds while actively researching, and easy to understand an old experiment from weeks or months ago."

What's visible vs hidden: verification material is the hard part and stays visible. Bookkeeping (IDs, costs, run names, audit records, full setup) goes under "Code, data and records".

16. **Method is visible**, as one plain sentence on what is compared, then a train → probe → readout → threshold → test flow. Give n and class balance for every set, and say where the threshold was set. Every results page has this method, in a few lines, even when the main point is elsewhere: what was held fixed (model, layer, probe, how hyperparameters and thresholds were chosen) and what each seed varies.
17. **Every main chart shows what makes its number mean something:**
    - chance, as a line;
    - at least one trivial baseline that could fake the effect (a length-only classifier, a shuffled-label probe);
    - a skyline (a probe trained on the target set).

    All of these are scored like the real rows, on the same test set. If no skyline exists, say so under the chart and why.
18. **Sanity checks**, for any classifier:
    - the score distribution per true class, with the threshold marked;
    - the headline metric split along the most likely confound (response length, source, topic);
    - a table of secondary metrics (AUROC, precision, recall and accuracy for the positive class) for every row of the main chart.

    Each caption says what the plot shows and what a broken experiment would have looked like.
19. **Examples**: show a typical positive, the highest-scoring negative and the lowest-scoring positive, each with its score. Link to the rest, sorted by error.
20. **Why we ran it**: say what was believed before the run and what result would change it, with a link to the run that prompted it. Follow with the prediction, and whether it held.
21. **Since then**: whenever a later run, finding or decision changes how an experiment reads, add a dated line to it. An experiment page must make sense months later without memory of the time. (Target: generate these from the thread's History lines that cite the experiment.)
22. **Code, data and records**: list the commit, the script, the config, the rerun command, the results folder, the per-item predictions, the log and the full setup, so getting into the weeds takes one tap.

## Reporting evidence (council of 18 Nov, agreed by the researcher)
Three builds of one results page were judged against the intent of the design skill rather than its template. These rules are where all three judges agreed the pages fell short.

23. **The opening carries the deciding reason.** State the answer and the one fact most likely to change how the researcher acts on it, even when that fact comes from a check or a secondary metric rather than the headline number (for example, that upweighting doubles false flags on honest answers about harmful topics). If two metrics point different ways, the opening says so. Each claim gets one verdict, stated once, and a later number that pulls the other way is reconciled where it appears.
24. **Match each conclusion to the comparison that supports it.** Say which uncertainty a range shows: seed variation, the test sample, or the difference between two arms. Overlapping seed ranges don't show that two arms are the same; that needs the uncertainty of the difference. A recommendation names what it trades and why that trade is the right one for the use in mind.
25. **When the finding is a trade-off across test sets,** show every test set in one view first, in the order the opening cites them, then the per-test-set detail. Charts that sit side by side keep one row order.
26. **Checks add evidence.** Each check adds something not already visible on the page, and quotes the number that settles it. Start from the strongest alternative explanation of the headline difference, given what was manipulated (for a probe trained on harm-pressure lies: that it learned "harmful topic" rather than "lie"), and test it on every arm the claim covers. Drop a check whose answer a chart already shows, and point to the chart instead. Word each check so a problem shows in its answer.
27. **Examples are evidence.** Show the actual text, trimmed, with each arm's score and the threshold, so the reader can confirm the example shows what its heading claims. Include at least one example per headline claim and one failure, and say how they were chosen.
28. **How the data was built:** show where the rows come from as a flow (a diagram), and how the arms differ as a table of arm by component, including each component's share of the loss weight. Counts in a flow add up on sight, with any rows left over named. Keep the source of a row and its label distinct ("harm-pressure lies" vs "harm-pressure rows").
29. **Anything the result depends on is body text,** not a grey caption. A caption says how to read its figure, and sits at the first figure that needs it.
30. **Next is ordered by value.** Recommend the first step and say why it comes first. Give each step a cost, and say what result would change the current conclusion.

