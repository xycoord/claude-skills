---
name: handoff
description: >
  Write or read a handoff document for transferring work between Claude sessions.
  Use this skill when the user says they're moving to a new instance, switching pods,
  ending a session that will be continued later, or when you're starting a session and
  find a handoff.md in the task directory. Also use when the user says things like
  "wrap up for now", "I'm going to spin up a new pod", "continue from where we left off",
  or "pick up the previous work".
---

# Handoff

How to transfer context between Claude sessions when work moves to a new instance
(e.g. new RunPod pod, larger GPU, session timeout, or resuming the next day).

## Writing a handoff

When the user indicates the session is ending and work will continue elsewhere, write
a `handoff.md` in the task directory. Commit and push it.

### Before writing

Check for cached data or downloaded models that won't survive the instance change. On
RunPod, `/workspace` persists but the root filesystem doesn't.

### Structure

```markdown
# Handoff — [task name]

Written: [timestamp]
Commit: [git commit hash]

## Task
One-sentence summary. Link to the task spec.

## Current status
What's done, what's in progress, what hasn't been started. Be specific — file paths,
experiment names, which steps in the spec have been completed.

## Key files
The files the next session needs to know about — scripts, results, configs,
cached data. Brief description of each.

## Environment state
Anything non-standard: installed packages, downloaded models and where they are,
environment variables set manually, running processes.

## Decisions made
Choices that weren't in the spec — hyperparameters, architectural decisions,
workarounds. Include the reasoning so the next session doesn't re-debate them.

## Known issues
Anything broken, flaky, or concerning.

## Next steps
What the next session should do first. Be concrete.
```

### Guidelines

- **Be concrete, not vague.** "The probe training script is mostly done" is useless.
  "Probe training script at `experiments/claude/training/train_probe.py` runs
  successfully for layers 1-6, layers 7-12 haven't been started" is useful.
- **Include the journal.** If you've been maintaining a journal.md, make sure it's
  committed. Reference it in the handoff — it provides the narrative context that the
  structured summary can't capture.
- **Don't duplicate the task spec.** The handoff complements the spec, not replaces it.
  Link to the spec and describe progress against it.
- **Flag data that won't persist.** If cached results, models, or intermediate files are
  on ephemeral storage, say so explicitly and note what will need to be regenerated and
  roughly how long it will take. For smaller files (processed datasets, activations,
  configs), consider moving them to persistent storage. For large files (model weights),
  just note where to re-download them.

## Reading a handoff

When starting a session and there's a `handoff.md` in the task directory:

1. Read the handoff document first.
2. Check staleness: compare the commit hash in the handoff against the current HEAD. If
   they differ significantly, the repo may have moved on — treat the handoff as context
   but verify against the actual state of the code and results.
3. Read the task spec it references.
4. Read the journal if one exists — scan recent entries to understand the trajectory.
5. Verify the environment: check that models, data, and packages mentioned in the handoff
   are actually present. Things may have changed if the instance is different.
6. Pick up from the "next steps" section, adjusting if the environment has changed.

If the handoff is unclear or seems stale, note what's ambiguous in the journal and
proceed with your best understanding. Don't wait for the user to clarify unless you
genuinely can't determine what to do next.
