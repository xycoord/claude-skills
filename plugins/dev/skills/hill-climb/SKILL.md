---
name: hill-climb
description: Improve something round by round against a fixed measure until it reaches a target — a judged one (a /council scoring screenshots of a page) or an objective one (load time, bundle size, query time). One hill or several at once (three pages). Use when someone asks for a hill climb, to get a page or area to a target score, or to drive a number down or up over several rounds.
argument-hint: "[what to climb] [measure] [target]"
---

# /hill-climb — change, measure, repeat

The measure never moves while the thing improves: the same capture or
command, the same data, the same scoring prompt, every round. Then a move in
the number is the thing moving. Everything else is yours to judge.

## Agree with the person first

In one short message:

- **The hills**: one page or several, one number or several. Hills that
  share code climb together, since a fix to one can lift the others.
- **The measure.** Objective: a command that prints a number, run enough
  times to see past noise, against what prod runs (a production build, not
  the dev server). Judged: a `/council` scoring a fixed set of screenshots
  in agreed categories. Optionally, **references** the person names as the
  bar (another page of ours, or their screenshots of another product at the
  same sizes), scored every round beside ours under neutral names, so the
  judges' drift shows.
- **What may change**: for a page, its look and layout, and whether
  reorganising it is in scope. Never what a feature does, and no feature
  removed.
- **The target and the budget.** Theirs to set. If they don't, for a judged
  climb: 9 out of 10 from every judge in every category (and at or above the
  references), within about 8 rounds. An objective climb needs its number
  agreed.
- **What it will cost**: a council per hill per round at least, plus any
  look across hills and comparisons. Start Codex's sign-in (the council's
  runner) while they're there: it needs them.

## The loop

Commit, measure, weigh, decide, change, look; repeat. The parts that have
mattered:

- **Know the noise before reading a move.** Score the unchanged baseline
  twice: a move inside the spread, up or down, isn't a move, and a pass by
  less than it is scored again.
- **Check the capture before judging.** The screenshots must show the
  round's commit, or the scores belong to another one; and a judge who finds
  a listed change missing stops trusting the list.
- **Undo what made things worse** before building on it.
- **Freeze the scoring prompt and the scored set**: context, wording rule,
  categories, reply shape, which screenshots are scored; only the list of
  changes is new each round. Fixed points can grow (a design kept on
  purpose, the person's taste), but never just to quiet a finding you
  declined, and a rise in the round one is added isn't the page improving.
  Any other change, the judges' effort included, starts a new baseline.
- **Decide with the council's rules** (*Weigh and act*).
- **For an objective measure**, find candidates by profiling, and measure
  one change at a time where it's cheap, so each is attributable.
- **Look at every change yourself** in the running app, and measure what
  can be measured rather than eyeballing it.
- **Keep the climb on disk.** It outlives your context: keep a state file in
  the run folder (the session's scratchpad, out of the repo where Claude
  judges start) with what the next decision and the stop rule depend on, and
  re-read it after a reset. Push every round, since the container can go
  too; the run folder goes with it, so a climb resumed in a new container
  starts a new baseline.

## Several hills

A review of all the pages together finds what's inconsistent between them
and misses each one's details; a review of one page does the reverse. Do
both.

A finding on several hills, or in shared code, is fixed once. A hill that has
reached its target still gets scored: a shared change can drop it.

## Orchestrating

You hold the prompts, the state and the decisions, and you decide who makes
each change.

- **One builder by default**: you, or one subagent you keep going back to.
  UI changes are more tangled than they look (shared styles, components,
  layouts), and one agent that compacts as it goes does better than a set
  split up front. Hand a change to a parallel implementer, in its own
  worktree, only when it's truly independent: two pages that share nothing.
- **Brief every subagent to edit, commit and report the commit, nothing
  more.** The repo's instructions may send it to run the app or open a PR,
  and a second copy of the app collides with yours. You bring the change
  in, run the app and look.
- **Findings go back to whoever built the change.** It knows why it made
  each choice, so it can fix the pattern rather than the one instance.
- **A fix of a few edits** is quicker to make than to brief.
- **Overlap the waiting**: while judges score, build what doesn't depend on
  their answer.

## A structural choice is an experiment

When a fix is a choice between layouts or approaches, prototype each behind
a temporary switch, capture them side by side, and ask the council to compare
them. Build the winner properly, take the switch out, and keep the choice as
a fixed point. When the problem is big ("this feels bad on a phone"), explore
structures, not polish.

## Effort and stopping

While the wins are easy, judge at a lower effort: rounds come back sooner,
and cost less. Each change of level is a new baseline, so step up rarely. A
pass counts only at `xhigh`, so confirm one found lower by scoring that
commit again.

Stop:
- **at the target**, on one commit, with every judge run;
- **on a plateau**, when rounds stop moving beyond noise;
- **at the budget**.

Short of the target, report what's still short and what the judges say holds
it back.

## The person's part

- After a round that improves, show before and after side by side with a
  note on each change (small changes are invisible without them), and carry
  on: wait only when a choice is theirs.
- Their taste beats the council's: it becomes a fixed point.
- The council's pass isn't their approval.

## The branch and the PR

Know what a push deploys; if it puts the climb in front of people, ask
first. No PR until the climb stops, since an open one reruns CI on every
round's push; then review and open it the repo's usual way. If its fixes could change the
result, measure that head again before calling it a pass, or say which commit
was measured. Then add a `## Hill-climb` section to the description: each
hill's lowest score per judge each round (medians for an objective measure),
the references', the fixed points added during the climb, and what was
declined to hold scope. Keep it there through later edits.
