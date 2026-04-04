---
name: research-exploratory
description: >
  For open-ended research investigation and exploration. Use this skill when the task
  involves investigating a phenomenon, understanding why something happens, debugging
  unexpected model behaviour, or any research where the question is "what's going on?"
  rather than "run this experiment". This includes mechanistic interpretability investigations,
  diagnosing training anomalies, understanding failure modes, and any task that starts with
  curiosity rather than a hypothesis. Always use alongside the autonomous-execution skill.
---

# Research: Exploratory Investigation

For open-ended investigation where the goal is understanding, not a specific metric.

Before starting, read:
- `../autonomous-execution/SKILL.md` (general task discipline)
- `../research-common/references/experiment-discipline.md` (experiment rigour)

## The explore–confirm cycle

Exploratory work isn't a linear progression from "exploring" to "confirming". It's a
cycle: you explore, form a hypothesis, test it rigorously, and the results raise new
questions that send you back to exploring. A single investigation might loop through
this cycle several times, each pass deepening your understanding.

Recognise which phase you're in at any given moment, because the standards differ.

### Exploring

The goal is to form hypotheses. You're looking for patterns, anomalies, and clues.

- **Start broad, then narrow.** Begin with quick, cheap diagnostic experiments. Which
  layers matter? Which inputs trigger the behaviour? What's the simplest reproduction
  case? Cast a wide net before going deep.
- **Favour speed over rigour.** In exploration, a rough answer in 5 minutes is worth more
  than a precise one in 2 hours. Single seeds are fine. Approximate measurements are
  fine. You're building intuition, not publishing results.
- **Try multiple angles.** Don't get stuck on one approach. If looking at activations
  isn't revealing anything, try attention patterns, logit attributions, or behavioural
  probes. Different lenses often illuminate different aspects.
- **Set time boxes.** Decide upfront how long to spend on each avenue — 20-30 minutes
  is usually enough to know if something is promising. If you're not making progress,
  note what you tried in the journal and move on.

### Confirming

You have a hypothesis worth testing properly. Note the transition in the journal.

- **State the hypothesis precisely.** Not "layer 12 seems important" but "the model
  encodes the target feature primarily in layer 12 residual stream, and a linear probe
  on this layer should achieve >80% accuracy".
- **Design a proper test.** Now the standards from experiment-discipline.md apply fully:
  controls, multiple seeds, baselines. The exploration phase bought you intuition;
  the confirmation phase demands evidence.
- **Be willing to reject your hypothesis.** If the rigorous test doesn't support what
  the exploration suggested, that's a result — don't keep tweaking until it "works".
  Report what you found and consider alternative explanations.
- **Let the results guide the next cycle.** A confirmed hypothesis often raises follow-up
  questions ("it's in layer 12, but why? what mechanism?"). A rejected hypothesis
  rules out one explanation and suggests you need to explore further. Either way,
  you're back in the exploration phase with better information than before.

## Maintaining a hypothesis tracker

In the journal, keep a running section that tracks your hypotheses:

```
## Hypotheses

| # | Hypothesis | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Feature X is encoded in layer 12 | Supported | Probe accuracy 87% (3 seeds) |
| 2 | The effect disappears with shuffled inputs | Refuted | Effect persists (see journal 14:30) |
| 3 | Attention head 8.3 mediates the behaviour | Untested | |
| 4 | It's a token-frequency artefact | Unclear | Partial correlation, needs more data |
```

Update this as evidence accumulates. It prevents you from going in circles and gives
the user a quick snapshot of where the investigation stands.

## When to escalate

Exploratory work has a unique escalation case: you've found something interesting. This
isn't a blocker — you can keep working — but the user would want to know about it.

Notify the user (as a non-urgent, informational notification) when:

- You find a result that changes the story or contradicts the initial assumptions
- You discover something unexpected that might open a new research direction
- You're stuck and think a conversation about the direction would be more productive
  than more solo exploration

## Proactive continuation

Exploratory tasks are natural candidates for proactive continuation — the
explore–confirm cycle always has another iteration. If the task spec includes the
proactive-continuation skill, keep cycling after completing the specified work: use
confirmed findings to generate new questions, explore those questions, form new
hypotheses, and test them. Each cycle should be clearly labelled in the journal so
the user can see where the specified investigation ended and the proactive work began.
