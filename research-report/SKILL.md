---
name: research-report
description: >
  Generate well-structured research experiment reports as Markdown files with matplotlib plots saved as PNGs.
  Use this skill whenever the user asks you to write up results, summarise an experiment, create a report
  from experimental data, produce findings, or document research outcomes — even if they don't say "report"
  explicitly. Also trigger when the user says things like "plot the results", "write up what we found",
  "summarise these runs", "make a report for my supervisor", or "document this experiment". This skill
  covers ML/AI safety research reports with comparisons against baselines, training curves, and evaluation
  metrics. If the task involves presenting experimental results in any written form, use this skill.
---

# Research Report Skill

Generate clear, well-structured experiment reports as Markdown with embedded matplotlib plots (saved as PNGs). The reports are designed to be viewed directly on GitHub.

## When to read the references

Before generating any plots, read `../plot/references/plotting.md` (the shared plotting conventions). It contains detailed conventions for colours, layout, bar charts, heatmaps, baselines, and error bars. Following these conventions is essential to producing consistent, readable figures.

## Repo structure context

Reports are generated within a standard Python research project. Here's the general layout:

```
project/
├── src/                       # Core library code
├── scripts/                   # Shared utility scripts
├── experiments/
│   ├── claude/                # One folder per team member
│   │   ├── training/          # Experiment scripts, organised by function
│   │   ├── eval/
│   │   ├── analysis/
│   │   └── reports/           # ← Reports go here
│   ├── alice/
│   └── ...
└── tasks/
    ├── current_task.md        # Task specs for Claude
    └── done/                  # Completed task specs
```

Each user's `reports/` folder contains their reports and a shared `figures/` directory:

```
experiments/claude/reports/
├── figures/
│   ├── reward_model_comparison/
│   │   ├── auc_bar.png
│   │   └── confusion_matrix.png
│   └── probe_analysis/
│       └── layer_heatmap.png
├── reward_model_comparison_report.md
└── probe_analysis_report.md
```

Key points to understand about this layout:

- **Experiment scripts** live under `experiments/<user>/` and are organised by function (training, eval, analysis). They're lightweight — mostly config and orchestration rather than heavy logic.
- **A single report may draw on multiple experiment scripts** — e.g. a training run from `experiments/claude/training/` and an evaluation from `experiments/claude/eval/`, plus baseline results from a previous experiment.
- **Task specs** are markdown files in `tasks/`, moved to `tasks/done/` when completed. They define what Claude should do but are separate from the report.

## Report file conventions

**Report location:** `experiments/<user>/reports/<report_name>.md`

**Report naming:** Derive the report name from the task spec where possible. If the task was `tasks/reward_model_comparison.md`, name the report `reward_model_comparison_report.md`. If there's no task spec (e.g. ad-hoc analysis), use a descriptive snake_case name.

**Figures location:** `experiments/<user>/reports/figures/`. This is a shared folder for all reports under that user. Use clear, descriptive filenames that won't collide across reports — either use a subfolder per report (e.g. `figures/reward_model_comparison/auc_bar.png`) or prefix filenames (e.g. `figures/reward_model_comparison_auc_bar.png`). For a one-off report a flat name like `figures/auc_bar.png` is fine; for a user with many reports, namespacing avoids confusion. Use judgement.

**Image references in markdown:** Use relative paths from the report file:

```markdown
![AUC-ROC by method](figures/reward_model_comparison/auc_bar.png)
```

**Task spec linking:** Include a link to the task spec at the top of the report (just after the title or in the experiment setup) so a reader can trace the intent, but write the report to be fully self-contained — it should make sense without reading the spec. For example:

```markdown
> Task spec: [`tasks/done/reward_model_comparison.md`](../../tasks/done/reward_model_comparison.md)
```

**Cross-referencing experiment scripts:** When describing methodology, link to the relevant experiment scripts so a reader can find the code:

```markdown
Training script: [`experiments/claude/training/reward_model.py`](../training/reward_model.py)
```

## Report structure

A report may cover one or several experiments. The key principle is that each experiment is self-contained: its setup and results live together so the reader can follow one experiment without jumping around. Adapt section depth and length to scale — a small ablation needs only a few sentences per section.

### Single-experiment report

```
# [Descriptive report title]

## ⚠️ Flags                          ← only if there are warnings
## Summary
## Experiment: [Name]
  ### Setup
  <details><summary>Full methodology</summary>...</details>
  ### Results
  ### Discussion
## Reproducibility
```

### Multi-experiment report

```
# [Descriptive report title]

## ⚠️ Flags                          ← only if there are warnings
## Summary
## Methods                            ← shared method descriptions, if applicable
## Experiment 1: [Name]
  ### Setup
  <details><summary>Full methodology</summary>...</details>
  ### Results
  ### Discussion
## Experiment 2: [Name]
  ### Setup
  <details><summary>Full methodology</summary>...</details>
  ### Results
  ### Discussion
## Overall discussion                 ← cross-experiment synthesis, if warranted
## Reproducibility
```

### Flags

If there are any warnings that the reader should know about before diving in — missing baselines, failed runs, caveats about data quality, experiments that didn't complete — collect them at the very top of the report under a `## ⚠️ Flags` section. Each flag should be a single clear sentence. For example:

```markdown
## ⚠️ Flags
- **Missing baseline:** No SFT baseline results available for Experiment 2. These should be run before drawing conclusions.
- **Incomplete run:** Experiment 3 training was stopped at 80% due to compute limits. Results are provisional.
```

If there are no flags, omit this section entirely.

### Summary

A short paragraph (3–6 sentences) covering the report as a whole: what experiments were run, what the headline findings are, and why they matter. Lead with the most important result. If a result is negative or inconclusive, say so plainly — don't bury it.

For multi-experiment reports, this is a high-level synthesis, not a per-experiment recap. Each experiment's own section covers its details.

### Methods (multi-experiment reports)

When multiple experiments compare the same methods, describe those methods once in a shared section before the experiment sections rather than repeating them in each experiment's setup. Give a brief description of each method — enough for a collaborator to understand what it is and how it differs from the others. Method abbreviations (see "Method naming" below) can also be defined here.

If an experiment introduces methods not used elsewhere, describe those in that experiment's own setup instead.

For single-experiment reports, this section is unnecessary — describe the methods in the experiment's setup directly.

### Per-experiment sections

Each experiment gets its own section containing setup, results, and discussion grouped together.

#### Setup (visible)

A brief, high-level description (roughly a paragraph) that gives enough context for anyone working on the same project to follow, even if they didn't specify this experiment. Cover:

- What question this experiment answers
- Which methods are being compared (reference the shared Methods section if they're described there, rather than re-describing them)
- Dataset(s) and key conditions
- Any methods unique to this experiment (describe these here)

This should be self-contained and readable at a glance. Don't reference the task specification — write as if the reader hasn't seen it.

#### Full methodology (collapsible)

Immediately after the brief setup, include the complete methodology inside a GitHub-compatible collapsible block:

```markdown
<details>
<summary>Full methodology</summary>

[Detailed description here]

</details>
```

This serves two purposes: (1) verifying that Claude carried out the experiment as intended, and (2) providing enough detail to write up the experiment for a paper or to specify follow-up tasks. It should cover:

- Precise model/method descriptions and how they differ
- Dataset details: size, splits, any filtering or preprocessing
- Hyperparameters and how they were chosen (grid search, defaults, etc.)
- Training details: epochs, batch size, optimiser, learning rate schedule
- Evaluation protocol: what metrics, how computed, how many seeds/folds
- Anything that deviates from project defaults

Write this as clear technical prose, not a raw config dump. Link to experiment scripts and config files in the repo where relevant (e.g. "Full config: [`experiments/claude/training/configs/reward_model.yaml`](../training/configs/reward_model.yaml)").

#### Results

The core of each experiment section. Interleave plots with short interpretive text. Each plot or table should be introduced with a sentence saying what to look at, and followed by a sentence or two on what it shows. Don't just dump figures — guide the reader.

For each key metric:
- Present a plot (see plotting conventions below)
- State the main result in words, including actual numbers
- Note anything surprising or worth investigating further

If there are many metrics or conditions, group them logically (e.g. by task, by metric type) using subheadings.

#### Discussion

Interpret this experiment's results honestly. Address whether the hypothesis was supported, unexpected findings, limitations, and concrete next steps. Keep this concise and specific to the experiment.

### Overall discussion (multi-experiment reports)

If the report contains multiple experiments, an overall discussion section after all experiment sections can synthesise cross-experiment themes: patterns across experiments, how findings from one experiment inform interpretation of another, and what the combined results suggest for the research direction. Only include this if there's genuine cross-experiment insight — don't add it just for completeness.

### Reproducibility

A brief pointer to where the reader can find everything needed to rerun the experiments. Link to the actual experiment scripts and any relevant config. For example:

```markdown
**Experiment 1 (reward model training):**
- Script: [`experiments/claude/training/reward_model.py`](../training/reward_model.py)
- Config: [`experiments/claude/training/configs/reward_model.yaml`](../training/configs/reward_model.yaml)

**Experiment 2 (evaluation):**
- Script: [`experiments/claude/eval/reward_model_eval.py`](../eval/reward_model_eval.py)

**Task spec:** [`tasks/done/reward_model_comparison.md`](../../tasks/done/reward_model_comparison.md)
```

Don't duplicate information that lives elsewhere in the repo — just link to it.

## Method naming

Define a canonical name for each method at the start of report generation and use it identically in every plot, table, and text reference throughout the report. If the full name is too long for axis labels, define a clear abbreviation and include a legend — in multi-experiment reports this fits naturally in the shared Methods section; in single-experiment reports, place it near the first plot or in the experiment setup. For example:

> **Abbreviations:** RL-KL = RLHF with KL penalty, SFT-base = supervised fine-tuning baseline, Rand = random classifier skyline.

## Baselines are critical

Every comparison plot must include relevant baselines. If baseline results are available, always plot them. If baselines are applicable but results are not available, add an entry to the **Flags** section at the top of the report (e.g. "Missing baseline: No SFT results for Experiment 2"). Never present results for new methods in isolation when a baseline comparison would be informative.

## Plotting conventions

The detailed plotting reference is in `../plot/references/plotting.md` — read it before generating any figures. Here's a summary of the key principles:

- Save all figures as PNG at 150 DPI minimum, at least 8×5 inches
- Use a consistent colour palette throughout the report: one colour group for skylines, one for baselines, one for new methods
- Bar order is always: skylines (if applicable) → baselines → new methods
- Baselines get both a bar and a horizontal dashed line for easy comparison
- Meaningful metric bounds should be reflected in the axis range (e.g. AUC plots span 0–1)
- Meaningful reference values (e.g. random = 0.5 for AUC) should be plotted as labelled horizontal lines
- Annotate bars with their actual values
- Include error bars where applicable, with a note on what they represent (e.g. ±1 std over 3 seeds)
- Remove top and right spines on bar charts
- Place legends outside the plot area
- Horizontal reference lines should be drawn behind bars (low zorder)
- Use subtle grid lines on the value axis

## Writing tone

Write for a technical collaborator who has context on the broader project but hasn't seen this specific experiment's results. Be direct and concise. State findings plainly — if something didn't work, say so. Avoid filler phrases ("it is interesting to note that...") and hedging where the data is clear. Use prose paragraphs rather than bullet-point lists for the narrative sections (summary, discussion), but tables and structured comparisons are fine in the results section.

## Mathematical notation

GitHub renders LaTeX maths natively via MathJax. Use it wherever mathematical precision helps — don't describe formulae in words when notation is clearer. Common places where LaTeX adds value:

- **Loss functions and objectives** — e.g. defining the reward model loss or KL penalty term in the methodology
- **Metric definitions** — especially non-obvious ones; if you're reporting a metric that a collaborator might not know offhand, define it
- **Thresholds and decision rules** — e.g. "we flag a sample when $p(\text{harmful}) > 0.8$"
- **Mathematical relationships** — anything involving summations, expectations, fractions, etc. that would be awkward in plain text

Use `$...$` for inline maths and a fenced code block with `math` for display equations:

````markdown
The KL-penalised reward objective is:

```math
\mathcal{L} = \mathbb{E}_{x \sim D}\left[ r(x) - \beta \, \text{KL}\left(\pi_\theta \| \pi_{\text{ref}}\right) \right]
```
````

Keep it pragmatic — a simple ratio or percentage doesn't need LaTeX, but anything with subscripts, Greek letters, summations, or fractions should use it. If a formula is central to the experiment (e.g. the training objective), place it in the methodology. If it's a metric definition, place it near the first plot that uses that metric.
