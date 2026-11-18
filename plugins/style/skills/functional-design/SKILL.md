---
name: functional-design
description: Logan's default look for pages people work with, such as artifacts, reports, dashboards, internal tools, notebooks and mock-ups, when the project has no design system or brand of its own. Design that feels good and doesn't get in the way, rather than bold or eye-catching. Read it before designing or restyling a page, and before choosing its fonts, colours or layout. A project's own design system or brand guide wins over it.
---

# Functional design

This is my default for pages I work with, such as reports, dashboards, tools and research notebooks. It isn't a style for pages that have to sell something or stand out, so don't reach for bold or unusual choices to make a page memorable. It isn't bare minimalism either. A page of raw HTML, or one that only just works, misses this style as badly as a flashy one does. The aim is design that feels good to use and doesn't get in the way. Every choice is deliberate, and anything that doesn't help me read, check or act is left out.

Restraint is what makes emphasis work. On a plain white page with one accent and a few greys, a red word or a bold number stands out without effort, and colour coding can use many colours and still read clearly. Cards, tinted backgrounds and decorative colour use up that contrast, so when something does need to stand out, there's nothing left to make it stand out with. That's why this style has no cards and a small palette, and why boldness, when a page needs it, goes in one place.

A project's own design system or brand guide wins over this one. For an Artifact, the artifact-design skill's page contract still applies, and this skill decides the look wherever that contract leaves a choice. Where other design guidance asks for a distinctive aesthetic, follow this one for my pages.

## Start from the kit

Paste `references/base.css` and `references/base.js` into the page and add only what it needs. They set the fonts, colours, sizes, margin layout, lists, forms, tables, phone and print behaviour, the remembered disclosure and chart tooltips, and their comments say how to use each part. `references/example.html` is a finished page, so copy its patterns rather than inventing new ones. Starting from the kit is what keeps my pages consistent, because a description of a look drifts in a way a stylesheet doesn't.

## Show what I need first

Each page leads with what I came for. A results page opens with the result, a status page with whether anything needs me, and a tool with the thing I came to do. Everything after that helps me understand it, check it or act on it.

Bookkeeping is whatever the page's question isn't about, and it goes in one disclosure at the end, called something plain like "Code, data and records". On a results page that means IDs, costs, run names and raw configuration, but on a spending page costs are the subject and stay visible. The disclosure stays open once opened, so it's there on every page while I'm working in the detail.

What lets me check a result or a recommendation stays visible, because checking is the hard part of my work. For an experiment that's the method, the comparison that gives a number its meaning, sanity checks and real examples. For a recommendation it's the assumptions, prices with their source and date, and what would change the answer.

Say each fact once on a page, because every repeat is something I read twice. An opening answer may state a figure that a later section explains, but nothing else repeats it. When everything was read at the same moment, give that moment once near the top ("As of 18 Nov 14:20").

When something needs me, the page opens with it: "Needs you" in the margin in the critical colour, a sentence saying what's wrong and what it costs, and one link naming the action. The header status says the same in the same colour. When nothing needs me, the page says so with the time it checked, because an empty space doesn't tell me whether anything was checked.

## Layout

A page is one typeset column on a plain white background, with no cards, boxes, shadows or tinted panels. Prose stays under about 640px wide, because longer lines tire the eye, while tables and charts may use the full width. Space does the separating, helped by the occasional 1px rule.

A margin column on the left labels each section with a plain word (Result, Method, Caveats) and holds its date or status, so I can scan a page by its labels without them interrupting the reading. A section has a margin label or, on a page long enough to need headings, a heading, but not both. Titles say something specific, such as "Which layer gives the best probe?" rather than "Results", so I can tell I'm in the right place.

The header bar holds a short name, at most one live status, and tabs if the page has sibling views. A page with neither tabs nor a live status has no header bar, and its title starts the page.

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

Colour coding is where colour is spent. When colour tells things apart, such as the models being compared, the series in a chart or the categories in a list, it can use as many distinct colours as the content needs, because the plain page leaves room for them. The first three come from the kit's tokens, and further ones continue in the dataviz skill's categorical order. A thing keeps its colour everywhere it appears, in charts, keys and tables alike, so I learn it once. Something that is itself a status, such as money wasted on a pod left running, takes that status colour. Colour that codes nothing is decoration, so leave it out.

## Lists and actions

Each list item is one link: the whole row is clickable, and hovering anywhere on it underlines only its title. A row never holds a second link, because two targets in a row make taps ambiguous, and a list is all links or none, so I can tell which rows open something.

A one-word verdict that answers a row's question may open its sentence in bold, as in "**No.** AUROC 0.54 on sandbagging". A label never does, so don't start sentences with "Next:" or "Cost:".

A page has at most one button-styled action. Every other action is a link, which keeps the one button meaningful. Inputs update the page as I type, unless the action sends something somewhere.

An empty list says what being empty means ("No jobs since 12 Nov"), and a page of fetched data says when it was read. If a refresh fails, the page says so and keeps showing the last figures with their age, rather than a blank area or a spinner.

## Charts

Load the dataviz skill for chart mechanics. My conventions on top of it are these.

Use dots for a few values, with a line through each when its range matters, a line for a trend, and bars when totals or their parts matter. Sort categories best first, and label series directly when there are four or fewer.

Every main chart shows the reference that gives its number meaning, on the same scale, because a number alone can't tell me whether it's good. For an experiment that's chance as a dashed line, trivial baselines that could fake the effect, and a skyline when one exists, drawn as hollow grey rows. For other pages it might be last week's average, the free option or the budget. If the reference that matters doesn't exist, say so under the chart.

The title says what's measured against what ("AUROC by test set"), and the caption gives n and what each mark and range means. Draw charts at the container's real width, so text keeps its size on a phone.

## Words

The words follow my Clear writing style. Things are called by the names I use, the same thing has the same name everywhere, and anything that says "running", "now" or "yet" carries a date.

## Before calling it done

Run the check script, which tests the rules a program can test in a headless browser at desktop and phone widths, and fix every failure:

```bash
uv run --with playwright python <this skill>/scripts/check.py page.html --shots /tmp/shots
```

Then look at the screenshots it saves, at 1280px in light and dark and at 390px as a phone, because the script can't judge how a page looks. Check that hover, tap, focus and the disclosure work.

When I correct the look of a page, add the correction to this skill with its reason, and add a check to the script if a program could catch it.
