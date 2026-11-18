---
name: design
description: Logan's default look for any page Claude designs for them, such as an artifact, report, dashboard, internal tool or mock-up, when the project has no design system or brand of its own. Read it before designing or restyling a page, and before choosing its fonts, colours or layout. A project's own design system or brand guide wins over it.
---

# Designing for me

The pages you make for me are for working, so my attention should go on what they say rather than on the page. My brief is that a page should feel great to use and be practical rather than eye-catching, while still looking good. Everything below serves that.

This is a default, so a project's own design system or brand guide wins over it. When the page is an Artifact, the artifact-design skill's page contract still applies, and this skill decides the look wherever that contract leaves a choice. Where other design guidance pushes for a bold or distinctive aesthetic, follow this one for my pages.

Start from the files beside this one. `references/base.css` holds the tokens and styles, and `references/base.js` holds the small scripts every page needs, so paste both into the page and add only what it needs. `references/example.html` is a finished page in this style, so copy its patterns rather than inventing new ones.

## Show what I need first

Each page leads with what I came for. A results page opens with the result, a status page opens with whether anything needs me, and a tool opens with the thing I came to do. Everything after that is there so I can understand it, check it or act on it.

Bookkeeping is whatever the page's question isn't about, and it goes in one disclosure at the end, called something plain like "Code, data and records". On a results page that means IDs, costs, run names, raw configuration and full tables of values. On a spending page, costs are the subject and stay visible. The disclosure remembers whether it was open, so that when I'm working in the detail it stays open. `base.js` does this with one fixed storage key, which carries across pages on the same site.

What lets me check a result or a recommendation isn't bookkeeping, so it stays visible. For an experiment that means the method, the comparison that gives a number its meaning, sanity checks and real examples. For a recommendation it means the assumptions as a list I can check, prices with their source and date, and what would change the answer. For a forecast it means the arithmetic behind it.

Say each fact once on a page. An opening answer may state a figure that a later section explains, but nothing else repeats it. When everything on a page was read at the same moment, give that moment once near the top ("As of 18 Nov 14:20") and date only what differs.

## When something needs me

A page that can need me opens with it. The margin says "Needs you" in the critical colour, with when it started. The opening sentence says what is wrong and what it costs, and one link names the action, such as "Delete the pod in Runpod". The header status says the same words in the same colour. Several things go in one list, most costly first. When nothing needs me, the page says so in one sentence with the time it was checked, such as "Nothing needs you. Checked 14:20."

## Layout

A page is one typeset column on a plain background, with no cards, boxes, shadows or tinted panels. Prose runs no wider than about 640px, while tables and charts may use the full content width. Space does the separating, helped by the occasional 1px rule.

A margin column on the left, about 170px wide, labels each section with a plain word (Result, Method, Caveats) and holds its date or status. The labels are ordinary words in muted text. A section has a margin label, not a margin label and a heading as well. Only a page long enough to need navigating gets headings, and then the margin holds just the section's date or status. Below 860px the margin folds above its content, with a label and its date on one line.

The header bar holds the page's short name, at most one live status, and tabs when the page has sibling views. It sticks to the top on a desktop. A page that stands alone, with no tabs and no live status, has no header bar, and its title starts the page. The title says what this page is about, rather than repeating the site's name.

Titles say something specific. A section about which layer works best is titled "Which layer gives the best probe?", not "Results".

A page with more than about four screens of content gets a short contents line under its opening answer, linking to each section.

These are the things that make a page look generated, so leave them out:

- cards for every item;
- pills and badges;
- small spaced-out capitals above headings;
- metadata strung together with middle dots;
- arrows or icons on ordinary links;
- emoji, gradients and decorative icons;
- big "stat tiles" for key numbers. A number I open the page for starts its sentence at the lead size instead ("$41.37 left.").

## Type

Albert Sans is the typeface for all text and headings, with its digits taken from Figtree. Fira Code is the monospace, used only for IDs, hashes, code and commands. `base.css` sets both up, and pages don't substitute other families.

The sizes are 24px for the page title, 20px for the opening answer, 17px for headings, 16px for body text, 15px for secondary text, 14px for margin labels and captions, and 13px for the footer and table headings. Chart ticks are 12px. Weights are 400, 500 for the titles of list rows, and 600 for headings and the occasional word that matters.

Numbers in columns and tables use tabular figures. Keep a value and its unit together with a non-breaking space, as in "n = 1,180" or "3 seeds". Use the same number of decimals for the same kind of figure everywhere.

Dates are written as "18 Nov". Add the year when the date is outside the current year, or on a page meant to last, such as a report. Times use the 24-hour clock, and a page of live data names its time zone once.

## Colour

The palette is near-neutral: a white background, ink, a softer second ink, a muted grey for labels, and two greys for rules. A single accent colour, a deep teal, marks links, the current tab and the one primary button, and nothing else.

Status colours for good, warning and critical are kept for status, and always sit beside a word that says the same thing. Colour the word, not the whole sentence. When a chart series is itself a status, such as money wasted on a pod left running, draw it in that status colour so it matches the words beside it.

Each chart series keeps its colour on every chart, so the same thing is always the same colour. If a chart needs more than three series, fold the minor ones into "Other" or split it into small charts rather than adding colours.

Dark mode gets its own chosen values rather than an automatic inversion. The tokens for both modes are in `base.css`.

## Links, lists and actions

Text links are in the accent colour and underline on hover. An item in a list is one link: the whole row is clickable, and hovering anywhere on it underlines only its title. A row never contains a second link. A list is either all links or all plain rows, so I can tell which rows open something.

A row has its title on the first line, in weight 500, and a short line of detail under it in the second ink colour. When a list is the page's main content, dates go in the margin. Inside a labelled section, they go in a narrow column beside the rows.

A one-word verdict that answers a row's question may open its sentence in bold, as in "**No.** AUROC 0.54 on sandbagging". A label never does, so don't write "Next:" or "Cost:" at the start of sentences, and don't open every row in a list with a bold word.

A page has at most one button-styled action, the primary one, in solid accent. Every other action is a link.

## Forms

An input has a muted 14px label above it, and is 44px tall with a 1px border, 16px text and the page's font. Units and limits go in the label ("Added a year, GB"). Inputs sit on a regular grid. Changing an input updates the page straight away, without a Calculate or Submit button, unless the action sends something somewhere. An error sits under its field, in the critical colour, and says what to type instead. The values I entered stay put after an error.

## States

An empty list says in a sentence what being empty means, such as "No jobs since 12 Nov". A page that shows fetched data gives the time it was read near the top. If a refresh fails, the page says so in the warning colour, says how old the figures are, and keeps showing the last good figures. Never show a blank area, or a spinner without words.

## Tables

Right-align numbers, put units in the column heading, and mark the row or cell that matters with weight, not colour. A table that is the page's main comparison uses the `main` class, which sets it at body size in ink.

On a phone, a table whose cells are phrases becomes one block per row, with each cell labelled by its column, using the `stack` class in `base.css`. A table of numbers instead scrolls sideways inside `.tablewrap`, with its first column fixed.

## Code and commands

A command I might copy goes on its own line in Fira Code, and scrolls sideways rather than wrapping.

## Charts

Load the dataviz skill for chart mechanics. On top of that, these are my conventions.

Choose the chart for the comparison. Use dots for a few values, with a line through each dot when its range matters. Use a line for a trend over a numeric axis such as time or layer, and bars when totals or what they're made of matter. Sort categories best first. Label series directly rather than with a legend when there are four or fewer.

Every main chart shows the reference that gives its number meaning, drawn on the same scale. For an experiment that means chance as a dashed line, trivial baselines that could fake the effect, and a skyline when one exists, with the baselines and skyline as hollow grey rows scored on the same test set. For other pages it might be last week's average, the free option or the budget. If the reference that would matter doesn't exist, say so under the chart and say why.

A chart's title says what's measured against what, as in "AUROC by test set". Its caption gives n and says what each mark and range means. For an experiment, the dot is the mean of the seeds and the line runs from the lowest seed to the highest. Hovering, tapping or focusing a mark shows its exact value, which `base.js` handles for any element with a `data-tip` attribute. Draw charts at the container's real width, so text keeps its set size on a phone instead of shrinking with the drawing, and keep labels, totals and values that matter on the phone version.

## Phones and access

Every page has to work at 390px wide. The margin labels fold above their content, the tabs take a row of their own, and tap targets are at least 44px tall, apart from links inside sentences. Charts redraw at the phone's width, with long labels wrapped onto two lines.

Use native links, buttons, headings, labels and table headers for their jobs. Everything works from the keyboard with a visible focus ring, and anything shown on hover is also shown on focus or tap. A chart's role and label describe it, and its exact values are in a table in the bookkeeping disclosure.

## Printing

Reports and decision pages print cleanly. `base.css` handles it: the header stops sticking, the bookkeeping disclosure opens, and links print in ink.

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

Look at screenshots of the page at 1280px in light and dark mode, and at 390px as a touch phone, and fix what you see. Check that hover, tap, focus and the disclosure work, and that nothing scrolls sideways on the phone.

When I make a call about the look, add it to this skill.
