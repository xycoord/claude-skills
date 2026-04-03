# Experiment Discipline

Common practices for running rigorous experiments. Referenced by all research skills.

## Before running anything

- **State your hypothesis.** Before every experiment, write down what you expect to happen
  and why in the journal. Without it, you'll rationalise any result after the fact.
- **Establish baselines.** Baselines are essential for interpreting results — without a
  comparison point, numbers are meaningless. Check whether relevant baselines already
  exist in the repo from previous experiments. If they don't exist and haven't been
  specified in the task, flag this to the user immediately (in the first-minutes phase)
  rather than running experiments you can't properly interpret. Baselines include both
  standard methods to compare against (e.g. the existing approach) and sanity-check
  controls (e.g. random labels, shuffled inputs) that verify your setup is valid.
- **Smoke test on small data.** Run the full pipeline on a tiny subset before launching
  the real thing. Check that outputs have the right shape, values are in a reasonable
  range, and nothing crashes.

## Design

- **Change one thing at a time.** If you're investigating a phenomenon, vary one factor
  per experiment. If you change the model, the dataset, and the method simultaneously,
  you can't attribute the result to any of them.
- **Always set a seed.** Every experiment must use an explicit random seed for
  reproducibility. How many distinct seeds to run depends on context: for long
  experiments, exploration phases, or cases where variance is inherently low (e.g.
  convex optimisation), a single seed is fine. For shorter runs where stochasticity
  could affect conclusions, use 3 seeds and report mean ± std. When in doubt, start
  with 1 seed to validate the pipeline, then add seeds to robustify findings that
  matter.

## During experiments

- **Save metrics programmatically.** Experiment scripts should write metrics to files
  (CSV, JSON, or similar) — don't rely on terminal output. This ensures results survive
  regardless of session state, enables automated comparison across runs, and feeds
  directly into plotting and reporting.
- **Compare against your hypothesis.** After each result, explicitly note in the journal
  whether it matched your expectation. "Expected probe accuracy ~85%, got 62%" is far
  more useful than just "probe accuracy: 62%".
- **Flag surprises, don't explain them away.** If a result is unexpected, resist the urge
  to immediately rationalise it and move on. Note the surprise in the journal and
  consider: is this a bug, a genuine finding, or a sign that your setup is wrong?
  If you're unsure, run a quick sanity check before proceeding.
- **Don't cherry-pick.** Report all results, including the ones that didn't work or
  don't support the hypothesis. Negative results are informative and the user needs
  to see them.
