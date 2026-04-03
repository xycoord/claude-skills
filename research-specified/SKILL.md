---
name: research-specified
description: >
  For executing well-defined research experiments specified in a task spec. Use this skill
  when the task spec defines exactly what experiments to run — hyperparameter sweeps, probe
  training on specific layers, activation collection, evaluation on specific benchmarks, or
  any research task where the experimental design is already determined. The user has decided
  what to do; your job is to execute it correctly, efficiently, and thoroughly.
  Always use alongside the autonomous-execution skill.
---

# Research: Specified Experiments

For tasks where the experiment design is already defined. The task spec tells you what
to run — your job is execution, not design.

Before starting, read:
- `../autonomous-execution/SKILL.md` (general task discipline)
- `../research-common/references/experiment-discipline.md` (experiment rigour)

## Your role

The value you add here is in efficiency, correctness, and thoroughness — not creativity.
Get the runs done cleanly, save results properly, report clearly.

- **Follow the spec precisely.** If it says "train probes on layers 1, 6, 12, 24", do
  exactly that. Don't add layers because you think they'd be interesting.
- **If you spot an issue with the spec, ask.** A hyperparameter that seems wrong, a
  missing baseline that would be easy to add, an ambiguity in the instructions — note
  it in the journal and notify the user. Don't silently "improve" the spec.
- **Flag unclear or missing metrics early.** Metrics determine what you can learn from
  an experiment. If the spec doesn't define metrics, or the specified metrics might not
  capture what matters, raise this with the user in the first-minutes phase. Some metrics
  can be computed post-hoc from saved results, but others require specific data to be
  collected during the run — better to clarify upfront.
- **Front-load validation.** Before running the full set of experiments, verify your setup
  with one quick run. Catch shape mismatches, data loading issues, and configuration
  errors before committing to the full sweep.

## Execution order

1. Read the full task spec. Identify all experiments, their dependencies, and what outputs
   are expected.
2. Check prerequisites (data, models, tokens, disk space) — see autonomous-execution.
3. Set up shared infrastructure (data loading, evaluation functions, plotting utilities)
   before running any experiments. This ensures consistency and avoids duplication.
4. Run experiments in a logical order. If later experiments depend on earlier results,
   respect the dependency. If they're independent, consider running them in parallel.
5. Save results incrementally — after each experiment, not all at the end.
6. Generate plots and write up results as specified.

## When the spec is ambiguous

Sometimes a spec is mostly well-defined but leaves some details unspecified (batch size,
learning rate, number of epochs). In these cases:

- Use sensible defaults and document what you chose in the journal.
- If a choice could meaningfully affect results, ask rather than guess.
- If the spec says "evaluate on the test set" but doesn't specify a metric, ask — don't
  assume.
