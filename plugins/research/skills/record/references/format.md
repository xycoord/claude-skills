# Notebook file format

The research repo (`xycoord/ai-research`) is the source of truth. The notebook is one page built from these files by `scripts/build_notebook.py` and published as a pinned claude.ai artifact. Every fact is written once, in the file that owns it: run answers in the experiment, beliefs and next steps in the thread. Everything else is generated: the Threads home, the Next view, History's rows of runs, each experiment's "Since then" lines from the thread's History, the findings and leads listed on an experiment page, and search.

## Layout

```
threads/<thread-id>.md            one research question
experiments/<experiment-id>/
    README.md                     the fixed record of one run
    figs/<name>.json              figures the README shows (optional)
glossary.yaml                     the project's terms, names and synonyms
notebook.yaml                     the notebook's settings (title, the notebook's and Drafts page's URLs)
```

IDs:

- A thread id is a short kebab-case slug (`readout`), and matches its file name.
- An experiment id is `E-YYYY-MM-DD-<slug>` (`E-2026-11-12-agg-sweep`), and matches its folder name.
- A finding id is `F-<slug>` and is unique across the repo.
- A lead or open question id is `Q-<slug>`, also unique across the repo.

Folders and files whose names start with `.` or `_`, and a `README.md` in `threads/`, are skipped, so notebook checkpoints and a note explaining a folder don't break the build.

## Writing YAML fields

- **Quote prose fields, or write them as block scalars.** YAML reads some unquoted words as other types, so `answer: No` becomes false, and it cuts an unquoted value at ` #`, taking the rest as a comment. Prose fields (`question`, `answer`, `short`, `claim`, `method`, `confidence`, `caveats`, `implication`, `retracted`, `action`, `settles`, `parked`, `line`, and the prediction's `text` and `how`) must be text, and the build stops on one that isn't, or on one that a ` #` cut short. A long field reads best as a folded block scalar:

  ```yaml
  answer: >-
    No. AUROC 0.54 on sandbagging (chance 0.50) vs 0.93 on held-out
    instructed lies. 3 seeds.
  ```

- **Dates are ISO dates**, such as `2026-11-14`, in every date field. The build stops on any other form, such as `14 Nov`.
- **Numbers are numbers**: `cost_gpu_min`, `cost_cpu_min`, `cost_usd` and `pr` unquoted, and `commit` a hash.

## threads/<thread-id>.md

YAML front matter, then optional free notes, which the notebook doesn't show.

```yaml
---
id: readout
title: Which token should the probe read?          # a specific question that makes sense alone
findings:                                         # current, superseded and retracted claims; order = display order
  - id: F-last-token
    status: current                               # current | superseded | retracted
    strength: strong                              # strong | moderate | tentative
    date: 2026-11-14                              # date of its current status (written, raised, replaced, retracted)
    raised: true                                  # optional: true if `date` is when it was raised, not first written
    claim: On harm-pressure lies, last-token readout reaches 0.79 macro-F1 vs 0.58 for mean-pool.
    short: Last-token beats pooling               # a few words, for indexes
    method: Linear probe at layer 16 of Llama 3.1 8B ...   # 1–3 sentences
    evidence:
      - { experiment: E-2026-11-12-agg-sweep, role: original }
      - { experiment: E-2026-11-14-agg-replicate, role: replication }
    figure: E-2026-11-12-agg-sweep/main           # optional: <experiment-id>/<fig name>
    confidence: 3 seeds agree, and the gap replicates on the convincing-game set; ...
    caveats: One model so far. The gap is smaller on convincing-game (0.71 vs 0.59).
    implication: Last-token is the default readout since 14 Nov. ...
    replaced_by: F-...                            # superseded only
    retracted: Train–test leak ...                # retracted only: why
next:                                             # what's running, open leads and questions, parked; order = value, best first
  - id: Q-other-family
    question: Does the last-token advantage hold on another model family?
    action: Run the readout comparison on Qwen 2.5 7B.
    cost_gpu_min: 50                              # optional: GPU-minutes, for work on a pod
    cost_cpu_min: 10                              # optional: minutes on CPU in a session, instead of cost_gpu_min
    state: running                                # open | running | parked (open if left out)
    experiment: E-2026-11-17-qwen-agg             # once planned (state stays open until it runs)
    settles: No gap there would narrow the finding to Llama.   # optional
    lead: false                                   # true if it came from exploration (an untested pattern)
    from: E-2026-11-18-false-alarms               # optional: the experiment a lead came from; it's listed under that page's Leads
    parked: too costly (about 12 GPU-hours)       # parked only: why, and what would bring it back
history:                                          # changes of belief, each attached to the run that caused it
  - { experiment: E-2026-11-14-agg-replicate, date: 2026-11-14, line: "Raised to strong. Last-token became the default readout." }
---
```

A history line reads "status change: gist". The notebook sets the part up to the first full stop or colon in bold.

## experiments/<experiment-id>/README.md

YAML front matter, then the write-up in Markdown under fixed `##` section headings. The notebook shows each heading as a margin label, in the mode's order whatever the file's order.

```yaml
---
id: E-2026-11-12-agg-sweep
thread: readout
mode: test                                        # test (testing a hypothesis) | explore (looking for one)
status: done                                      # planned | running | done | abandoned | retracted
date: 2026-11-12                                  # when it was planned; matches the id
started: 2026-11-12                               # optional: when it started running, for "Running since" and "Run"
short: the readout sweep                          # one short name, used in every sentence that mentions it
question: Does reading the probe at the last token beat pooling on harm-pressure lies?
answer: Yes. Macro-F1 0.79 (0.77–0.81) for last-token vs 0.58 (0.55–0.61) for mean-pool. 3 seeds.
                                                  # explore mode: what was seen, in a sentence or two
prediction:                                       # test mode only, written before the run
  text: Last-token beats mean-pool by at least 0.05 macro-F1.
  written: 2026-11-11
  held: true                                      # after the run: true | false | partly (left out for No answer)
  how: last-token beat mean-pool by 0.21 macro-F1
commit: a1b2c3d
pr: 12                                            # ai-research PR number, optional
results: [runs/claude-agg-sweep-1, runs/claude-agg-sweep-2]   # paths in the HF dataset xycoord/research-results
cost_usd: 3.80
rerun: uv run probes/readout_sweep.py -c configs/E-2026-11-12-agg-sweep.yaml
since:                                            # dated lines added when later work changes how this reads
  - { date: 2026-11-14, line: "Replicated on convincing-game, with a smaller gap." }
amended:                                          # changes to the plan made before the real run, each dated; shown at the end of Method
  - { date: 2026-11-11, line: "Added max-pool as a third readout." }
---
```

Sections:

- Test mode: `## Why we ran it`, `## What was compared`, `## Result`, `## Method`, `## Checks`, `## Examples`, `## Caveats`.
- Explore mode: `## Why we looked`, `## The data`, `## Patterns`, `## Looked at and found nothing`, `## Method`.

Any section may be missing. The opening (the answer, or what was seen) comes from the front matter, not a section. `###` headings inside a section are fine, for example one per pattern. The notebook adds the rest of the page itself: Since then (the `since` lines plus later changes of belief from the thread's History), the prediction under Why we ran it, the findings that cite the run, and for exploration the Leads whose `from` names it.

`since` is for changes the thread's History doesn't already say, because History lines that bear on a run reach its page by themselves.

## Text in either file

Prose fields in the front matter and the write-up are Markdown.

- **Raw HTML is shown as text**, exactly as written, so quoted model output such as `<think>` or `<s>` stays visible and nothing in a file can run on the page.
- **Inside fenced code blocks**, `##` lines and `::fig` lines are just code: they don't start sections or place figures.

- **Links** to other pages are hash links: `[the readout sweep](#E-2026-11-12-agg-sweep)`, `#F-<id>` for a finding, `#Q-<id>` for a next step, `#t-<thread-id>` for a thread. The build fails on a link to anything that doesn't exist.
- **Tokens** go in backticks with their leading space kept, as `` ` Austin` ``. A code span that starts or ends with a space is set as a token; any other code span is set as code.
- **Verdicts:** a test's answer that opens with Yes, No, Partly, Not yet or No answer, followed by a full stop, comma or colon, has that verdict set in bold.

## experiments/<id>/figs/<name>.json

A figure is the arguments of one call into the design kit (`style:functional-design`: charts.js and interp.js), plus a title and caption, or a custom view when no kit view fits. It's placed in the write-up by a line of its own, `::fig <name>`.

```json
{ "view": "dotChart", "title": "Macro-F1 by readout", "caption": "Harm-pressure v2 test set, n = 1,180. Mean and range of 3 seeds.",
  "options": { "metric": "Macro-F1", "from": 0.4, "to": 1, "lines": [{"v": 0.5, "label": "chance"}],
               "rows": [{"label": "Last-token", "v": 0.79, "lo": 0.77, "hi": 0.81, "c": 1}],
               "refs": [{"label": "Shuffled labels", "v": 0.50, "lo": 0.49, "hi": 0.51}] } }
```

- `view` is one of the kit's functions: `dotChart`, `lineChart`, `barChart`, `distChart`, `tokenText`, `topExamples`, `heatmap`, `lensExplorer`, `logitLens`, `graph`. Their comments in charts.js and interp.js say what `options` each takes.
- JSON can't hold a function, so a chart's number format is given as `digits` (decimal places), `percent: true` (shows 0.17 as 17%), `prefix` or `suffix`, and a heatmap's `mask` as `"causal"` (hides cells above the diagonal).
- A figure with `"bleed": true` uses the full page width.
- A table is `{ "view": "table", "head": [...], "rows": [[...]], "numeric": [false, true, ...] }`. Numeric columns are right-aligned and keep their decimal places; `digits` fixes them. Cells that are strings may use inline Markdown, such as `**0.79**`.
- Title and caption may use inline Markdown too, for tokens in particular.
- The bookkeeping disclosure shows the values behind every dot, line and bar chart, so a reader can check a chart's numbers.

A **custom view** draws anything the kit doesn't, from its own code. The JSON holds the data, and `figs/<name>.js` beside it holds the drawing code, as the body of `function (el, data)`: it fills `el` with the figure, using `data` from the JSON.

```json
{ "view": "custom", "title": "Each feature's direction in the hidden space", "caption": "Columns of W at S = 0.9, seed 1.",
  "data": { "features": [{ "name": "Feature 1", "x": 0.98, "y": 0.10 }] },
  "values": { "head": ["Feature", "x", "y"], "rows": [["Feature 1", 0.98, 0.10]] } }
```

- The code runs in the notebook page, after the kit, so it can use the kit's helpers: `FD.draw` (draws at the container's width and redraws on resize), `FD.svg`, `FD.text`, `FD.col` (series colours), `FD.hit` (a hover target with the exact value) and `FD.esc` from charts.js, and `IV.tint`, `IV.key` and `IV.tok` from interp.js. It uses the kit's colour tokens, such as `var(--s1)`, never colours of its own. A view whose colours encode values marks `el` with `data-viz`.
- `values` is optional: a table of the numbers behind the figure, shown in the bookkeeping disclosure like a kit chart's.
- The build checks the code's syntax with `node --check` when node is installed, and refuses `</script` or `<!--` in it, which would end the page's script. Each custom view runs in its own script, so one that fails at run time shows an error in its own place and leaves the rest of the page working.

## glossary.yaml

```yaml
terms:
  - term: readout
    means: how a probe's per-token scores become one score for a response
    values: [last-token, mean-pool, max-pool]
    synonyms: [aggregation, pooling method]
  - term: mean-pool
    synonyms: [mean aggregation, average pooling]
datasets:
  - name: harm-pressure v2
    synonyms: [harm pressure, HP]
conventions:
  - Every comparison uses "vs".
  - '"set" means a dataset; "split" only train, dev and test.'
  - Tokens are written in monospace, not quotes, with their leading space kept.
```

Search in the notebook expands a query through these synonyms, so "mean aggregation" finds mean-pool experiments, and says which names it also matched.

## notebook.yaml

```yaml
title: ai-research notebook
artifact: https://claude.ai/artifact/<id>        # the pinned notebook; every session publishes here
drafts: https://claude.ai/artifact/<id>          # the pinned Drafts page: open pull requests before they merge
last_visit: null                                  # optional: date used to mark changes as new
repo: xycoord/ai-research                         # optional: the GitHub repo that links point to (this is the default)
results: xycoord/research-results                 # optional: the Hugging Face dataset that results paths are in (this is the default)
```
