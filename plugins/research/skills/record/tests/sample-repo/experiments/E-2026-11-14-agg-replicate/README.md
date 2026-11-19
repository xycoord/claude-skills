---
id: E-2026-11-14-agg-replicate
thread: readout
mode: test
status: done
date: 2026-11-14
short: the convincing-game run
question: Does the last-token advantage hold on convincing-game lies?
answer: Yes, with a smaller gap. Macro-F1 0.71 (0.69–0.73) for last-token vs 0.59 (0.57–0.61) for mean-pool. 3 seeds.
prediction:
  text: Last-token beats mean-pool by at least 0.05 macro-F1 on convincing-game.
  written: 2026-11-13
  held: true
  how: last-token beat mean-pool by 0.12 macro-F1
commit: c4f1a09
pr: 14
results: [runs/claude-agg-rep-1]
cost_usd: 2.90
rerun: uv run probes/readout_sweep.py -c configs/E-2026-11-14-agg-replicate.yaml
---

## Why we ran it

[The readout sweep](#E-2026-11-12-agg-sweep) found last-token ahead on harm-pressure lies, from one test set. A second kind of lie checks that the gap isn't a property of that one set.

## What was compared

The same three readouts as the readout sweep, on the same probe. Only the test set changes.

## Result

::fig main

## Method

The probe, readouts and thresholds of the readout sweep, unchanged, scored on the convincing-game test split (n = 860, 51% lies). 3 seeds.

## Checks

A shuffled-label probe scores 0.50 (0.48–0.52), at chance, so the probe isn't reading something the labels don't carry.

## Caveats

Convincing-game responses are shorter than harm-pressure ones, a median of 41 tokens vs 88, which leaves pooling less to dilute and may explain the smaller gap.
