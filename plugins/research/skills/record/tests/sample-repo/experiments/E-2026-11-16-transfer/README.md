---
id: E-2026-11-16-transfer
thread: transfer
mode: test
status: done
date: 2026-11-16
short: the transfer test
question: Does a probe trained on instructed lies detect sandbagging?
answer: No. AUROC 0.54 on sandbagging (chance 0.50) vs 0.93 on held-out instructed lies and 0.84 on harm-pressure lies. 3 seeds.
prediction:
  text: AUROC above 0.70 on sandbagging.
  written: 2026-11-15
  held: false
  how: AUROC was 0.54 on sandbagging
commit: 9d0e4f2
pr: 15
results: [runs/claude-transfer-1, runs/claude-transfer-2, runs/claude-transfer-3]
cost_usd: 1.90
rerun: uv run probes/transfer.py -c configs/E-2026-11-16-transfer.yaml
---

## Why we ran it

Every probe so far was trained and tested on lies told for the same reason. A lie detector is only useful if it catches lies it wasn't trained on, and sandbagging is the furthest from instructed lying of the sets we have.

## Result

::fig main

No probe has been trained on sandbagging, so the best reachable score on that set is unknown and the chart has no skyline.

## Method

The last-token probe from [the readout sweep](#E-2026-11-12-agg-sweep), trained only on instructed lies, is scored without retraining on three test sets. Only the test data changes.

- Held-out instructed lies, n = 600
- Harm-pressure v2, test split, n = 1,180
- Sandbagging, n = 212, where the model underperforms on purpose when told it's being evaluated

## Checks

A probe that reads only response length scores 0.57 on sandbagging, above the probe itself, so what little the probe gets there could be length.

## Caveats

The sandbagging set is small, so its 95% interval is 0.46–0.62.
