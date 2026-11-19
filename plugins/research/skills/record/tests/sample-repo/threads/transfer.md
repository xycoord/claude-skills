---
id: transfer
title: Does a probe trained on instructed lies catch other kinds of lie?
findings:
  - id: F-no-transfer
    status: current
    strength: moderate
    date: 2026-11-16
    claim: Trained only on instructed lies, the last-token probe scores near chance on sandbagging, at 0.54 AUROC vs 0.50 for chance.
    short: No transfer to sandbagging
    method: The last-token probe at layer 16, trained only on instructed lies, is scored without retraining on held-out instructed lies, harm-pressure v2 and sandbagging. 3 seeds.
    evidence:
      - { experiment: E-2026-11-16-transfer, role: original }
    figure: E-2026-11-16-transfer/main
    confidence: Moderate, because 3 seeds agree and the same probe reaches 0.93 on held-out instructed lies, so the probe itself works. It isn't strong because the sandbagging set is small and there's only one of it.
    caveats: The sandbagging set has 212 items, so its 95% interval is 0.46–0.62. No probe has been trained on sandbagging, so there's no skyline for it.
    implication: The probe isn't a general lie detector, so it shouldn't be used to flag sandbagging. Whether a mix of training sets fixes that is the next question.
next:
  - id: Q-mix-sandbag
    question: Does a probe trained on a mix of lie types detect sandbagging?
    action: Retrain on instructed plus harm-pressure lies, then test on sandbagging.
    cost_gpu_min: 30
    settles: Above 0.70 AUROC would mean the gap is about training data rather than the probe.
  - id: Q-refusal-matched
    question: Does the probe score refusals higher than other honest answers when topic is matched?
    action: Score 500 refusals and 500 topic-matched helpful answers.
    cost_gpu_min: 10
    lead: true
    from: E-2026-11-18-false-alarms
  - id: Q-second-sandbag
    question: Does the near-chance result hold on a second sandbagging set?
    action: Find or build a second sandbagging set; none found yet.
history:
  - { experiment: E-2026-11-16-transfer, date: 2026-11-16, line: "New finding, moderate: no transfer to sandbagging." }
---
