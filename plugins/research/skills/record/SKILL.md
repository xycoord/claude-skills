---
name: record
description: Write up research in the notebook and publish it — the files that hold an experiment's record and a thread's findings, Next and History, the rules for what they say, and how the notebook page is built from them and published to its pinned artifact. Use when writing up an experiment (planned, running or finished), when a result changes a thread's findings, Next or History, when starting a new research question, and after any such change merges to main, to publish the notebook.
---

# Recording research

The research repo is the source of truth. Results are written as files in it,
and the notebook, one page published as a pinned claude.ai artifact, is built
from those files by `scripts/build_notebook.py` beside this file. **The page is
never edited by hand**, by you or anyone else: change the files and rebuild,
because a hand edit is lost at the next build and leaves the page out of step
with the repo.

## What goes where

Two kinds of file hold everything, and each fact is written once, in the file
that owns it.

- **An experiment** (`experiments/<id>/README.md`, with figures in `figs/`) is
  the fixed record of one run: why it was run, what was compared, the result,
  the method, checks and examples. Write it when the run is planned, update it
  while it runs, and finish it when the run ends. After that it doesn't change,
  except for a dated `since` line when later work changes how it reads and the
  thread's History doesn't already say so.
- **A thread** (`threads/<id>.md`) is one research question. It holds the
  current findings, Next (what's running, open questions and leads with their
  cost, parked ones with why) and History (one line per change of belief,
  attached to the run that caused it). Update it whenever a run changes what's
  believed or what to do next.

The home page, the Next view, History's run rows, search and the links between
pages are generated, so don't write them anywhere.

Each experiment has a mode, chosen by its purpose: `test` when it tests a
prediction, and `explore` when it gathers data to look for patterns. Only a
test produces a finding. Exploring produces leads, which go in the thread's
Next with `lead: true` and `from: <experiment>` until a test confirms or
rejects them.

## How to write them

- **The format** is in `references/format.md`. Follow it exactly, because the
  build reads it field by field. Quote prose fields in the YAML front matter,
  or write them as block scalars (`>-`), because YAML turns an unquoted
  `answer: No` into false and cuts a value at ` #`. Dates are ISO dates.
  An experiment's `date` is when it was planned, matching its id, and
  `started` is when it began running.
- **The writing rules** are in `references/writing-rules.md`: shared
  principles, the principles for each mode, and worked examples. Read them
  before writing anything for the notebook, and take the principles rather
  than the examples' wording. In short, the opening says the most important
  thing first, the method is visible, every result shows what makes its number
  mean something, checks and examples are evidence, and a pattern found by
  looking is offered for the person to judge, not stated as a finding.
- **The project's glossary** is `glossary.yaml` in the research repo. Use its
  names, one name per thing. When a new name for an existing thing comes up,
  add it as a synonym, because search uses the synonyms.
- **Prose** follows the person's Clear writing style
  (`~/.claude/output-styles/clear.md`).
- **The look** comes from `style:functional-design`, through the build
  script. Figures are the arguments of one call into its charts.js or
  interp.js, so read those files' comments when making one.

Before marking the PR ready, build the page from your branch to check the files:
`uv run <this skill>/scripts/build_notebook.py <repo> -o <scratchpad>/notebook.html`.
It stops on anything it can't build, such as a finding citing an experiment
that doesn't exist or a figure with an unknown view, and names the file. Fix
every error. Look at the warnings too, since each is something a reader would
miss.

## Publishing

Publish from `main` only, whenever a change to the notebook's files reaches
it, so the page always matches `main`. After a merge, the session that owns
the PR publishes: it's subscribed to the PR, so the merge wakes it. After an
experiment's plan or status is pushed straight to `main` (the `experiment`
skill), the session that pushed it publishes straight after.

1. Pull `main` in the research repo.
2. Build with `--publish`: `uv run <this skill>/scripts/build_notebook.py <repo> -o <scratchpad>/notebook.html --publish`.
   It refuses unless the checkout is clean and matches `origin/main`. A build
   without `--publish` is marked in its footer as a preview of its branch, so
   never publish one.
3. Read the artifact at `notebook.yaml`'s `artifact` address with the
   Artifact tool (`action: "read"`). A publish to an artifact this session
   hasn't read is refused.
4. Publish the built file to that address (`url` set to it).

If the publish is refused because another session published first, pull
`main`, rebuild and publish again. The rebuilt page holds both sessions'
work, because both are in `main`. Never merge two versions of the HTML by
hand.

The notebook's artifact is created once, when the research repo is set up, and
its address is committed in `notebook.yaml`. If `artifact` is ever empty,
don't create one: a second session doing the same would make a second
notebook. Tell the person instead.

## The build script

`scripts/build_notebook.py` is a self-contained uv script. It reads
`threads/`, `experiments/`, `glossary.yaml` and `notebook.yaml`, checks them,
and writes one page with the design kit, the data and its own rendering
script inside. The page has no doctype, html, head or body tags, because the
artifact publisher adds them. It finds the kit through `FD_KIT` if that's set,
then the style plugin beside this one in the same checkout or install, so the
kit matches the script's version, then the newest style plugin under
`~/.claude/plugins/`, and downloads it from this repo's `main` if none is
there.

`tests/sample-repo/` is a made-up research repo for testing the script, with
threads and experiments in both modes. It isn't notebook content.
