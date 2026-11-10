---
name: council
description: Get independent opinions on the same thing from several models of different families, then weigh what they agree on. For judging UI screenshots against categories (the measure in a /hill-climb), comparing options, reviewing a plan before building it, or a second look at a risky diff. Use when someone says "council" or asks what other models think. On a diff it's an extra opinion asked for on purpose, never part of the repo's own code review.
argument-hint: "[what to judge: screenshots, options, a plan, a diff]"
---

# /council — several opinions, independently

One model's opinion is hard to tell from noise, and a model judging work
from its own family flatters it. The same input, judged separately by models
from different families, gives a signal: what they all flag is very likely
real; what only one flags may be taste, or may be the one judge who saw it.

## The judges

- **Opus**: a fresh `Agent` with `model: opus` and `effort: <level>`, in the
  background.
- **Fable**: the same with `model: fable`.
- **GPT**: `scripts/codex_agent.py` in this skill's folder, in the
  background. Its docstring has the setup (once per container), the exit
  codes and what a call costs.

Every judge runs at the same effort level. Opus and Fable are both Claude
models, the family that usually wrote the work, so GPT is the only other
family in the room.

**Spend it at the edge.** A council earns its cost where the work is at the
edge of what one model gets right on its own: taste in a UI, a plan with
real risk, a tricky diff. On a routine change it only confirms.

**Never substitute** a model for a judge that can't run, or invent its
answer; say beside the result who didn't run.

## Isolation

The judges' independence is what makes their agreement mean anything.

- **One prompt, the same for every judge**, with everything a judge needs in
  it. Claude judges also see the repo's CLAUDE.md files and GPT doesn't, so
  never rely on what CLAUDE.md tells one of them.
- **Nothing else in front of them.** The runner starts GPT in an empty
  folder. Claude judges start in the repo, with tools that could edit, so
  put the prompt and inputs in a folder that holds nothing else and launch
  each with the same short line: read that file, look at nothing else (for a
  plan or a diff, the repo too), change nothing. Nothing stops a judge
  reading, so keep earlier answers and the climb's state away from where
  judges are pointed, and never name their paths in a prompt.
- **Never in the independent round's prompt:** the target, earlier scores,
  what another judge said, or what you hope to hear. A known goal inflates
  scores, and an agent handed your hypothesis tends to confirm it.
- Ask for one reply shape, so the answers can be set side by side.

## What a good prompt carries

Always: what the thing is, who it's for, what to ignore, and the fixed points
(choices that aren't open, each with its reason, and the person's own calls).
Then whatever the question needs. Some things that have mattered:

**UI (screenshots).**
- Who uses each page and how often, and the repo's **house wording rule,
  copied verbatim**, where it has one. Without it judges read the app as
  first-time visitors and mark the house's own terms as jargon.
- Categories to score, what each end of the scale means, evidence for every
  score short of the top naming the page and element, and changes concrete
  enough to build.
- **Screenshots judges can score fairly**, from a capture script (the
  repo's own, where it has one):
  - reset the data before every capture: a capture that types into a page
    changes what the next one starts from;
  - capture phones as touch phones (Playwright's `has_touch` and
    `is_mobile`). At phone width a desktop browser shows the mouse sizes, so
    judges mark down 44px targets drawn at 24px;
  - a realistic state, seeded or route-mocked;
  - tall pages in pieces a downscaled image keeps legible, each image named
    uniquely (the runner refuses duplicates).
- **Detail needs a close look.** Whole pages show judges the big things and
  hide the small ones: close-ups and a measured audit (computed sizes, gaps,
  colours) find the rest. In a climb, decide them before the baseline.
- **In a climb**, a neutral list of what changed since the last capture, to
  check for regressions. Never which finding a change answers, or that it's
  better.

**A choice between options**: each side by side on the same inputs.
**A plan**: the plan and the code it touches. **A diff**: the diff, the repo
read-only, and the CLAUDE.md files that govern it.

## Weigh and act

- **Agreement is evidence, not an order**, and counts for more across
  families: GPT with either Claude judge outweighs Opus and Fable alone.
- **Check every claim against the thing itself** before acting on it:
  judges misread sizes and states in screenshots.
- **A doubt that persists is signal.** One judge raising the same doubt
  round after round, with no one agreeing, deserves a proper look, not a
  vote.
- **Then let them talk.** Kept apart, judges can't do what a band does with
  "I'm not sure about that part": explain and answer each other. Where they
  still disagree on something that would change what gets built, ask each
  again in a new call with its own answer, the others' reasons (never their
  scores) and the same inputs. A doubt that survives is worth acting on; one
  given up may have been taste, or deference, so it isn't agreement. Talk
  only after the independent round, which stays the record: talking first
  anchors the judges on each other.
- Before taking a change, look for whether what it replaces was designed
  that way on purpose (a comment beside it, the CLAUDE.md files, the design
  docs, the history). Keep the purpose, and make it a fixed point with its
  reason.
- Decline what's outside what the person asked for, and say why.
- **Outside a climb, report** what the judges said and what you'd do. Change
  things only if that was the ask.
