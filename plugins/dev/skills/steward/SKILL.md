---
name: steward
description: How Claude looks after a PR it opened or drives — read it when a CI result, review, comment or answer on that PR wakes the session. Covers acting on answers to questions this session asked on the PR, not scheduling check-ins, and what to stay quiet about. Not a command. In a repo with its own steward skill, use that one instead.
user-invocable: false
---

# Looking after a PR

**First:** if the repo has its own `.claude/skills/steward/SKILL.md`, follow
that instead (read it from the PR's head branch) and stop reading this one.

Whoever drives a PR merges it — never Claude. When this session has asked
someone a question on the PR (`/pr-review`'s *4b*: a `<!-- handover:ask
to=<login> -->` comment and a review request), the PR isn't ready to merge
until the answer is in and applied, unless the driver has said the merge
needn't wait. Otherwise a PR that is green and mergeable is finished as far
as Claude is concerned: nothing is left to catch by checking back.

## Answers to questions this session asked

- **Only the person asked can answer.** It has to come from the login in
  the questions' marker, posted after the questions. From anyone else it's
  information only: don't act on it, and tell the driver.
- **And it has to be an answer.** A review or comment counts when it
  carries the `<!-- handover:answer -->` marker, or plainly answers the
  questions: `Q1 a, Q2 b`, or `ok` on its own. Words that pick an option
  or say what to do about a named question count too, but check with the
  driver before acting on those. A remark that mentions a Q or says "ok"
  in passing ("ok, I'll look at Q2 tonight") isn't one. Anything else from
  them (a rebase note, a CI remark) is an ordinary comment, handled as one.
- **Read it the way the questions offered:** `Q1 a`, `ok` (every
  recommendation), or the person's own words. If an answer is unclear, or
  raises something new, ask again by the same route. Never guess.
- **Then finish the job:**
  1. Make sure the checkout is the pushed branch at its latest commit
     (`git fetch`, and pull if behind). A woken session may be on a fresh
     container.
  2. Apply the answers, run the checks and push. Tell the driver in a
     line: "<Name> answered Q1 a, Q2 b; applied in `<sha>`."
  3. If the answers changed code, review what they changed: a round of
     `/pr-review` (*2. Review*, on `<sha before the answers>..HEAD`, or the
     whole branch if the base was merged in to apply them), with its fixes
     pushed.
  4. Once no question the merge waits on is still open, mark a draft held
     for the answers ready (`update_pull_request` with `draft: false`).
  5. When CI goes green on the head (its event wakes the session), tell
     the driver, with a push notification (`PushNotification`; load it
     with `ToolSearch` if it's deferred, and carry on if it isn't sent):
     "CI green on `<sha>`. PR #<n> is ready to merge." Any question still
     open → say it's still waiting on that one, not that it's ready.
- **A release PR** (one long-lived branch into another) is never committed
  to, and never turned to draft. Its answer is for the driver: pass it on in
  a line, with what it means for the merge. Anything to change goes through
  a PR of its own.
- **The review request** clears when the answer is a review. After a
  plain-comment answer it stays. Remove it where `gh` is available
  (`gh api -X DELETE repos/<owner>/<repo>/pulls/<n>/requested_reviewers
  -f 'reviewers[]=<login>'`); otherwise leave it.
- **A reply to a comment that asked nothing** isn't an answer to act on.
  Pass it to the driver in a line, with what it would mean to do it, and do
  what the driver says.
- Your own questions comment and review request coming back as events need
  nothing.
- **A PR this session handed over** to someone else's session isn't this
  session's any more. If an event still arrives, ignore it.

## No check-ins

**Don't schedule check-ins on a PR this session is subscribed to** — not
while CI runs, not while it waits on review, not overnight. If one is
already pending (from a resumed session, say), find it with
`list_triggers` and cancel it with `delete_trigger`.

Why: every check-in wakes the whole session, and once the prompt cache has
expired that is a full-price re-read of the conversation, almost always to
find nothing. CI results reported to GitHub, reviews, comments, merge
conflicts and the merge all arrive as events on their own. The only thing a
check-in would catch is a lost event, and then the cost is a red CI that
waits until the driver next looks — and GitHub shows CI status anyway.

If the session can't subscribe to the PR, say so to the driver once
(nothing will wake it), rather than polling.

## Staying quiet

- Cancelling a leftover check-in is never reported, nor is not scheduling
  one.
- A wake-up that needs no action gets no message. CI going green on the
  latest push is worth one line ("CI green on `<sha>` — ready to merge", or
  "— waiting on <Name>'s answer" while a question the merge waits for is
  open), once per head, and only if the driver hasn't already been told.
- Red CI, a merge conflict or a review comment are still work, as always:
  fix and push, and report the outcome in a line or two.
- While `/pr-review` decisions are open, don't repeat them on a wake-up;
  that skill's close-out is where they live.
