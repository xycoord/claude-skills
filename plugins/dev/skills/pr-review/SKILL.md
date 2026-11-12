---
name: pr-review
description: Get a branch to ready before handing it over — review it in rounds with the built-in /code-review, fix the clear findings, brief whoever is driving on the calls that need them, then open (or ready) its PR with a problem-first description. Claude runs this itself once it judges work done that is going to a PR (the branch has one, the person asked for one, or the repo's docs say changes go through PRs), before opening the PR or saying it's finished; otherwise it offers it in a line. It can also be typed. Not mid-iteration, and not again on a head a run already covers. In a repo with its own pr-review skill, use that one instead.
argument-hint: "[low|medium|high|xhigh|max]  (default high; medium for docs only)"
---

# /pr-review — make it ready, and ask only what needs a person

**First:** look for the repo's own copy at
`<root>/.claude/skills/pr-review/SKILL.md`, where `<root>` is `git rev-parse
--show-toplevel` in the checkout the branch is in (not wherever the session
started). If it's there, invoke the repo's `pr-review` skill with this run's
argument (`$ARGUMENTS`), or read that file and follow it with that argument,
and stop reading this one. It knows the repo's people, branches and checks;
this is the general version.

What reaches the driver (the person working with this session) should be the
most finished thing Claude can make on its own: reviewed, fixed, proved and
described. The driver's part is the decisions. Everything else — the review,
sorting the findings, the fixes, the checks, the push, the PR — happens
without them, and nothing is called ready until it meets the bar below. A
reviewer's time is for the calls only a person can make, never for finding
what Claude could have found.

The driver should hear about each decision **as soon as the findings are
sorted**, and never wait for the fixing to finish before they can answer.

## When it runs

- **Claude runs it by itself** once it judges a branch done **and the work
  is going to a PR**: the branch already has one, the driver has asked for
  one, or the repo's docs say changes go through PRs. Then it runs before
  opening the PR, or before telling the driver the work is finished,
  whichever comes first. The driver can also type it.
- **Otherwise, offer it:** end with one line, "`/dev:pr-review` to review
  this and open a PR?", and don't run it.
- **Say nothing** on the default branch, or in a repo with no GitHub
  remote: the work isn't going through a PR.
- **Not mid-iteration:** while the work is still being built, or the driver
  is still trying versions out.
- **Not twice on the same head:** if a run's close-out already covers this
  commit, say so in a line instead.
- **Not on a release PR** (one long-lived branch into another, e.g.
  `develop` into `main`), or the merge-back after one: its PRs were each
  reviewed on the way in.

## Read the repo first

The repo decides what this skill can't. Before step 1, read the root
`CLAUDE.md` (and any it points to for the area changed), then `CONTRIBUTING`
if it exists, for:

- **the base branch** a PR goes into: the open PR's base if there is one;
  otherwise what the repo's docs say; otherwise the default branch (`git
  ls-remote --symref origin HEAD`: `origin/HEAD` is often missing in a
  cloud clone). Never a `dev` branch merely because one exists. The brief
  names the base, so the driver can catch a wrong one before the PR opens;
- **the checks** to run before a push (a `make` target, package scripts, the
  CI workflow's steps);
- **who owns what**: a written rule in `CLAUDE.md` or `CONTRIBUTING` that
  gives a kind of change to a named person beyond the driver (an owner of
  the servers, of money rules, of security). Those become questions on the
  PR (*4b*). `CODEOWNERS` doesn't count: GitHub requests those reviews by
  itself, and it says whose review is needed, not whose decision a finding
  is. If the repo names nobody, every decision is the driver's and *4b*
  never applies;
- **the driver's GitHub login** (the MCP's `get_me`, or `gh api user --jq
  .login`). A named owner who is the driver is nobody else. A team, or a
  person the repo gives no GitHub login for, can't be asked through *4b*:
  that call goes to the driver, with who else should see it;
- **house rules**: standing answers about whole classes of finding, in
  `.claude/pr-review-rules.md` if it exists. A finding a rule covers is
  fixed or dropped as the rule says, never asked about again.

## Ground rules

- **The review itself is the built-in `/code-review`.** Don't add review
  heuristics here or second-guess its method: it improves as Claude Code and
  the models do, and this skill should get those improvements for free. This
  skill only decides what happens to each finding and who sees it.
- **Every finding, not the top few.** Claude is doing the fixing, so a cap
  only hides work. Always pass `--max-findings all`. Keeping the PR small
  is the sort's job (step 3), not the review's.
- **Effort is `high`** unless the driver passes a level. This run's
  argument: `$ARGUMENTS` — use it as the level if it is one of `low`,
  `medium`, `high`, `xhigh`, `max`; otherwise `high`, or `medium` when the
  branch changes only docs, skills or wording.

## Ready means

Say a PR is ready only when all of these hold. Never "ready, but…": what
falls short is either fixed or said plainly as the thing still open.

- **Every change in the diff is proved.** Logic has a test that would fail
  without it, where the repo has a test suite; where it has none, it has
  been run (a script, a REPL call, the command's output) and *How it was
  checked* says how. Adding a test framework is a Decide, never a Fix. What
  users see has been tried in the app, with screenshots
  (the `verify` skill), and the ones that show the change are in the PR
  description (*6. Open the PR*). A docs or skills change has been read
  through as its reader would. Anything that couldn't be checked here is
  named in the PR description.
- **The last review round found nothing left to fix** (step 2).
- **Every finding is fixed, or declined with a reason** the driver can
  read.
- **The PR merges into its base without conflicts**, and CI is green on its
  head (where the repo has CI). CI runs only once the PR is open, so it's
  the last thing to land. Being behind the base is fine unless GitHub
  says the branch must be up to date to merge (the PR's merge state reads
  `behind`): then it's short of ready, and step 1.5 says what to do.
- **The PR description is current** (*6. Open the PR*).
- **No decision is open** for the driver, and no question waits on anyone
  else, unless the driver has said the merge needn't wait.

## 1. Get the branch ready

1. On the base branch or the default branch → stop: there is no feature
   branch to review.
2. Uncommitted changes to tracked files (`git diff HEAD` is not empty) →
   stop and ask whether to commit them first. Never review a tree that
   differs from what the PR will show. Untracked files don't count.
3. Find the branch's open PR, if there is one: its base is `<base>` from
   here on (otherwise the base from *Read the repo first*). Subscribe this
   session to its activity (`subscribe_pr_activity`) where that tool
   exists. No PR → don't open one yet: it opens in *6. Open the PR*,
   reviewed, unless questions need it sooner (*4b*).
4. Fetch the base by name, so a single-branch clone gets it: `git fetch
   origin +refs/heads/<base>:refs/remotes/origin/<base>`. If `git
   merge-base origin/<base> HEAD` then finds nothing (a shallow clone),
   unshallow it the same way: `git fetch --unshallow origin
   +refs/heads/<base>:refs/remotes/origin/<base>`, plus the same for the
   branch if it's on origin. Do this before every review round.
5. Behind its base → leave it, and say so in the close-out: an unasked
   merge commit is noise. Update it only when the driver asks or GitHub
   requires it (*Ready means*), and then by merging the base in. Anything
   that rewrites the branch's history (a rebase, a force-push) needs the
   driver's yes first, and the next review round then covers the whole
   branch. Either way:
   - **It conflicts** → stop, and tell the driver what conflicts. GitHub
     runs no checks on a conflicted PR. Don't resolve it unasked.
   - **Updating would need care the repo calls out** (migrations to
     renumber, generated files, a lockfile) → do what the repo's docs say.
6. Unpushed commits → run the repo's checks for what
   the branch changes, then push the branch once (`git push -u origin
   <branch>`). If a pre-push hook or a check fails, fix what it reports,
   commit, and push again before going on — the review must see the code
   the PR will contain.
7. Note the size before review: `git diff --shortstat origin/<base>...HEAD`.
   *3. Sort* compares against it.
8. **Try the UI, alongside.** The review reads code; it doesn't use the
   app. If this branch changes what users see and you haven't already tried
   this version in a browser, start the `verify` skill now in a background
   agent, in this checkout, and carry straight on to *2. Review*. If item 2
   or 5 stopped for the driver, start it once the branch is settled. Tell it
   to report only: no edits, commits or pushes, none of the skill's
   fixing (the review is changing code alongside it), no sending files to
   the person (report the screenshot paths), and never switching branches
   or stashing in this checkout. A "before" it hasn't got comes from a `git
   worktree` of `origin/<base>` on another port, or is reported missing. Wait for its
   report before sorting: each problem it saw is a finding like the
   review's, and the screenshots that show the change best go out with the
   close-out and in the PR description.

## 2. Review, in rounds

**Round 1** reviews the whole branch, `origin/<base>...HEAD`. Fetch the
base first as in step 1.4, so the range is current. Invoke the `code-review`
skill with the effort level, `--max-findings all` and that range, e.g.

```
high --max-findings all origin/main...HEAD
```

Then sort (step 3), brief (step 4) and fix (step 5).

**Later rounds review the fixes**, because a fix is new code too. Before
fixing, note the head (`<pre-fix sha>`) in the brief, so it survives a
long wait. After the round's push, review `<pre-fix sha>..HEAD` the same
way, and check that each finding the last round fixed is really fixed. If
the base was merged in or the branch rebased after `<pre-fix sha>` (to
clear a conflict, say), that range holds other people's work, or no
longer exists, so review the whole branch again
(`origin/<base>...HEAD`) instead. New findings are sorted, briefed and
fixed as in round 1; their decisions continue the brief's numbering, in a
short follow-up brief in the same shape.

**When to stop:**
- after a round with nothing to fix (only drops, or nothing at all);
- after 3 rounds, or 5 when a round's findings touch auth or security,
  data loss, money or concurrency.

An answer that arrives later and changes code gets one round on what it
changed, even past the limit; any more count toward the limit. An answer
that changes nothing needs no round. If the limit is reached with fixes
still being found, stop anyway and say so in the close-out. It usually means
the approach needs a rethink, which is the driver's call (a decision of its
own, including whether to go on).

Each review takes several minutes. If it runs in the background, say in one
line that it's running and wait for its result to arrive — don't poll.
However it reports its findings (as text, through `ReportFindings`, or as a
background agent's report), carry on from step 3 with that list.

## 3. Sort every finding

Read the code each finding points at before you sort it — a finding is a
claim to check, not an order. **Judge a finding by what happens when its
path is hit, not by how often it's likely to be hit.** Each goes in exactly
one bucket:

- **Fix** — you can trace a realistic path from a real caller, input or
  user action to the failure, and the fix is in proportion to what it
  prevents. A rare path is a Fix however rare when hitting it means:
  - a wrong figure, especially money;
  - data lost, or saved wrongly;
  - an answer that is silently wrong;
  - a security hole;
  - or a user stuck with no way through.

  Prefer the fix that deletes or narrows code to one that adds. A fix that
  takes a lot of code is still a Fix, as long as it stays within what the
  PR set out to do.
- **Decide** — a reasonable answer depends on something a person knows or
  owns. Two kinds:
  - *product calls* — behaviour or UI users will notice that the PR didn't
    set out to change; how the product answers a question for them; money,
    pricing, billing and other business rules;
  - *technical calls* — security trade-offs; writes to outside services; a
    finding that disputes a decision the repo has written down; a fix that
    widens the PR well beyond what it set out to do; two defensible fixes
    with different costs; a failure path you can't tell is realistic.
- **Drop** — the path is far-fetched, the finding is wrong on reading the
  code, it's already handled, or the fix costs more than it buys. A rare
  path whose worst case is cheap is a nit, whatever label it came with: an
  error message and a retry, a cosmetic glitch, a log line. Each drop needs
  a one-line reason; the driver sees them at the end and can overrule. One
  worth doing some day goes under **Follow-ups** instead.

When a finding fits both Fix and Decide, settle it in this order:

1. Money, billing or security → **Decide**, however clear the fix and even
   when it only restores what the PR meant to do.
2. Otherwise, a fix that restores what the PR plainly meant to do →
   **Fix**, even when users will see it.
3. Otherwise → **Decide**.

Findings that are really the same problem merge into one.

**Keep the PR the size of the job.** After the last round, compare
`--shortstat` with the one noted in *1. Get the branch ready*.

- **If the review grew the PR noticeably**, look again at what grew. Keep
  the fixes for costly paths. Cut what serves no one:
  - handling for states that can't happen;
  - options nobody asked for;
  - an abstraction with one caller;
  - checks that repeat one already made.
- **Useful extras aren't bloat.** The work may have added things beyond the
  ask that make someone's job easier, such as keyboard shortcuts on a page
  people click through all day. Don't strip those, unless they're wrong.
  Name each one in the PR description under **Also added**, so it's found
  on purpose and can be turned down.

**Who decides.** Every Decide is the driver's, in the brief — except one the
repo gives to someone else (*Read the repo first*): that is a question for
them on the PR (*4b*), and the brief says it went there. If the PR as a
whole touches an area the repo says needs a named person's say, that is a
question too, whatever the findings say.

## 4. Post the brief — before fixing anything

As soon as the sorting is done, and **before the first fix**, post the
brief as ordinary chat text (not a question picker) and send a push
notification with `PushNotification`: "N decisions waiting on <branch or
PR>" (skip it when there are none). It is often a deferred tool — load it
with `ToolSearch` (`select:PushNotification`) first. If it isn't available
or reports "not sent", carry on: the brief in chat is what matters. Then go
straight on to step 5 in the same turn — don't end the turn to wait for
answers.

Use exactly this shape, every time:

```markdown
## PR #<n> · <N> decisions for you

Into `<base>`. Fixing <F> findings meanwhile (from `<pre-fix sha>`),
dropping <X> (listed at the end).
<When there are any: "<Q> go to <name> as questions on the PR — don't merge
until they've answered.">

**D1 · <the decision as a short question>**
`<path>:<line>` — <what goes wrong, concretely: who does what, and what
they see or what breaks. One or two sentences.>
<Only if it helps: why it isn't an obvious fix, in one sentence.>
- **a** (recommended) <option> — <its cost or consequence>
- **b** <option> — <its cost or consequence>
- **c** Leave as is — <what that means>

**D2 · …**

Reply like `D1 a, D2 b, D3: <your own words>` · `ok` takes every
recommendation · anything you don't mention stays open.
```

Rules for the brief:

- Before the PR is open, the branch name stands in for `PR #<n>`.
- Lead each decision with the consequence in the user's terms (what they
  see, what figure is wrong, what's lost), not the code's. The `path:line`
  is there to open if wanted; the text must stand without it.
- A code excerpt only when the decision turns on the exact code, at most
  6 lines.
- 2–4 options. Always mark one recommended and put it first. "Leave as is"
  is an option whenever it's a real choice.
- Keep each decision to about 8 lines. If it can't be explained in that,
  it's still one decision — say less about the mechanism, more about the
  choice.
- No decisions → say so in one line and carry on.

### 4b. Questions for someone else

Only when the repo gives a call to a named person other than the driver.

1. **Can it be answered without them?** A question this session can settle
   from the code, the repo's docs, GitHub or public documentation isn't a
   question for a person. Look first.
2. **It needs a PR.** If there isn't one yet, open it as a draft, with the
   description from step 6 as far as it goes, and subscribe this session to
   it straight away (`subscribe_pr_activity`, where that tool exists), so an
   answer wakes it. Step 6 marks it ready.
3. **Post one comment** addressed to them, starting with the marker
   `<!-- handover:ask to=<their GitHub login> -->`, then `@<login>`, a line
   on what the PR does, and each question numbered `Q1`, `Q2`… in the
   brief's shape (consequence first, options, one recommended), ending
   "Reply like `Q1 a, Q2 b` · `ok` takes every recommendation". Then
   request their review on the PR: that is the "your turn" signal.
4. Their answer wakes this session; the `steward` skill says how to take it.

**When they go out** depends on what they're asked to judge:

- **A question about one finding** → right after the brief and before the
  first fix, as the driver's decisions do. It stands whatever the fixes
  change, and the answer may take hours. Don't fix that finding before
  they answer.
- **A question about the PR as a whole** → at step 6, once the last round
  has found nothing to fix, so they judge the finished thing: the
  description current, the screenshots on the PR itself, and the question
  describing the PR as it is now. If the branch changes afterwards in a way
  the question covers, edit the comment to match and say so in a line. The
  PR stays a draft until it's answered.

## 5. Fix, and pick up answers as they arrive

Work through the **Fix** bucket. There's no tool to check for a reply:
anything the driver sends while you work is delivered to you between tool
calls, so keep each fix to ordinary tool calls and watch for it. When an
answer arrives, add those decisions to the work (an answered decision is
just another fix, or a drop). Don't hold the clear fixes for the answers,
and don't hold the answers for the clear fixes. A decision with no answer
by the close-out stays open — never guess one.

Work quietly: no commentary between fixes. Every line written here pushes
the brief further up the screen while the driver is reading it.

- Group commits by problem, with messages that say what was wrong.
- A fix for a logic bug comes with the test that would have caught it,
  where the repo has a test suite (otherwise, run it and say how).
- Before pushing, run the repo's fast checks for what you touched, and
  re-read your own diff for anything CI would reject.
- Push once per round, when its Fix bucket is done, including any
  decisions answered by then. Later answers get their own push, and their
  own review round.
- An answer that states a rule for a *class* of finding ("never add server
  validation for UI-only filters") → after applying it, offer in one line
  to add it to `.claude/pr-review-rules.md` (one line per rule: what to do,
  and why), creating the file if needed, and add it if the driver says yes.

Then the next round (step 2), until it stops.

## 6. Open the PR, or bring it up to date

- **No PR** → open one into `<base>`, not as a draft, unless a question
  about the PR as a whole holds its merge (*4b*). Use the GitHub MCP tools;
  where there are none, the REST API (`gh api repos/<owner>/<repo>/pulls
  -f base=<base> -f head=<branch> -f title=… -F body=@<file>`, adding `-F
  draft=true` for a draft). `gh pr create` uses GraphQL, which a cloud
  session's proxy refuses.
- **A draft** → mark it ready (the MCP's `update_pull_request` with `draft:
  false`; else, in a cloud session, `gh api -X POST
  repos/<owner>/<repo>/pulls/<n>/ccr/ready_for_review`; on a laptop, `gh pr
  ready <n>`), unless a question to someone else is still open and the merge waits for
  it. Then it stays a draft until the answer is applied, so nobody merges
  it early.
- **A question about the PR as a whole** (*4b*) goes out now, after the
  description and any screenshots are in place.
- **Either way:** subscribe this session to the PR's activity
  (`subscribe_pr_activity`) where that tool exists, so CI results and
  answers wake it. Don't schedule a check-in to watch CI or a reply (the
  `steward` skill has why). Make the description match what the branch is
  now.

**Screenshots.** When the PR changes what users see, the description shows
it: the few `verify` screenshots that carry the change, before and after
for existing UI, in a small table under the bullets. Use the repo's own
script for this if it has one; otherwise `PR_SHOTS_PROTECTED=<base> bash
<this skill's folder>/scripts/pr-shots.sh push <files>` puts them on a side branch
(`shots/<branch>`, never merged) and prints the image lines; `steward`
deletes the side branch when the PR closes. Run it again
after a fix changes what they show, and replace the lines. Sample data
only, never a real person's details: anyone who can read the repo can see
them.

The title says what changes, in plain words. The description **starts
with the problem**, as the people who had it saw it, and only then says
what changed:

```markdown
<What was wrong or missing, and for whom: one to three sentences. The
problem, not the patch.>

<What changes, in a few bullets: what someone will see or do differently
first; the mechanism only where a reviewer needs it.>

**Also added:** <each extra beyond the ask, in a line> (leave out if none)
**How it was checked:** <one line: the tests added or run, the screenshots>
**Not covered:** <anything that couldn't be checked here> (leave out if none)
```

- If the repo has a PR template, keep its headings and fit this into them.
- **Not covered** is for what this session couldn't reach after trying,
  never for what it didn't look up. A check a session can run (a CI run's
  result, a health endpoint) is run, not left as a tick-box for a person.
- Bad: "Refactor ChecklistRow; add useScrollRestore; update tests."
- Good: "Ticking a checklist row on a phone jumped the page back to the
  top, so people lost their place on long lists. Ticks now keep the
  scroll position."
- End with the attribution lines the session asks for, and never name a
  model anywhere in it.

## 7. Close out

The bottom of the last message is all the driver sees above the prompt
box, and by now the brief from step 4 has scrolled out of sight. So **open
decisions always come last, in full** — the record of what was done goes
above them, kept short. End the turn with:

```markdown
**Fixed** (<F>): <fix>, <fix>, <fix> — <short sha(s)>
**Decided**: D1 a — <what was done>
**Dropped** (<X>): <finding in a few words> (<why>); <…>
**Follow-ups** (<Y>): <worth doing some day, in a few words>; <…>
**Waiting on <name>** (<Q>): <item in a few words>; <…> — asked on the PR
**Rounds**: <R> (the last found nothing to fix) · size <+a/−b> before review, <+c/−d> after

---

## <N> still need you

**D2 · <question>**
<the full D2 block from the brief: consequence, options, recommendation>

**D3 · …**

Reply like `D2 a, D3: <your own words>` · `ok` takes every recommendation
```

- Each record line is one line, a phrase per item, not a bullet. Leave out
  a line that would be empty. `path:line` only where the driver would need
  it to overrule a drop.
- Nothing open for the driver, and the rest of *Ready means* met apart
  from CI → look at CI on the head first, then end with one line in place
  of the decisions block:
  - Something waiting on someone else: `**Nothing needs you yet.** PR #<n>
    waits for <name>'s answers — this session carries on when they arrive.
    Don't merge it until then.`
  - Nothing waiting, CI green (or no CI) → `**Nothing needs you.** PR #<n>
    is ready to merge.`
  - CI still running, and this session is subscribed to the PR →
    `**Nothing needs you.** CI is running on PR #<n>; I'll say when it's
    green and ready to merge.`
  - CI still running, and no subscription (nothing will wake this
    session) → `**Nothing needs you yet.** CI hasn't finished on PR #<n>,
    and this session won't hear when it does: check its checks on GitHub
    before merging, and bring me back if one is red.`
  - Anything else short of the bar → say exactly what, instead of "ready".
- Never shorten an open decision to a one-line reminder: a question
  without its context is the thing the driver has to go hunting for.
- Open decisions appear in full only in the brief and in close-outs — the
  one after the fixes, and the one after each answer, which is the newest
  message and so must carry what's still open. Wake-ups while waiting — CI
  results, someone else's answer arriving — never repeat them. If one needs
  no action, say nothing; otherwise one line on what happened.

When the driver answers, or someone else's answer arrives, carry on from
step 5: apply, check, push, review the change (step 2), then step 6 (a
draft held for that answer is marked ready now), and close out again the
same way.

Merging is the person's, never Claude's: get the PR ready, then say it's
ready to merge.
