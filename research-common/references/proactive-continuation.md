# Proactive Continuation

When you finish the specified work and the user isn't available to respond (e.g. they're
asleep, away from their computer, or otherwise occupied), compute resources are sitting
idle. Rather than waiting, use the remaining time productively. This guidance covers how
to do that safely.

Only applies when the task spec explicitly enables proactive continuation or the user
has indicated they'll be away.

## Prerequisites

Before doing any proactive work:

1. The primary task is fully complete — results saved, plots generated, report written.
2. Everything is committed and pushed.
3. The user has been notified that the specified work is done.

## What to work on

Look at your results and journal for loose ends:

- A surprising result worth investigating further
- An ablation that would strengthen a finding
- A follow-up experiment that's a natural next step
- A variation the user mentioned as interesting but didn't include in the spec
- Improving efficiency of existing code for future use

Prioritise work that would be most useful to the user. Quick wins and high-information
experiments first.

## How to work on it

- **Keep it low-risk.** Don't make changes that could break or invalidate the primary
  results. Work in new scripts and save to new output files. The original results
  must remain intact.
- **Journal everything.** Proactive work needs more documentation, not less, because the
  user didn't specify it. Make it easy for them to see what you did and why when they
  come back.
- **Commit and push regularly.** The user may check in on progress remotely. Make sure
  your latest work and journal are always pushed.
- **Label it clearly.** In the journal and in commit messages, make it obvious which work
  was proactive vs. specified. The user needs to distinguish "I asked for this" from
  "Claude thought this would be useful".
- **Write up as you go.** Don't leave a pile of uninterpreted results. For each proactive
  experiment, add a brief write-up to the journal or report with what you tried and
  what you found.
