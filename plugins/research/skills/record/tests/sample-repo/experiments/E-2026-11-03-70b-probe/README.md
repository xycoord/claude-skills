---
id: E-2026-11-03-70b-probe
thread: scale
mode: test
status: retracted
date: 2026-11-03
short: the 70B probe
question: Does the 8B probe recipe work on Llama 3.1 70B?
answer: Retracted. The 0.97 AUROC came from a train–test leak in the split.
commit: 2f8e6a4
results: [runs/claude-70b-probe-1]
cost_usd: 11.20
rerun: uv run probes/probe.py -c configs/E-2026-11-03-70b-probe.yaml
---

## Why we ran it

The 8B probe worked, and a larger model is the obvious next test of whether the recipe is general.

## Method

The 8B recipe on Llama 3.1 70B at layer 40, the same relative depth, trained and tested on instructed lies. 1 seed.

## Caveats

The split was built by prompt template, not by prompt, so paraphrases of training prompts reached the test split.
