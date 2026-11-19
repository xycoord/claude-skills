---
id: E-2026-11-17-qwen-agg
thread: readout
mode: test
status: running
date: 2026-11-17
short: the Qwen comparison
question: Does the last-token advantage hold on Qwen 2.5 7B?
prediction:
  text: Last-token beats mean-pool by at least 0.1 macro-F1 on harm-pressure v2.
  written: 2026-11-17
commit: 5b7a1c0
results: [runs/claude-qwen-agg-1]
rerun: uv run probes/readout_sweep.py -c configs/E-2026-11-17-qwen-agg.yaml
---

## Why we ran it

Every readout result so far comes from Llama 3.1 8B. If the advantage comes from how Llama places its decision late in a response, another model family might not show it.

## What was compared

The three readouts of [the readout sweep](#E-2026-11-12-agg-sweep), on Qwen 2.5 7B Instruct.

## Method

The readout sweep's recipe at Qwen's layer 14, the same relative depth as Llama's layer 16. Trained on instructed lies, tested on harm-pressure v2. 3 seeds.
