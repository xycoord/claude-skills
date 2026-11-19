---
id: readout
title: Which token should a lie probe on Llama 3.1 8B read?
findings:
  - id: F-last-token
    status: current
    strength: strong
    date: 2026-11-14
    claim: On harm-pressure and convincing-game lies, last-token readout beats mean-pool, at 0.79 vs 0.58 and 0.71 vs 0.59 macro-F1.
    short: Last-token beats pooling
    method: A linear probe at layer 16, trained on instructed lies and tested on two other kinds of lie. Three readouts of its per-token scores are compared, each with its own threshold set on the instructed-lies dev split, over 3 seeds.
    evidence:
      - { experiment: E-2026-11-12-agg-sweep, role: original }
      - { experiment: E-2026-11-14-agg-replicate, role: replication on convincing-game }
    figure: E-2026-11-12-agg-sweep/main
    confidence: Strong, because 3 seeds agree on both sets, the gap is larger than the seed range on each, and a shuffled-label probe scores 0.50. It isn't higher because it rests on one model.
    caveats: One model so far. The gap is smaller on convincing-game (0.12 vs 0.21 macro-F1), and responses there are shorter.
    implication: Last-token has been the default readout since 14 Nov. One reading is that the lie is settled near the end of a response and pooling dilutes it, which is untested.
  - id: F-last-token-hp
    status: superseded
    strength: moderate
    date: 2026-11-14
    claim: On harm-pressure lies, last-token readout reaches 0.79 macro-F1 vs 0.58 for mean-pool.
    short: Last-token beats pooling on harm-pressure
    evidence:
      - { experiment: E-2026-11-12-agg-sweep, role: original }
    replaced_by: F-last-token
next:
  - id: Q-other-family
    question: Does the last-token advantage hold on another model family?
    action: Run the readout comparison on Qwen 2.5 7B.
    cost_gpu_min: 50
    state: running
    experiment: E-2026-11-17-qwen-agg
    settles: No gap there would narrow the finding to Llama.
  - id: Q-length-matched
    question: Does last-token still lead when lies and honest answers are matched for length?
    action: Rescore the readout sweep's test set on 400 length-matched pairs; no new training needed.
    cost_gpu_min: 15
    settles: A gap under 0.05 would mean length explains most of it.
history:
  - { experiment: E-2026-11-12-agg-sweep, date: 2026-11-12, line: "New finding, moderate: last-token beats pooling on harm-pressure." }
  - { experiment: E-2026-11-14-agg-replicate, date: 2026-11-14, line: "Raised to strong. Last-token became the default readout." }
---

Notes: the length-matched rescore is cheap, so run it before the next model family if Qwen stalls.
