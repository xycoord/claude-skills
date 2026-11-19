---
name: experiment
description: Run one research experiment from question to result, testing a hypothesis or looking for one. Covers checking it hasn't been done, writing the plan and prediction before anything runs, choosing whether it runs in the session or on a GPU pod, a branch and PR per experiment, proving the code on a tiny run first, watching the first results, and handing over to the record skill. Use whenever you're about to run an experiment or analysis in a research repo, including small ones.
---

# Running an experiment

An experiment answers one question, and the person needs to trust the answer. Most of what goes wrong in research with an AI happens before the result: a question already answered, a prediction adjusted after the fact, a missing baseline, or a bug found after the money is spent. This skill puts the decisions that prevent those at the start, where they're cheap.

The research repo's `CLAUDE.md` says where things live and the daily budget. The `compute` skill covers pods and jobs. The `record` skill covers the write-up, the file format and the notebook. This skill is the path between them.

## 1. Check it hasn't been done

Search the notebook's experiments and threads for the question, expanding the terms through `glossary.yaml`'s synonyms. A question can be answered under another name, and repeating it wastes the person's time and money. If something close exists, say what it found and how your question differs before going on.

Then find the thread the question belongs to, or start one if none fits. Most experiments come from a thread's Next list; if so, say which item.

## 2. Choose the mode and how free you are

**The mode follows the purpose.** If the experiment starts with a prediction to check, it's testing a hypothesis (`mode: test`). If it gathers data to find patterns, it's looking for one (`mode: explore`). The two are planned and written up differently, so decide before planning.

**How free you are follows the request.** If the person specified the experiment, follow it exactly and ask before changing anything material. If they set a goal and left the approach open, choose it, and write each choice and its reason into the plan so it can be questioned later.

## 3. Write the plan before anything runs

Create `experiments/<id>/README.md` with `status: planned`, in the `record` skill's format, before any code that produces results runs. A plan written afterwards can't show what was expected, and the person can't tell a prediction from a description.

For every experiment, the plan says:
- the question, and why it's worth asking now;
- the method: what is held fixed, what varies, what it runs on, how choices such as hyperparameters and thresholds will be made, and what each repeat changes;
- where it runs and what it should cost (section 4).

When testing a hypothesis, it also says:
- **the prediction,** with the result that would change the person's mind, written so that it can clearly fail;
- **the references** each result will be shown against: what nothing would score, what something trivial scores, and the best score reachable, scored on the same data. If one doesn't exist, say so now;
- **the strongest alternative explanation** of the result you expect, and the check that would rule it out. Plan it for every arm.

When looking for a hypothesis, it also says:
- what data will be gathered, and which slices and views you expect to look at;
- that every further slice you look at will be counted, so a pattern can be reported with how many things were looked at before it stood out.

Never change a prediction after seeing results. If the plan turns out wrong, say so in the write-up and keep the original.

## 4. Choose where it runs

Run it in the session when it's quick enough on CPU: small models, analysis of results already on Hugging Face, plotting. A pod's setup (start-up, installing, downloading a model) costs minutes and money that a small job doesn't need.

Use a GPU pod when a GPU would help, even a cheap one, for anything that would take more than a few minutes on CPU or that needs a model's activations. Weigh the setup cost against the run: a cheap GPU that saves twenty minutes is worth it. Follow the `compute` skill for the pod, and choose the cheapest GPU that fits the model in memory.

Estimate the cost before launching, from the GPU's hourly price and the expected run time including setup.

## 5. Go ahead, or ask first

**Judge it by the worst case, not the estimate.** A pod can bill until its deadline, so the worst case is the GPU's hourly price times the time until every pod's deadline, plus the `compute` skill's margin for its fallback delete.

**Under $5 in the worst case, go ahead.** The plan shows what was predicted before it ran, which is what the person needs in order to trust it.

**At $5 or more, ask first.** Post the plan with its cost, send a push notification, and wait for a yes before launching. Keep within the daily budget in `CLAUDE.md` either way.

## 6. One branch and pull request per experiment

Work on a branch named after the experiment (`claude/<experiment-id>`) and open its PR in the research repo as soon as the plan is written, as a draft. The PR shows the plan before the result, and the `compute` skill's job reports post to it, which wakes this session. The write-up goes into the same PR, and the person merges it.

## 7. Prove the code before the real run

Run a tiny version first, on CPU in the session where possible: a few examples, one seed, a small model. Check that it runs end to end, that its outputs have the right shapes and ranges, and that its sanity checks behave: a shuffled-label control scores at chance, a known-answer case gets the known answer, and the trivial baseline lands where it should. Only then launch the real run. A bug found after an hour on a GPU costs the hour; one found on a tiny run costs a minute.

Commit and push the code and its config (`configs/<experiment-id>.yaml`) before the real run, so it runs from a pinned commit and can be rerun. A pod fetches the commit from GitHub, so an unpushed commit fails only after the pod has started and been paid for.

## 8. Run it and watch the first results

Launch it as the `compute` skill says, with `REPO` and `PR` set so reports reach the PR. Have the job write a first look early (`$JOB_OUT/FIRST_LOOK`), and check it when it lands: if the numbers are broken (chance everywhere, NaNs, a baseline beating everything), stop the job rather than paying for the rest, and fix it.

Save per-item outputs (each example's score, prediction or activation summary), not just the final numbers, because the write-up's examples and checks need them.

## 9. Hand over to `record`

When the results are in, follow the `record` skill: write the result into the experiment's file and its figures, give an honest verdict against the prediction (it held, or it didn't, and by how much), and update the thread's findings, Next and History. Build the notebook from the branch to check it, then mark the PR ready for review. When the person merges it, the merge wakes this session, which publishes the notebook as the `record` skill says.

If the experiment failed or was abandoned, record it anyway, with what happened and why. A failed run that leaves no record will be run again.

## 10. Propose what comes next, and stop

Add the follow-ups the result suggests to the thread's Next list, each with the action that would answer it, its cost, and why it's worth doing, with the most valuable first. Then tell the person, with a push notification, what the result was and what you'd do next. Don't start the next experiment until they choose.
