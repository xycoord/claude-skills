---
name: functional-design
description: Logan's default look for pages people work with, such as artifacts, reports, dashboards, internal tools, notebooks and mock-ups, when the project has no design system or brand of its own. Design that feels good and doesn't get in the way, rather than bold or eye-catching. Read it before designing or restyling a page, and before choosing its fonts, colours or layout. A project's own design system or brand guide wins over it.
---

# Functional design

This is my default for pages I work with, such as reports, dashboards, tools and research notebooks. It isn't a style for pages that have to sell something or stand out, so don't reach for bold or unusual choices to make a page memorable. It isn't bare minimalism either. A page of raw HTML, or one that only just works, misses this style as badly as a flashy one does. The aim is design that feels good to use and doesn't get in the way. Every choice is deliberate, and anything that doesn't help me read, check or act is left out.

Restraint is what makes emphasis work. On a plain white page with one accent and a few greys, a red word or a bold number stands out without effort, and colour coding can use many colours and still read clearly. Cards, tinted backgrounds and decorative colour use up that contrast, so when something does need to stand out, there's nothing left to make it stand out with. That's why this style has no cards and a small palette, and why boldness, when a page needs it, goes in one place.

A project's own design system or brand guide wins over this one. For an Artifact, the artifact-design skill's page contract still applies, and this skill decides the look wherever that contract leaves a choice. Where other design guidance asks for a distinctive aesthetic, follow this one for my pages.

## Start from the kit

Paste `references/base.css` and `references/base.js` into the page, `references/charts.js` if it has charts, and `references/interp.js` after it for views of model internals, then add only what the page needs. They set the fonts, colours, sizes, margin layout, lists, forms, tables, diagrams, charts, phone and print behaviour, the remembered disclosure and value tooltips, and their comments say how to use each part. `references/example.html` is a finished page, so copy its patterns rather than inventing new ones. Starting from the kit is what keeps my pages consistent, because a description of a look drifts in a way a stylesheet doesn't.

## Show what I need first

Each page leads with what I came for. A results page opens with the result, a status page with whether anything needs me, and a tool with the thing I came to do. Everything after that helps me understand it, check it or act on it.

A results page keeps the same order every time, so I know where to look: the answer, what was compared and how its data was built, the result charts, the method, the checks, examples, confidence and caveats, and what to try next. What was compared comes before the results because it introduces the things being compared and their colours, so the charts read at a glance. Show it as a diagram or table rather than prose where you can, because I can decide to skip a diagram in a moment, while skipping prose means reading it first. A brief that lists these in another order is telling you what to include, not where to put it.

Bookkeeping is whatever the page's question isn't about, and it goes in one disclosure at the end, called something plain like "Code, data and records". On a results page that means IDs, costs, run names and raw configuration, but on a spending page costs are the subject and stay visible. The disclosure stays open once opened, so it's there on every page while I'm working in the detail.

What lets me check a result or a recommendation stays visible, because checking is the hard part of my work. For an experiment that's the method, the comparison that gives a number its meaning, sanity checks and real examples. For a recommendation it's the assumptions, prices with their source and date, and what would change the answer.

Say each fact once on a page, because every repeat is something I read twice. An opening answer may state a figure that a later section explains, but nothing else repeats it. When everything was read at the same moment, give that moment once near the top ("As of 18 Nov 14:20").

When something needs me, the page opens with it: "Needs you" in the margin in the critical colour, a sentence saying what's wrong and what it costs, and one link naming the action. The header status says the same in the same colour. When nothing needs me, the page says so with the time it checked, because an empty space doesn't tell me whether anything was checked.

## Layout

A page is one typeset column on a plain white background, with no cards, boxes, shadows or tinted panels. Prose stays under about 640px wide, because longer lines tire the eye. That limit is for reading line by line, so it doesn't apply to figures. A diagram, or a chart or table that needs the room, may use the full width of the page, margin column included, with the `bleed` class in `base.css`, while its caption stays at text width. Keep to those two widths rather than giving each figure its own, so the page doesn't end at a different edge every few inches. Space does the separating, helped by the occasional 1px rule.

A margin column on the left labels each section with a plain word (Result, Method, Caveats) and holds its date or status, so I can scan a page by its labels without them interrupting the reading. A section has a margin label or, on a page long enough to need headings, a heading, but not both. Titles say something specific, such as "Which layer gives the best probe?" rather than "Results", so I can tell I'm in the right place.

The header bar holds a short name, at most one live status, and tabs if the page has sibling views. A page with neither tabs nor a live status has no header bar, and its title starts the page.

An artifact has no back button, so every page or view reached from another one shows the way back at the top. Usually that's the header's name linking home, or a short line naming the page above. The link goes back through the history when there is one, so I return to where I was on the page I came from, and opens the parent page when there isn't. Within one artifact, separate views are better as hash views of a single page than as separate files, because each view then has an address I can link to and the way back stays inside the page.

These are the marks of a generated page, and each costs attention without carrying information, so leave them out:

- cards around every item, which turn one page into many small ones;
- pills and badges, which shout every status at the same volume;
- small spaced-out capitals above headings, which label what the heading already says;
- metadata strung together with middle dots, which reads as a code to decipher;
- arrows or icons on ordinary links, which are already marked by colour;
- emoji, gradients and decorative icons;
- big "stat tiles", when a sentence that starts with the number ("$41.37 left.") says more;
- Claude's own house look of a cream background, serif headings and a terracotta accent, which suits an editorial page but not a working one.

## Type and colour

Albert Sans is for all text, with its digits taken from Figtree. Fira Code is only for IDs, hashes, code and commands, because monospace anywhere else is decoration. Pages don't substitute other families. The kit's seven sizes and three weights each have one job, and keeping to them is what lets a change of size or weight mean something.

The palette is white, two inks, a muted grey for labels, two greys for rules, and one accent, a deep teal. The accent marks links, the current tab and the one primary button, so teal always means "you can act on this". Status colours for good, warning and critical are only for status, always on a word that says the same thing, so the meaning survives for colour-blind readers and in print. Colour the word rather than the sentence.

Colour coding is where colour is spent. When colour tells things apart, such as the models being compared, the series in a chart or the categories in a list, it can use as many distinct colours as the content needs, because the plain page leaves room for them. They come from the kit's eight series tokens, in order. Three of them are pale against white, so whatever they code also gets a direct label or a table of values. A thing keeps its colour everywhere it appears, in charts, tables and diagrams alike, so I learn it once. Outside a chart, its colour shows as a small dot before its name, from the `sw` class in `base.css`. Something that is itself a status, such as money wasted on a pod left running, takes that status colour. Colour that codes nothing is decoration, so leave it out.

## Lists and actions

Each list item is one link: the whole row is clickable, and hovering anywhere on it underlines only its title. A row never holds a second link, because two targets in a row make taps ambiguous, and a list is all links or none, so I can tell which rows open something.

A one-word verdict that answers a row's question may open its sentence in bold, as in "**No.** AUROC 0.54 on sandbagging". It stays in ink when the answer is reassuring, and takes the warning or critical colour only when the check found a problem, so colour in a list of checks always means "look here". A label never does, so don't start sentences with "Next:" or "Cost:".

A page has at most one button-styled action. Every other action is a link, which keeps the one button meaningful. Inputs update the page as I type, unless the action sends something somewhere.

An empty list says what being empty means ("No jobs since 12 Nov"), and a page of fetched data says when it was read. If a refresh fails, the page says so and keeps showing the last figures with their age, rather than a blank area or a spinner.

## Charts

Draw charts with `references/charts.js`, which `references/charts.html` shows in use. It has the four kinds my pages need: dots with ranges for a few values, lines for a trend over time or another numeric axis, stacked bars for totals and what they're made of, and a two-class score distribution. Each draws at its container's real width so text keeps its size on a phone, labels series directly, and shows exact values on hover, tap or focus. Using it keeps every chart looking like the same hand drew it.

When a chart needs something the kit doesn't draw, load the dataviz skill and follow its method. This skill supplies the settings that method asks a design system for: the series colours in `base.css`, which are its own validated order, the status colours, and white and near-black as the two backgrounds. Its rules then apply as written, such as one axis per chart and colour that follows the thing rather than its rank.

Every main chart shows the reference that gives its number meaning, on the same scale, because a number alone can't tell me whether it's good. For an experiment that's chance as a dashed line, trivial baselines that could fake the effect, and a skyline when one exists, drawn as hollow grey rows under the heading "References", each labelled with what it is. For other pages it might be last week's average, the free option or the budget. If the reference that matters doesn't exist, say so under the chart.

The title says what's measured against what ("AUROC by test set"), and the caption gives n and what each mark and range means. Sort categories best first, except where several charts sit side by side: there each compared thing keeps the same row in every chart, with `keepOrder`, so I only learn the order once.

## Diagrams

A diagram shows flow, and a table makes comparisons, so a page can need both for the same things. How three training sets are built from shared sources is a diagram, and what each set contains side by side is a table. Put the key numbers in the diagram's boxes as well, so it supports a rough comparison on its own. A plain sequence of steps reads better as a list, like the method flow in `example.html`, so a diagram earns its place when the structure branches, joins or loops. Then the boxes are allowed, because in a diagram they carry the structure. They use 1px strokes in the rule grey, with no fills or coloured edges. A box for a colour-coded thing gets the same colour key as everywhere else, a small dot before its name from the `sw` class, because coloured stripes down the side of a box are another mark of a generated page. Labels are plain words in the page font at 13px, with a muted second line for detail, and arrows are simple. `base.css` styles an `svg.diagram` this way, and `charts.html` has an example. Give the drawing its natural size, so its text stays at 13px, inside a `.tablewrap` so a narrow window can scroll it. For the mechanics of drawing one, load the artifact-diagramming skill.

## Views of model internals

My research is AI safety work on what happens inside models, and its most useful views often aren't standard charts. `references/interp.js` draws the established ones, and `references/interp.html` shows each in use: values over text (token highlights), a feature's top-activating examples, heatmaps over two axes (attention, or a probe's score by layer and token), a lens explorer for the logit lens, the J-lens or any tuned lens (a grid of each layer's top token at each position, the full readout for a selected cell, and pinned tokens' ranks through the layers), and attribution graphs. I also expect to need views nobody has designed yet, so these principles matter more than the list.

- Say what the unit is, whether a token, a feature, a head or a layer, because the unit decides the layout.
- Encode a value by its kind. A signed value, for or against something, runs from blue through the page colour to red, so zero is nothing. A magnitude runs from the page colour to violet, a different hue, so it's never mistaken for one side of a signed value. Every view carries its key, and shows each exact value on hover or focus.
- Views shown together share one scale, because colours on different scales can't be compared.
- Over text, a value is a pale tint behind ink-coloured words, so the text stays readable.
- Monospace marks a token as a token. In prose, write a token in monospace rather than in quotes, keeping its leading space inside, as in "the model predicts ` Austin`". In views, set tokens shown as units in monospace too: lens cells, readout lists, axis labels and pinned tokens. Running text that's read for meaning, such as a response with token highlights, stays in the body font. Don't draw visible marks for spaces, because they're noise. `IV.tok()` in `interp.js` and the `tok` class set a token.
- Every mark leads back to the raw data behind it, one step away.
- Here colour is data, not decoration, so the rule against tinted backgrounds doesn't apply. Mark the view's container `data-viz`, which the check script exempts.
- Build a new kind of view as a prototype on real data, and iterate on it with me. Only once it has proved useful does it join the kit.

## Words

The words on a page follow my Clear writing style. When you're running as a subagent without it, read it from `~/.claude/output-styles/clear.md` before writing the page's text. Things are called by the names I use, the same thing has the same name everywhere, and anything that says "running", "now" or "yet" carries a date.

## Before calling it done

I read these pages on a laptop and almost never on a phone, so design for the desktop. A page should still fit a phone's width without breaking, and the kit handles that, but don't spend effort on phone-specific layouts.

Run the check script, which tests the rules a program can test in a headless browser, and fix every failure:

```bash
uv run --with playwright python <this skill>/scripts/check.py page.html --shots /tmp/shots
```

Then look at the screenshots it saves, at 1280px in light and dark, because the script can't judge how a page looks. Glance at the phone one only to see that nothing is broken. Check that hover, focus and the disclosure work.

When I correct the look of a page, add the correction to this skill with its reason, and add a check to the script if a program could catch it.
