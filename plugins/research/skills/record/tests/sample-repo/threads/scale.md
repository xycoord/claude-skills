---
id: scale
title: Does the layer-16 probe recipe work on Llama 3.1 70B?
findings:
  - id: F-70b-high
    status: retracted
    strength: moderate
    date: 2026-11-09
    claim: A probe detects instructed lies in Llama 3.1 70B at 0.97 AUROC.
    short: 70B probe at 0.97
    evidence:
      - { experiment: E-2026-11-03-70b-probe, role: original }
    retracted: "Train–test leak: the split put paraphrases of training items in the test set. Found 9 Nov and fixed in `7e1f0aa`; not rerun since."
next:
  - id: Q-70b-rerun
    question: With the fixed split, does the probe recipe reach 0.85 AUROC on Llama 3.1 70B?
    action: Rerun the 70B probe with the fixed split on 2 × H100.
    cost_gpu_min: 720
    state: parked
    parked: too costly at about 12 GPU-hours on 2 × H100; worth it once the 8B readout and transfer results settle
history:
  - { experiment: E-2026-11-03-70b-probe, date: 2026-11-09, line: "Retracted: train–test leak in the split." }
---
