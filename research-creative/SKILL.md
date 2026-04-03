---
name: research-creative
description: >
  For goal-directed research tasks with creative freedom. Use this skill when the task spec
  defines a goal and evaluation metric but gives latitude on how to achieve it — e.g. "train
  the best probe you can", "find a good architecture for this task", "maximise this metric
  using whatever approach you think works". The user has defined success; your job is to
  find the best path to it. Always use alongside the autonomous-execution skill.
---

# Research: Creative / Goal-Directed

For tasks where the goal is defined but the path is up to you. You have a metric to
optimise and freedom to experiment with how to get there.

Before starting, read:
- `../autonomous-execution/SKILL.md` (general task discipline)
- `../research-common/references/experiment-discipline.md` (experiment rigour)

## Your approach

### Understand the problem first

Before jumping to solutions, spend time understanding what you're working with. Look at
the datasets — their distributions, edge cases, class balance, examples that seem hard.
Check what the model actually produces on representative inputs. This kind of exploratory
groundwork often reveals what the real challenges are and saves you from optimising in
the wrong direction.

### Start simple

Don't jump to novel ideas before establishing what a straightforward approach achieves.
Train the obvious baseline first — the simplest architecture, the default hyperparameters,
the standard preprocessing. This gives you a reference point and often reveals what
aspects of the problem are hard.

### Iterate methodically

Each iteration should change one thing and measure its effect. Log every attempt and its
result in the journal, including things that didn't work. The journal should read as a
coherent narrative of your search, not just a list of results.

A useful journal pattern for creative work:

```
## HH:MM — Trying X

Rationale: I think X might help because...
Expected effect: should improve metric by roughly...
Result: metric went from A to B.
Interpretation: this suggests... Next I'll try...
```

For systematic hyperparameter sweeps or tuning, consider using wandb (Weights & Biases)
to track runs and visualise results. It's particularly useful when exploring large
parameter spaces.

### Be genuinely creative

You have license to try unconventional approaches. Use it. Some ideas to consider:

- Different architectures beyond the obvious (e.g. if the spec says "train a probe",
  that doesn't mean it has to be a linear probe — try MLPs, different depths, skip
  connections)
- Preprocessing and data augmentation tricks
- Non-standard training schedules (warmup, cyclical LR, early stopping criteria)
- Ensembling or combining approaches
- Drawing on techniques from adjacent areas

But always compare back to your current best. Novelty without improvement is just noise.

### Give novel methods a fair shot

When trying a new approach, don't give up after a single run with default hyperparameters
— novel methods often need different tuning than established ones. But be pragmatic: if
an approach isn't showing any promise after reasonable effort, move on rather than
over-optimising a dud.

When a method you expected to work doesn't, pay attention to why. If it's surprising —
something that should have worked in theory — that's worth investigating and noting in
the journal, as it might reveal something about the problem. If it's unsurprising —
a long shot that didn't pay off — note the result briefly and move on.

### Avoid metric hacking

When optimising a metric, it's tempting to find approaches that improve the number
without actually solving the underlying problem. Watch out for two common failure modes:

- **Train/test leakage.** If you're improving training data or methods to score better
  on a test set, be very careful that knowledge of the test set isn't leaking into your
  training process. Curating training data to "cover" test set patterns is a subtle
  form of this.
- **Impractical methods.** An approach that scores well but couldn't realistically be
  deployed is rarely useful. For example, a method that requires running two models
  simultaneously when only one would be available in practice, or a technique that
  needs information that wouldn't exist at inference time. Apply common sense: would
  a researcher look at this method and say "that's clever" or "that's cheating"?

Completely avoiding these pitfalls requires deep domain understanding, but thinking
critically about whether your improvements reflect genuine progress goes a long way.

### Know when to stop

Diminishing returns are real. Track your progress:

- If your last 3 attempts haven't improved on the best result, step back and consider
  whether you need a fundamentally different approach or whether you've found a
  reasonable optimum.
- If you've been working on incremental improvements for a while, try one bold experiment
  — something that might fail but could also break through a plateau.
- Document your best result clearly so it's easy to find among all the iterations.

### Keep the best result reproducible

As you iterate, maintain a clear record of what your best-performing configuration is:
the exact hyperparameters, the code version, the data split. The user should be able to
reproduce your best result from what's in the repo.
