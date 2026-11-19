---
name: experiment
description: Run one research experiment from question to result, testing a hypothesis or looking for one. Covers checking it hasn't been done, choosing where it runs and its worst-case cost, writing the plan and prediction and putting them on main before anything runs, asking before costly runs, a branch and PR per experiment, proving the code on a tiny run, the first look at results, the write-up and what comes next. Use whenever you're about to run an experiment or analysis in a research repo, including small ones.
---

# Running an experiment

An experiment answers one question, and the person needs to trust the answer.
Most of what goes wrong happens before the result: a question already
answered, a prediction adjusted after the fact, a missing baseline, or a bug
found after the money is spent. This skill puts the decisions that prevent
those at the start, where they're cheap. The research repo's `CLAUDE.md` says
where things live and what may go straight to `main`; the `compute` skill
covers pods and jobs; the `record` skill covers the file format, the
write-up and the notebook.

## 1. Check it hasn't been done

Pull `main` first, since another session may have planned something since
your checkout. Then search the experiments and threads for the question,
expanding the terms through `glossary.yaml`'s synonyms, because a question
can be answered under another name. Look at planned and running experiments
and open PRs too, in case another session is already on it. For questions
about deception, also look in the earlier project named in `CLAUDE.md`. If
something close exists, say what it is and how your question differs before
going on.

Then find the thread the question belongs to, or start one if none fits. Most
experiments come from an item in a thread's Next; if so, that item becomes
this experiment's entry.

## 2. Choose the mode and how free you are

**The mode follows the purpose.** If the experiment starts with a prediction
to check, it's testing a hypothesis (`mode: test`). If it gathers data to find
patterns, it's looking for one (`mode: explore`). The two are planned and
written up differently, so decide before planning.

**How free you are follows the request.** If the person specified the
experiment, follow it exactly and ask before changing anything material. If
they set a goal and left the approach open, choose it, and write each choice
and its reason into the plan.

## 3. Choose where it runs, and its worst case

Run it in the session when it's quick enough on CPU: small models, analysis
of results already on Hugging Face, plotting. A pod's setup (start-up,
installing, downloading a model) costs minutes and money that a small job
doesn't need.

Use a GPU pod when a GPU would help, even a cheap one: for anything that
would take more than a few minutes on CPU, or that needs activations from a
model too big to run quickly on CPU. Choose the GPU with the lowest cost for
the whole run, setup included, among those that fit the model in memory.

Then work out two numbers:
- **the estimate:** the hourly price times the expected time, setup included;
- **the worst case:** the hourly price times (`MAX_HOURS` + 1 +
  `RESCUE_MINUTES`/60), which is how long the `compute` skill's job can bill
  if everything goes wrong. Set `MAX_HOURS` to about 1.5 to 2 times the
  estimate, and shorten `RESCUE_MINUTES` (to 30, say) when it makes the
  difference.

An experiment's spend is everything it uses: every launch and relaunch, and
any pod used while developing it.

## 4. Write the plan

Write `experiments/<id>/README.md` with `status: planned`, in the `record`
skill's format, before any code that produces results runs. A plan written
afterwards can't show what was expected.

Every plan says, in these places:
- **the question** (`question`), and why it's worth asking now
  (`## Why we ran it`, or `## Why we looked`);
- **the method** (`## Method`): what is held fixed, what varies, what it runs
  on, how choices such as hyperparameters and thresholds are made, what each
  repeat changes, where it runs, the estimate and the worst case;
- **the analysis plan** (`## Method`): the main metric; the rule that decides
  the answer, allowing for noise; which split each choice is made on, with
  the test split scored once at the end; the seeds; the smallest difference
  the run can resolve; and the unit of analysis, saying whether items are
  independent (tokens from one prompt are not).

When testing a hypothesis, it also says:
- **the prediction** (`prediction.text` and `written`), with the result that
  would change the person's mind, written so that it can clearly fail;
- **the references** each result will be shown against
  (`## What was compared`): what nothing would score, what something trivial
  scores, and the best score reachable, all on the same data. Controls such
  as shuffled labels and a trivial baseline are arms of the real run. If a
  reference doesn't exist, say so now;
- **the strongest alternative explanation** of the expected result for each
  arm, and the check that would rule it out (`## Checks`). In interpretability
  the usual ones are surface cues and leaks in the data, checked with a
  control set, an out-of-distribution set, and a random-direction or
  control-task baseline. A claim that the model *uses* something needs an
  ablation or steering, because a direction that can be decoded may go
  unused. Lens results depend on the lens, so name it.

When looking for a hypothesis, it also says (`## The data`, `## Method`):
- what data will be gathered, and which slices and views you expect to look
  at;
- a held-out portion that nobody looks at until a pattern is chosen to check
  on it;
- a random control shown in the same view, so a pattern can be compared with
  what noise looks like there;
- a limit on how many slices you'll look at, and that every slice is
  counted, so each pattern is reported with how many things were looked at
  before it stood out.

Leave `answer`, `held`, `how`, `commit`, `results` and `cost_usd` empty until
there are results. In the thread, the experiment's Next entry gets
`experiment: <id>` and stays `state: open` until it runs. A new thread starts
with only its `id`, `title` and `next`. Add any term the plan uses to the
glossary.

Never change a prediction after seeing results. A plan can be amended before
any results exist, with a dated line saying what changed and why. After that,
keep the plan and say in the write-up where the run departed from it.

## 5. Put the plan on `main`

Build a preview of the notebook (the `record` skill's check build) to catch
format errors, then commit the plan and push it straight to `main`, without a
PR. `CLAUDE.md` lists what may go to `main` this way; everything else goes
through the experiment's PR. Then publish the notebook as the `record` skill
says. With the plan on `main`, the notebook shows what's in progress, the
next session's check finds it, and the commit's time shows the prediction
came before the result.

Keep a separate worktree on `main` for these pushes and for publishing, so
they never mix with the experiment branch's work.

If the push is rejected because `main` moved, pull with a rebase, check again
that nobody else has planned the same experiment, and push again. If it's
refused outright, stop and tell the person. Don't run an experiment whose
plan isn't on `main`.

## 6. Go ahead, or ask first

**Under $5, go ahead.** The test is the experiment's worst case: what it has
spent so far plus this launch's worst case.

**At $5 or more, ask first.** Ask too, whatever the cost, before a third
launch after two that failed. Send a push notification with the question, the
worst case and a link to the plan on GitHub, and end the turn. Only the
person's reply in the session, or a comment from them on the PR that isn't a
job report, counts as a yes. If the answer is no, set `status: abandoned`
with a one-line `answer` saying why, put its Next entry back to open without
the experiment, and push both to `main`.

Either way, keep within the daily budget in `CLAUDE.md`.

## 7. One branch and pull request per experiment

Work on a branch from `main` named after the experiment
(`claude/<experiment-id>`). Open its PR in the research repo as a draft with
the first code commit. The code, the results and the write-up go there, and
the person merges it. The `compute` skill's job reports post to the PR, which
wakes this session.

## 8. Prove the plumbing on a tiny run

Run a tiny version first, on CPU in the session where possible: a few
examples, one seed, a small model. It proves the code works, not the result.
Check that:
- it runs end to end, and its outputs have the right shapes and ranges;
- every file it should write is written, and a pod job's are uploaded;
- a case with a known answer gets it;
- 10 to 20 raw items, inputs and outputs, look right when you read them
  yourself;
- for activations: the token positions and chat template are right, outputs
  with the hooks attached match outputs without them, the final layer
  through the lens reproduces the model's own output, and splits are made by
  prompt, not by token.

Then estimate the cost again from the tiny run's timing, and go back to
section 6 if the worst case has crossed $5.

Commit and push the code and its config (`configs/<experiment-id>.yaml`)
before the real run, so it runs from a pinned commit and can be rerun. A pod
fetches the commit from GitHub, so an unpushed commit fails only after the
pod has started and been paid for.

## 9. Run it, and take the first look

Launch a pod job as the `compute` skill says, with `REPO` and `PR` set so
reports reach the PR. When its `started` report arrives, set the
experiment's `status: running`, its `started` date and `pr`, and its Next
entry's `state: running`, then push those to `main` and publish the
notebook. A session run that will finish within minutes can skip this.

Have the job write results as each condition finishes, so a stopped job
loses little and can resume (`RESUME_FROM`). Save per-item outputs (each
example's score, prediction or activation summary) under a stable item id,
with the config, seed and commit, because the write-up's examples and checks
need them. A session run does the same: it writes to an output folder,
uploads it to the results dataset under `runs/<JOB_ID>/`, and commits only
small summaries.

Have the job write a first look early (`$JOB_OUT/FIRST_LOOK`), and check it
when it lands, controls included. Stop only for a broken implementation:
NaNs, a failed known-answer check, wrong shapes, or a control that can't be
right, such as shuffled labels scoring well above chance. A result at chance,
or a baseline that beats everything, can be the answer, so it's not a reason
to stop. To stop: delete the pod, keep its cost in the experiment's spend,
fix the code, rerun the tiny run, relaunch with a new `JOB_ID`, and note the
relaunch in the write-up.

## 10. Write it up

Merge `origin/main` into the branch first, since the plan and status pushes
moved it. If that conflicts, take `main`'s version of the plan, and never
edit the prediction to resolve it.

Then follow the `record` skill: write the result into the experiment's file
and its figures, and update the thread's findings and History. A test's
answer opens with Yes, No, Partly or No answer (when the run couldn't tell),
and `held` says whether the prediction held: true, false or partly, with
`how`. A pattern you noticed in a test that it wasn't designed to check goes
in Next as a lead, not a finding.

Add the follow-ups the result suggests to the thread's Next, each with the
action that would answer it, its cost and why it's worth doing, the most
valuable first. Build the notebook from the branch to check it, then mark the
PR ready for review. The merge wakes this session, which publishes the
notebook as the `record` skill says.

If the experiment is abandoned before any results, record that on `main`
(`status: abandoned`, a one-line `answer` saying why, and its Next entry back
to open). If it's abandoned or fails after producing results, write it up
through the PR like any other. A failed run that leaves no record will be
run again.

## 11. Say what comes next, and stop

Tell the person, with a push notification, what the result was and which
item in Next you'd do next. Don't start it until they choose.
