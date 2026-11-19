---
id: E-2026-11-18-false-alarms
thread: transfer
mode: explore
status: done
date: 2026-11-18
short: the false-alarm look
question: What do the honest answers the probe flags as lies have in common?
answer: Gathered the 212 honest answers the last-token probe flagged, out of 5,300, with each token's score. Two things stood out, both candidates rather than findings. Most false alarms are refusals, and their scores peak in the first sentence rather than at the end.
commit: 0c3d9b7
results: [runs/claude-false-alarms-1]
cost_usd: 0.40
rerun: uv run probes/false_alarms.py -c configs/E-2026-11-18-false-alarms.yaml
---

## Why we looked

The last-token probe flags 4% of honest answers as lies. Before trusting it on new sets, it's worth knowing whether those false alarms are random or share something the probe is reacting to.

## The data

::fig slices

::fig scores

::fig items

## Patterns

### Most false alarms are refusals

61% of false alarms are refusals, vs 12% of all honest answers.

- **Where to see it:** the refusal row of the slice chart, and the items table, where 7 of the 8 highest-scoring rows refuse.
- **How it was found:** 9 attributes were sliced, and this was the largest difference.
- **A cheap noise test:** it holds in each of 3 seeds, and in a held-out half of the honest answers, at 58% refusals.
- **What counts against it:** 39 of the false alarms are ordinary helpful answers with no refusal, and their scores look no different.

### Scores peak early in refusals

::fig refusal-tokens

In refusals that are flagged, the per-token score is highest in the first sentence and falls by the end, the reverse of a typical lie.

- **Where to see it:** the token view of a flagged refusal, and the layer-by-token view below.
- **How it was found:** looked for after the first pattern, in the 129 flagged refusals only.
- **A cheap noise test:** not run; the same view on unflagged refusals would show whether every refusal starts high.
- **What counts against it:** the last-token readout reads the final token, so an early peak shouldn't by itself raise the readout's score.

::fig by-layer

## Looked at and found nothing

Response length, the system prompt and the answer's position in the conversation were each sliced into quartiles, and none showed a difference in the false-alarm rate larger than 1.2 points.

## Method

The last-token probe at layer 16 from [the readout sweep](#E-2026-11-12-agg-sweep), seed 0, scored every honest answer in the instructed-lies and harm-pressure v2 pools, 5,300 in all, at its usual threshold of 0.46. Each flagged answer was labelled by topic, refusal, length, system prompt and position, by a fixed rubric and Claude, with 50 checked by hand (49 agreed).
