---
name: functional-design
description: Logan's default look for pages people work with, such as artifacts, reports, dashboards, internal tools, notebooks and mock-ups, when the project has no design system or brand of its own. Design that feels good and doesn't get in the way, rather than bold or eye-catching. Read it before designing or restyling a page, and before choosing its fonts, colours or layout. A project's own design system or brand guide wins over it.
---

# Functional design

This is my default for pages I work with, such as reports, dashboards, tools and research notebooks. It isn't a style for pages that have to sell something or stand out, so don't reach for bold or unusual choices to make a page memorable. It isn't bare minimalism either. A page of raw HTML, or one that only just works, misses this style as badly as a flashy one does. The aim is design that feels good to use and doesn't get in the way. Every choice is deliberate, and anything that doesn't help me read, check or act is left out.

Restraint is what makes emphasis work. On a plain white page with one accent and a few greys, a red word or a bold number stands out without effort, and a chart can use many colours and still read clearly. Cards, tinted backgrounds and decorative colour use up that contrast, so when something does need to stand out, there's nothing left to make it stand out with. That's why this style has no cards and a small palette, and why boldness, when a page needs it, should go in one place.

A project's own design system or brand guide wins over this one. When the page is an Artifact, the artifact-design skill's page contract still applies, and this skill decides the look wherever that contract leaves a choice. Where other design guidance asks for a distinctive aesthetic or aesthetic risk, follow this one for my pages.

## Start from the kit

`references/base.css` holds the tokens and styles, and `references/base.js` holds the small scripts every page needs, so paste both into the page and add only what it needs. `references/example.html` is a finished page in this style, so copy its patterns rather than inventing new ones. Starting from the kit is what keeps my pages consistent, because a description of a look drifts in a way a stylesheet doesn't.

## Show what I need first

Each page leads with what I came for. A results page opens with the result, a status page opens with whether anything needs me, and a tool opens with the thing I came to do. Everything after that is there so I can understand it, check it or act on it.

Bookkeeping is whatever the page's question isn't about, and it goes in one disclosure at the end, called something plain like "Code, data and records". On a results page that means IDs, costs, run names, raw configuration and full tables of values, but on a spending page costs are the subject and stay visible. The disclosure stays open once I've opened it, because when I'm working in the detail I want it there on every page.

What lets me check a result or a recommendation isn't bookkeeping, so it stays visible. For an experiment that's the method, the comparison that gives a number its meaning, sanity checks and real examples. For a recommendation it's the assumptions, prices with their source and date, and what would change the answer. For a forecast it's the arithmetic. Checking is the hard part of my work, so it shouldn't cost a click.

Say each fact once on a page, because every repeat is something I read twice. An opening answer may state a figure that a later section explains, but nothing else repeats it. When everything on a page was read at the same moment, give that moment once near the top ("As of 18 Nov 14:20") and date only what differs.

## When something needs me

A page that can need me opens with it. The margin says "Needs you" in the critical colour, with when it started. The opening sentence says what is wrong and what it costs, and one link names the action, such as "Delete the pod in Runpod". The header status says the same words in the same colour. Several things go in one list, most costly first. When nothing needs me, the page says so in one sentence with the time it was checked, because a blank space doesn't tell me whether anything was checked.

## Layout

A page is one typeset column on a plain white background, with no cards, boxes, shadows or tinted panels. Prose runs no wider than about 640px, because longer lines are tiring to read, while tables and charts may use the full content width. Space does the separating, helped by the occasional 1px rule.

A margin column on the left, about 170px wide, labels each section with a plain word (Result, Method, Caveats) and holds its date or status. It lets me scan a page by its labels without the labels interrupting the reading. A section has a margin label or, on a page long enough to need navigating, a heading, but not both stacked. Below 860px the margin folds above its content, with a label and its date on one line.

The header bar holds the page's short name, at most one live status, and tabs when the page has sibling views. A page that stands alone, with no tabs and no live status, has no header bar, and its title starts the page. Titles say something specific, such as "Which layer gives the best probe?" rather than "Results", because a specific title tells me whether I'm in the right place. A page longer than about four screens gets a short contents line under its opening answer.

These are the marks of a generated page, and each one costs attention without carrying information, so leave them out:

- cards around every item, which turn one page into many small ones;
- pills and badges, which shout every status at the same volume;
- small spaced-out capitals above headings, which label what the heading already says;
- metadata strung together with middle dots, which reads as a code to decipher;
- arrows or icons on ordinary links, which add noise to something already marked by colour;
- emoji, gradients and decorative icons;
- big "stat tiles" for key numbers, when a sentence that starts with the number at the lead size ("$41.37 left.") says more;
- Claude's own house look of a cream background, serif headings and a terracotta accent, which suits an editorial page but not a working one.

## Type

Albert Sans is the typeface for all text and headings, with its digits taken from Figtree. Fira Code is the monospace, used only for IDs, hashes, code and commands, because monospace elsewhere is decoration. `base.css` sets both up, and pages don't substitute other families.

There are seven sizes, and each has one job: 24px for the page title, 20px for the opening answer, 17px for headings, 16px for body text, 15px for secondary text, 14px for margin labels and captions, and 13px for the footer and table headings. Weights are 400, 500 for the titles of list rows, and 600 for headings and the occasional word that matters. A small, fixed scale is what lets a size or weight change mean something.

Numbers in columns use tabular figures so they line up. Keep a value and its unit together with a non-breaking space, as in "n = 1,180", and use the same number of decimals for the same kind of figure everywhere. Dates are written "18 Nov", with the year added when it isn't the current one or the page is meant to last. Times use the 24-hour clock, and a page of live data names its time zone once.

## Colour

The palette is a white background, ink, a softer second ink, a muted grey for labels, two greys for rules, and one accent, a deep teal. The accent marks links, the current tab and the one primary button, and nothing else, so that teal always means "you can act on this".

Status colours for good, warning and critical are kept for status, and always sit on a word that says the same thing, so the meaning survives for colour-blind readers and in print. Colour the word, not the whole sentence. When a chart series is itself a status, such as money wasted on a pod left running, draw it in that status colour so it matches the words beside it.

Charts are where colour is spent. The first three series use the tokens in `base.css`, and beyond that, use the dataviz skill's categorical palette in its fixed order. The white page is what lets many series stay distinct, which is one more reason the background stays plain. Each series keeps its colour on every chart, so the same thing is always the same colour.

Dark mode has its own chosen values rather than an automatic inversion, and they're in `base.css`.

## Links, lists and actions

Text links are in the accent colour and underline on hover. An item in a list is one link: the whole row is clickable, and hovering anywhere on it underlines only its title. A row never contains a second link, because two targets in one row make the underline jump and taps ambiguous. A list is either all links or all plain rows, so I can tell which rows open something.

A row has its title on the first line and a short line of detail under it. When a list is the page's main content, dates go in the margin. Inside a labelled section, they go in a narrow column beside the rows.

A one-word verdict that answers a row's question may open its sentence in bold, as in "**No.** AUROC 0.54 on sandbagging". A label never does, so don't start sentences with "Next:" or "Cost:", and don't open every row in a list with a bold word.

A page has at most one button-styled action, in solid accent. Every other action is a link, which keeps the one button meaningful.

## Forms, states and tables

Inputs have a label above them and units in the label ("Added a year, GB"). Changing an input updates the page straight away, unless the action sends something somewhere. An error sits under its field and says what to type instead, and what I entered stays put.

An empty list says what being empty means ("No jobs since 12 Nov"). A page of fetched data says when it was read, and if a refresh fails it says so, says how old the figures are and keeps showing them. Never leave a blank area or a spinner without words.

Right-align numbers in tables, put units in the column heading, and mark the cell that matters with weight rather than colour. On a phone, a table of phrases turns into one block per row and a table of numbers scrolls sideways, which the `stack` and `tablewrap` classes in `base.css` handle. A command I might copy goes on its own line in Fira Code and scrolls rather than wraps.

## Charts

Load the dataviz skill for chart mechanics. On top of that, these are my conventions.

Choose the chart for the comparison. Use dots for a few values, with a line through each dot when its range matters. Use a line for a trend over time or another numeric axis, and bars when totals or what they're made of matter. Sort categories best first, and label series directly rather than with a legend when there are four or fewer.

Every main chart shows the reference that gives its number meaning, on the same scale, because a number alone can't tell me whether it's good. For an experiment that's chance as a dashed line, trivial baselines that could fake the effect, and a skyline when one exists, with the baselines and skyline as hollow grey rows. For other pages it might be last week's average, the free option or the budget. If the reference that would matter doesn't exist, say so under the chart.

A chart's title says what's measured against what, as in "AUROC by test set". Its caption gives n and says what each mark and range means. Hovering, tapping or focusing a mark shows its exact value, which `base.js` handles for anything with a `data-tip` attribute. Draw charts at the container's real width, so text keeps its size on a phone instead of shrinking with the drawing.

## Phones and access

Every page works at 390px wide, with tap targets at least 44px tall apart from links inside sentences, and nothing scrolling sideways. Use native links, buttons, headings, labels and table headers for their jobs. Everything works from the keyboard with a visible focus ring, and anything shown on hover is also shown on focus or tap. Reports and decision pages print cleanly, which `base.css` handles.

## Words on the page

The words follow my Clear writing style. Labels are plain words, things are called by the names I use, and the same thing has the same name everywhere. Anything that says "running", "now" or "yet" carries a date.

## Example of what to avoid

This is the templated version of a status block. The same content in this style is the History row in `example.html`.

```html
<div class="card shadow rounded-xl p-6">
  <div class="text-xs uppercase tracking-widest text-gray-400">Experiment status</div>
  <h3>Transfer test <span class="pill pill-green">✓ Complete</span></h3>
  <p>AUROC: <b>0.54</b> · n=212 · 3 seeds · A40</p>
  <a href="#">View details →</a>
</div>
```

## Before calling it done

Look at screenshots of the page at 1280px in light and dark mode, and at 390px as a touch phone, and fix what you see. Check that hover, tap, focus and the disclosure work.

When I correct the look of a page, add the correction to this skill with its reason.
