---
name: design
description: Logan's default look for any page Claude designs for them, such as an artifact, report, dashboard, internal tool or mock-up, when the project has no design system or brand of its own. Read it before designing or restyling a page, and before choosing its fonts, colours or layout. A project's own design system or brand guide wins over it.
---

# Designing for me

The pages you make for me are for working, so my attention should go on what they say rather than on the page. My brief is that a page should feel great to use and be practical rather than eye-catching, while still looking good. Everything below serves that.

This is a default. A project's own design system or brand guide wins over it, so check for one first. The Grove, for example, has its own. When the page is an Artifact, the artifact-design skill's page contract still applies, and this skill decides the look wherever that contract leaves a choice. Where other design guidance pushes for a bold or distinctive aesthetic, follow this one for my pages.

Start from the two files beside this one. `references/base.css` holds the tokens and base styles, so copy it into the page and add only what the page needs. `references/example.html` is a finished page in this style, so copy its patterns rather than inventing new ones.

## Show what I need first

Each page answers one question, and the answer comes first. A results page opens with the result, and a status page opens with whether anything needs me. Everything after that is there so I can understand the answer, check it or act on it.

Bookkeeping goes in a single disclosure at the end of the page, called something plain like "Code, data and records". That covers IDs, costs, run names, raw configuration, audit trails and full tables of values. The disclosure remembers whether it was open, in local storage, because when I'm working in the detail I want it open on every page without asking twice.

What lets me check a result isn't bookkeeping, so it stays visible. That includes the method, the comparison that gives a number its meaning, sanity checks and real examples. Hiding those behind a click is the most expensive kind of tidying.

Pages should still make sense months later. Give every status a date ("Since 10 Nov", "Running since 17 Nov"), say why something was done, and say what changed afterwards.

Say each fact once. When the same information would appear on several pages, keep it in one place and generate the other views from it, because copies drift apart.

## Layout

A page is one typeset column on a plain background, with no cards, boxes or shadows. Text runs no wider than about 640px. Space does the separating, helped by the occasional 1px rule. One tinted panel on a page is fine for something that really is different in kind, such as a note on what happened since, but not more than one.

A margin column on the left, about 170px wide, holds plain-word labels for each section (Result, Method, Caveats), along with dates and statuses. Below about 860px the margin labels fold above their content. The labels are ordinary words in muted text. Don't use stylised run-in labels, small spaced capitals above headings, or bold label-colon pairs.

The header holds the page's name, at most one live status (such as "1 experiment running", as a link) and a few tabs. It sticks to the top on a desktop.

Titles say something specific. A section about which layer works best is titled "Which layer gives the best probe?", not "Results", and a list of things to do is titled by what they are.

These are the things that make a page look generated, so leave them out:

- identical rounded cards for every item;
- pills and badges on everything;
- small spaced-out capitals above headings;
- metadata strung together with middle dots;
- arrows or icons on ordinary links;
- emoji, gradients and decorative icons;
- a lone accent colour splashed on grey to look designed.

## Type

Albert Sans is the typeface for all text and headings, with its digits taken from Figtree, as on the research notebook. `base.css` sets this up. Fira Code is the monospace, and it's used only for IDs, hashes, code and commands, never for decoration or for numbers in prose. I've tried and rejected IBM Plex Sans with Plex Mono, Geist with Geist Mono, the Source family, Atkinson Hyperlegible, and Space Grotesk with Inter and JetBrains Mono.

Keep to a few sizes and three weights. The page title is 24px, an answer or claim that opens a page is 18 to 20px, body text is 16px, secondary text is 15px, and margin labels and captions are 14px. Weights are 400, 500 for titles of list rows, and 600 for headings and the occasional word that matters.

Numbers in columns and tables use tabular figures. Keep a value and its unit together with a non-breaking space, as in "n = 1,180" or "3 seeds". Use the same number of decimals for the same kind of figure everywhere.

## Colour

The palette is near-neutral: a white background, ink, a softer second ink, a muted grey for labels, and two greys for rules. A single accent colour, a deep teal, marks links and the current state, and nothing else. Status colours for good, warning and critical are kept for status, and always appear beside a word that says the same thing. Each chart series keeps its colour on every chart, so the same thing is always the same colour.

Dark mode gets its own chosen values rather than an automatic inversion. The tokens for both modes are in `base.css`.

## Links and lists

Text links are in the accent colour and underline on hover. An item in a list is one link: the whole row is clickable, and hovering anywhere on it underlines only its title. A row never contains a second link, because two targets in one row make the underline jump around and make taps ambiguous.

Lists of things put the date or status in the margin and the item's title on the first line, with one line of detail under it in the second ink colour.

## Charts

Load the dataviz skill for chart mechanics. On top of that, these are my conventions.

To compare a few categories, use a horizontal dot-and-range chart. The dot is the mean of the seeds, the line runs from the lowest seed to the highest, rows are sorted by value, and the values sit in a column on the right. A line over a numeric axis, such as layer or time, is a line chart.

Every main chart shows what makes its number mean something. Chance is a dashed line. Trivial baselines that could fake the effect, such as a classifier that only sees length, appear as hollow grey rows scored on the same test set, and so does a skyline when one exists. If there is no skyline, say so under the chart and say why.

A chart's title says what's measured against what, as in "AUROC by test set". Its caption gives n, the number of seeds and what the range shows, without repeating the method. Label series directly rather than with a legend when there are four or fewer. Hovering or tapping a mark shows its exact value. Draw charts at the container's real width, so text keeps its set size on a phone instead of shrinking with the drawing.

## Phones

Every page has to work at 390px wide. The margin labels fold above their content, the tabs take a row of their own, and tap targets are at least 44px tall. Charts redraw at the phone's width, with long labels wrapped onto two lines.

## Words on the page

The words follow my Clear writing style. Labels are plain words, things are called by the names I use, and the same thing has the same name everywhere. Anything that says "running", "now" or "yet" carries a date.

## Example: a status block

Templated:

```html
<div class="card shadow rounded-xl p-6">
  <div class="text-xs uppercase tracking-widest text-gray-400">Experiment status</div>
  <h3>Transfer test <span class="pill pill-green">✓ Complete</span></h3>
  <p>AUROC: <b>0.54</b> · n=212 · 3 seeds · A40</p>
  <a href="#">View details →</a>
</div>
```

Clear:

```html
<section class="mg sec">
  <div class="ml">16 Nov</div>
  <div class="mc">
    <a class="item" href="#">
      <span class="t">Does a probe trained on instructed lies detect sandbagging?</span>
      <p class="a"><b>No.</b> AUROC 0.54 vs chance 0.50 on sandbagging. 3 seeds.</p>
    </a>
  </div>
</section>
```

## How to work

Before calling a page done, look at screenshots of it at 1280px in light and dark mode and at 390px as a touch phone, and fix what you see. Check that the hover and disclosure states work.

When a choice is structural, such as how information is split between pages or what goes on the home page, build both options behind a temporary switch and compare them side by side, using a council if the choice is big. Settle the structure before polishing.

My taste wins over any reviewer's. When I make a call about the look, it becomes part of this style.
