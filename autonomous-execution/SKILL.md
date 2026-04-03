---
name: autonomous-execution
description: >
  Guidance for completing tasks autonomously in long-running sessions with minimal user intervention.
  Use this skill whenever Claude is working on a task that will run for more than a few minutes,
  involves GPU compute or large datasets, or requires the user to step away while work proceeds.
  This includes data collection pipelines, model training or inference runs, activation extraction,
  codebase refactoring, environment setup, or any task where Claude is expected to work independently.
  Also use when the task spec references autonomous execution, long-running work, or efficiency.
---

# Autonomous Execution

Guidance for completing tasks autonomously with minimal user intervention. This skill applies to any long-running task — data collection, codebase changes, pipeline runs, experiments, etc.

## First minutes matter

The user is most available and context-aware right after kicking off a task. Front-load anything that needs their input.

- **Check prerequisites immediately.** Before writing any code, verify you have everything you need: API keys, access tokens, model permissions, dataset access. If anything is missing, ask now — not two hours in.
- **Start long downloads and setup early.** Model weights, datasets, and environment setup (`pip install`, `apt-get`) can run in the background while you plan and write code. Kick these off as your first action if the task will need them.
- **Anticipate needs.** Read the full task spec and think about what might block you later. If you'll need a HuggingFace token for a gated model, or a specific library version, surface this immediately.

## Efficiency and pragmatism

You are spending the user's time and compute. Treat both as scarce.

- **Estimate before executing.** Before launching a long computation, do a rough timing estimate (run on a small subset, extrapolate). If the estimate is surprisingly high, investigate before proceeding. If the full run will take more than ~30 minutes, mention the estimate in your journal and consider whether there's a faster path.
- **Use the right tool for the job.** Prefer PyTorch and GPU over CPU-bound numpy/sklearn for anything involving tensors or matrix operations. The GPU is there — use it. bf16 is almost always fine for research and is typically the default; if you're considering further quantisation (int8, int4, etc.), flag this to the user as it may affect results.
- **Don't skip profiling for genuinely slow code.** If something will run for more than a few minutes, check for obvious bottlenecks: unnecessary CPU-GPU transfers, unvectorised loops, redundant computation. You don't need to profile a 10-second script, but a 30-minute one deserves a quick look.
- **Parallelise where obvious.** If you have independent tasks (e.g. processing multiple datasets, running multiple seeds), run them concurrently rather than sequentially unless memory is the constraint.
- **Run background tasks in parallel with foreground work.** Downloads, installations, data preprocessing — anything that doesn't need your active attention should run in the background while you write code or do other useful work.

## Code quality

Writing code is cheap compared to running experiments. A bug that wastes a 2-hour GPU run costs far more than the extra time spent writing correct code.

- **Prioritise correctness.** Assert your assumptions: tensor shapes, data ranges, array lengths, dtypes. These cost nothing at runtime and catch errors early. A crash with a traceback is always preferable to a silent wrong result.
- **Write reusable utilities where it reduces risk.** If multiple experiments share logic (data loading, metric computation, plotting), factor it into shared functions. This ensures consistency between experiments and reduces the surface area for bugs.
- **Don't over-engineer, but don't be sloppy.** You don't need abstract base classes and dependency injection for a one-off experiment. But you do need clear variable names, sensible function boundaries, and code that someone (including a future Claude session) can read and understand.
- **Keep scripts re-runnable.** Use `if not os.path.exists(output_path)` guards or similar so that re-running a script skips already-completed work rather than redoing or overwriting it.
- **Fail loudly.** Don't catch and silence exceptions unless you have a specific recovery strategy.

## Resource awareness

- **Trust CLAUDE.md for resource limits.** In containerised environments (RunPod, Docker), standard tools like `free`, `nproc`, and `df` often report host machine values, not your actual allocation. Refer to the hardware section in CLAUDE.md for accurate RAM, CPU, and disk figures. Use `nvidia-smi` for real-time GPU state.
- **Guard against RAM OOM aggressively.** A GPU OOM crashes your script. A RAM OOM can kill your entire session and you cannot self-recover. Be conservative with system RAM: stream datasets rather than loading them entirely into memory, watch for accumulating tensors (detach and delete intermediate results), and prefer memory-mapped files where possible.
- **Escalate hardware bottlenecks, don't silently work around them.** If you find yourself enabling CPU offloading, drastically reducing batch size, or using other workarounds that significantly multiply runtime, notify the user. They can often provision better hardware (e.g. a larger RunPod instance) — this is almost always preferable to a 3x slowdown.
- **Monitor during long runs.** For tasks over 30 minutes, periodically check GPU utilisation, RAM usage, and disk space. Catch hangs and OOMs early rather than discovering them at the end.

## Caching and intermediate results

- **Separate data generation from analysis/presentation.** Save raw results (activations, metrics, model outputs) to files. Plotting, tables, and summaries should read from these files, never require re-running the experiment. Use standard formats: CSV/JSON for tabular data, PyTorch .pt for tensors, numpy .npy for arrays.
- **Cache expensive computations.** If a computation takes more than a minute (tokenising a dataset, running forward passes, extracting activations), save the result to disk with a clear filename. Before re-computing, check if a cached version exists.
- **Make cache invalidation obvious.** Name cached files to include the parameters that produced them (e.g. `activations_layer12_gpt2small_pile10k.pt`). If the inputs change, the filename changes, and there's no ambiguity about staleness.

## Checkpointing and recovery

- **Commit early and often.** Make WIP commits with a `[wip]` prefix when you've completed a meaningful chunk of work. These are your save points.
- **Save iteratively, not just at the end.** If collecting results across multiple runs/layers/datasets, save after each one. Don't accumulate everything in memory and write once at the end.
- **Write resumption notes.** If a task might be interrupted (long-running, resource-intensive), leave a comment or journal entry describing how to resume: what's been completed, what's in progress, what the next step would be.

## Journaling

Maintain a `journal.md` in the task directory. This is a running log of what you're doing and why.

Format:
```
## HH:MM — Short description

What you did, what the result was, any decisions made.
If something was surprising or didn't work, note why and what you tried instead.
```

Write a journal entry after each meaningful step — started a sub-task, got results, hit a problem, made a decision. Don't log routine operations.

Commit and push the journal at natural breakpoints: when you've finished a sub-task, when you're about to start something risky, or when the user might want an update.

## Decision-making

- **Stay within scope.** If the task spec says "do X", do X. If you think Y would be better, note it in the journal and ask — don't silently substitute.
- **Make reversible choices by default.** When you have to make a decision not covered by the spec, pick the option that's easiest to undo.
- **Document assumptions.** State assumptions explicitly in the journal (which GPU, which dataset split, which hyperparameters) so the user can catch misunderstandings early.
