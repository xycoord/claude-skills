---
name: task-discussion
description: >
  Have a structured discussion to collaboratively write a task spec before any work begins.
  Use this skill when the user wants to discuss, plan, or scope a task before executing it.
  Triggers include: "let's discuss this task", "help me write a task spec", "I want to talk
  through what I need", "let's plan this out", "before you start, let's discuss", or any
  indication that the user wants to have a conversation about what to do rather than have
  you do it. Also triggers on /task-discussion. IMPORTANT: this skill is for discussion
  only — do not start executing the task.
---

# Task Discussion

A structured conversation to produce a clear, unambiguous task spec. Your role is to
help the user think through what they want, anticipate problems, and write it down
precisely enough that a Claude session can execute it autonomously.

**Do not start working on the task itself.** This skill is purely for discussion and
spec writing.

Before starting the discussion, read the skills that will be relevant to the task.
In particular, read `../autonomous-execution/SKILL.md` and whichever research skill
applies (specified, creative, or exploratory). Understanding what those skills already
cover will help you write a spec that complements them rather than repeating them.

The user will typically provide an initial description of the task to kick things off.
Use this as a starting point — it will capture their intent but likely have gaps,
ambiguities, or suboptimal approaches. Your job is to fill those gaps through
conversation.

## Start by understanding the codebase

Before asking the user questions, explore the repo to build context:

- Read the project structure (key directories, src layout, existing experiments)
- Check what models, datasets, and utilities are already available
- Look at previous task specs in `tasks/` and `tasks/done/` to understand conventions
  and what's been done before
- Check existing results and reports to understand where the research is at

This means you can ask informed questions rather than generic ones, and you can
spot when the user's plan conflicts with or duplicates existing work.

## Your role in the discussion

You're not just a scribe — you're a collaborator. This means:

- **Challenge bad ideas.** If the user's proposed approach is suboptimal and there's a
  more standard or efficient way, say so. Explain why and suggest the alternative. Don't
  silently accept an approach you think is wrong.
- **Anticipate problems.** Think about what could go wrong: resource constraints, edge
  cases, missing dependencies, experiments that might not be informative. Raise these
  early so the spec can account for them.
- **Make suggestions.** If you see an opportunity the user hasn't mentioned — a useful
  ablation, a relevant baseline, an existing utility that would save time — bring it up.
- **Ask about things the user might not have considered.** What happens if an experiment
  fails? What if results are inconclusive? What if the model doesn't fit in memory?
  These fallback scenarios should be in the spec.

Have a natural conversation. Use your judgement on format — sometimes a focused checklist
is the most efficient way to cover practical details, other times a conversational
back-and-forth is better for working through design questions.

## Areas to cover

Not every task needs all of these. Use judgement about what's relevant.

- **Goal and motivation.** What are we trying to achieve and why? Understanding the
  motivation helps make better decisions about scope and trade-offs.
- **Scope.** What specifically should be done? What should explicitly *not* be done?
  For large tasks, what are the phases or stages?
- **Approach.** Are there existing utilities or scripts to reuse? Known approaches to
  build on? Prior work in the repo? Is the user's suggested approach the best one?
- **Metrics.** What should be measured? This is worth discussing carefully — metrics
  determine what you can learn. Are there metrics that can be computed post-hoc vs.
  ones needing specific data collection during the run?
- **Baselines.** What to compare against? Do they already exist in the repo?
- **Practicalities.** Hardware constraints, time budget, dependencies, known gotchas.
- **Failure modes.** What should Claude do if something goes wrong? Notify, retry,
  skip, use a fallback?
- **Task type.** Specified experiments, creative/goal-directed, or exploratory? This
  determines which research skill to reference.
- **On completion.** Report? Plots? Proactive continuation if finished early?

## Writing the spec

Once the discussion has converged, draft the task spec as a markdown file and save it
to the tasks directory. Tell the user where it is so they can review it in their
preferred editor. Don't commit until they've approved it.

Large tasks may include multiple phases or many experiments — structure the spec to
reflect this, with clear ordering where it matters and explicit notes on what can
run in parallel.

The spec doesn't need to repeat guidance that's already in the skills it references.
For example, don't restate the journaling conventions or caching strategy — just
reference the relevant skills. The spec should focus on what's specific to this task.

### Structure

```markdown
# [Task title]

## Goal
What this task aims to achieve and why.

## Skills
Which skills to use (e.g. autonomous-execution, research-specified, research-report).

## Experiments / Work items
Concrete description of what to do. For multi-phase tasks, organise into phases with
clear dependencies between them.

## Metrics
What to measure and how.

## Baselines
What to compare against and where to find existing baseline results.

## Constraints
Hardware, time, scope boundaries, things to avoid.

## Failure modes
What to do when things go wrong — for each likely failure, a concrete instruction.

## On completion
What to produce (report, plots, saved results) and whether to continue proactively.
```

Adapt this structure to the task — not every section is always needed. A simple
data collection task might just need goal, work items, and constraints.

### Good spec writing

- **Be specific enough to execute but not so detailed you're writing the code.** "Train
  linear probes on layers 1, 6, 12, 24 of GPT-2 small using the TruthfulQA dataset"
  is good. Pseudocode for the training loop is too much.
- **State what, not how.** Unless the how matters (a specific algorithm, a particular
  library), leave implementation choices to the executing session.
- **Make the implicit explicit.** If you mean "use the default train/test split", say so.
  If you mean "3 seeds", say so. The executing Claude will make reasonable defaults but
  they might not be your defaults.
- **Include fallback instructions.** "If the model doesn't fit in bf16, notify me rather
  than quantising" is much better than leaving Claude to guess.
