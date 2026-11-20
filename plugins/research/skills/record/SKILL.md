---
name: record
description: Write up research in the notebook and publish it — the files that hold an experiment's record and a thread's findings, Next and History, the rules for what they say, how the notebook page is built from them and published to its pinned artifact, and the Drafts page that shows open pull requests before they merge. Use when writing up an experiment (planned, running or finished), when a result changes a thread's findings, Next or History, when starting a new research question, when redrawing a figure of results already in the record, after pushing to a pull request that changes the notebook's files, and after any such change merges to main, to publish the notebook.
---

# Recording research

The research repo is the source of truth. Results are written as files in it,
and the notebook, one page published as a pinned claude.ai artifact, is built
from those files by `scripts/build_notebook.py` beside this file. **The page is
never edited by hand**, by you or anyone else: change the files and rebuild,
because a hand edit is lost at the next build and leaves the page out of step
with the repo.

The notebook shows only `main`. A second pinned page, **Drafts**, shows each
open pull request as the notebook would look once it merges, built by the same
script. The person looks at work there while it's in progress and gives
feedback, so merging is when a result is accepted, not when it's first seen.

## What goes where

Two kinds of file hold everything, and each fact is written once, in the file
that owns it.

- **An experiment** (`experiments/<id>/README.md`, with figures in `figs/`) is
  the fixed record of one run: why it was run, what was compared, the result,
  the method, checks and examples. Write it when the run is planned, update it
  while it runs, and finish it when the run ends. Until its PR merges, the
  write-up is a draft that changes with the person's feedback. After that it
  doesn't change, except for a dated `since` line when later work changes how
  it reads and the thread's History doesn't already say so, and for redrawn
  figures (below).
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
  script. Show each result in the form that makes it clearest, whether or
  not the kit has it. Where a kit view fits, a figure is the arguments of one
  call into its charts.js or interp.js, so read those files' comments. Where
  none does, such as a new way of looking at a model's internals or a plot
  the paper you're reproducing used, write a custom view (`format.md` says
  how), following the design skill's principles for charts and for views of
  model internals. A custom view that proves useful can join the kit later.

## Redrawing figures

A figure can be redrawn without a new experiment when the person wants a
clearer or different view of a result already in the record, finished or not.
A redraw changes only how numbers that were already computed are shown: the
view, the layout, labels and colours, which computed numbers sit side by side,
or a custom view's code. It needs no plan, tiny run or launch log, because
nothing new is computed from the data.

- Work on a branch named `claude/fig-<slug>` with its own PR, or on the
  experiment's own branch if its PR is still open. Push each version and
  publish the Drafts page, so the person sees it within a minute or two.
  Several experiments' figures can be redrawn in one PR.
- Change the experiment's text only where it describes the figure, such as a
  caption, so the two still match.
- A redraw must leave the result reading the same. Don't drop a condition,
  baseline, control or error bar the result depends on, and don't change an
  axis or scale in a way that changes what the figure seems to say. If the
  person asks for a change that would, say so and ask how to record it.
- If it needs a number the record doesn't already have, such as a new metric,
  slice, threshold or another pass over the data, it's an analysis, and the
  `experiment` skill applies.

## Checking the files

Before pushing a change to the notebook's files, build the page from your
branch to check them: `uv run <this skill>/scripts/build_notebook.py <repo> -o <scratchpad>/notebook.html`.
It stops on anything it can't build, such as a finding citing an experiment
that doesn't exist or a figure with an unknown view, and names the file. Fix
every error. Look at the warnings too, since each is something a reader would
miss.

## Publishing

There are two pages, each at an address in `notebook.yaml`: the notebook
(`artifact`) and the Drafts page (`drafts`). Each is rebuilt in full every
time, so publishing never merges two versions of a page by hand.

### The notebook

Publish from `main` only, whenever a change to the notebook's files reaches
it, so the page always matches `main`. After a merge, the session that owns
the PR publishes: it's subscribed to the PR, so the merge wakes it. After an
experiment's plan or status is pushed straight to `main` (the `experiment`
skill), the session that pushed it publishes straight after. Several pushes
within a few minutes of each other can share one publish after the last.

1. Bring a checkout of `main` up to date: in the `experiment` skill's
   detached copy, `git fetch` and `git checkout --detach origin/main`; in a
   checkout on the `main` branch, `git pull`.
2. Build with `--publish`: `uv run <this skill>/scripts/build_notebook.py <repo> -o <scratchpad>/notebook.html --publish`.
   It refuses unless the checkout is clean and matches `origin/main`. A build
   without `--publish` is marked as a preview of its branch, so never publish
   one to the notebook's address.
3. Read the artifact at `notebook.yaml`'s `artifact` address with the
   Artifact tool (`action: "read"`). A publish to an artifact this session
   hasn't read is refused, so the read registers the live version. Don't
   open the saved copy of the page it writes, because the page you publish is
   rebuilt from `main` and needs nothing from the old one.
4. Publish the built file to that address (`url` set to it).

If the publish is refused because another session published first, update
the checkout as in step 1, rebuild and publish again. The rebuilt page holds
both sessions' work, because both are in `main`. Never merge two versions of
the HTML by hand.

### The Drafts page

Publish it whenever the person should see work that isn't on `main` yet:
- after each push to a branch whose open PR changes the notebook's files,
  such as a write-up, a revision after feedback or a redrawn figure;
- after a PR that changed them merges or is closed, so it drops off the page;
- after opening such a PR.

Several pushes within a few minutes of each other can share one publish after
the last.

1. Push first. The page is built from each branch's latest commit on GitHub,
   not from your checkout, so an unpushed commit doesn't show.
2. List the research repo's open PRs as JSON, with each one's `number`,
   `title` and `branch`, in `<scratchpad>/prs.json`. `gh pr list --state open
   --json number,title,headRefName` writes it as it is; with the GitHub tools,
   list the open PRs and write that shape.
3. Build from any checkout of the research repo:
   `uv run <this skill>/scripts/build_notebook.py <repo> -o <scratchpad>/drafts.html --drafts <scratchpad>/prs.json`.
   It fetches each branch itself and leaves the checkout as it was. It shows
   only PRs that change the notebook's files, and a branch whose files don't
   build is listed with its errors instead of stopping the page.
4. Read the artifact at `notebook.yaml`'s `drafts` address, then publish the
   built file to it, as for the notebook.

If the publish is refused because another session published first, build and
publish again. The rebuilt page holds both sessions' work, because it's built
from every open PR.

When you tell the person about a draft, give the Drafts page's address and
name the experiment or figure. The page opens on the list of drafts, each a
click from its changes.

### When the notebook is behind `main`

The session that owns a PR publishes after it merges, but if that session has
ended, the notebook falls behind `main`. So before publishing the Drafts page,
and at the start of an experiment, check. Read the notebook's artifact as in
step 3 of *The notebook*: the read saves a copy of the page and names its
file. Find the commit it was built from with
`grep -o '"source":{"publish":true,"commit":"[0-9a-f]*"' <saved file>`,
without opening the file. If `git diff --quiet <that commit> origin/main --
threads experiments glossary.yaml notebook.yaml` reports a difference, publish
the notebook.

### Creating the pages

Each page's artifact is created once, when the research repo is set up, and
its address is committed in `notebook.yaml`. If `artifact` or `drafts` is
ever empty, don't create one: a second session doing the same would make a
second page. Tell the person instead.

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
