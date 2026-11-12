---
name: verify
description: Try a web UI change the way its users would before handing it over — start the app, set up the situation the change is about, go through the changed workflow in a real browser, look at the screenshots, fix what's wrong, and send the person the screenshots. Use whenever a change alters what a web app shows (a page, a component, or an API a page shows), and before changing existing web UI, to see how it behaves now. Not for CLIs, libraries or desktop apps. In a repo with its own verify skill, use that one instead.
---

# /verify — try it before handing it over

**First:** if the repo has its own copy at
`<root>/.claude/skills/verify/SKILL.md` (`<root>` is `git rev-parse
--show-toplevel` in the checkout being changed), follow that instead and
stop reading this one. Not a browser app (a CLI, a TUI, a desktop app)?
Use the built-in `run` skill, or run the command and show its output.

The UI mistakes that reach people are ones a single go through the feature
would have caught: they reply with a screenshot and "this is bad". So before
a UI change is handed over, Claude uses it — in a browser, against a running
app, as its users would — and looks at what it sees. This replaces asking
the person for "steps to check": run the steps yourself.

## 1. Start the app

Find how the repo runs locally, in this order: a script or skill the repo
keeps for exactly this (`.claude/scripts/`, `scripts/`), the root
`CLAUDE.md`, the README, then the `Makefile`, `package.json` scripts
(`dev`, `start`) or a Docker Compose file. Prefer the dev server (it reloads
on edit, so iterating is edit → re-run the check) over a production build.

- **Run it in the background** (`run_in_background`) and read its output
  for the port it really listens on: many servers move to the next free
  port.
- **Sample data only.** Use the repo's seed or fixtures; never point the
  app at a production database or real customer data, and never let it
  write to a real outside service: turn live writes off, turn sandbox or
  test modes on, and leave live credentials out of its environment.
- **Can't get it up?** Missing services (a database, a cache) can often be
  started in the container; a missing secret can't be invented. Try for a
  few minutes, then say exactly what blocks it and what you checked
  instead. Don't hand over a UI change as tried when it wasn't.
- If the person may want to open the app themselves, tell their app the
  port with `report_preview_port` (where that tool exists). Not for a
  server only your check uses.
- **A server from an earlier turn may be gone** (the container restarted
  or was replaced). Before each run of the check, make sure the server
  this check started, from this checkout, is still running (its
  background task, or its process), and start it again if not. Something
  else answering on that port isn't it.

**Changing existing UI?** Run the check once before you touch it, for the
"before" — how it behaves now, on the same scenario — and hand over before
and after side by side.

## 2. Write the check

A short Playwright script in the scratchpad (in a cloud container
`require('playwright')` / `from playwright.sync_api import ...` work from
any folder and `chromium.launch()` needs no options; don't install
another). Keep it re-runnable: the same script is the before, the after and
every round in between.

- **Set up the situation the change is about**, through the app's API, a
  seed command or the database: the record with the awkward state, the
  empty list, the long name. Give what you create distinctive names, so
  data from earlier runs doesn't confuse this one.
- **Sign in as the person who'd use it** (the repo's seed or docs name the
  test logins; a plain user rather than an admin when that's who meets the
  change).
- **Go through the changed workflow as they would** — click, type, the
  awkward values, undo, the empty state, an error, a long name. Not just
  the happy path the code was written for.
- **Screenshot every step that shows something new**, at desktop width in
  light mode and as a phone in dark mode if the app has one
  (`color_scheme` on the context). Take phones as touch phones (a
  Playwright device such as `iPhone 13`, or `has_touch` and `is_mobile`
  with a 390×844 viewport): at phone width a desktop context shows mouse
  sizes and hover styles, and skips `(pointer: coarse)` rules. A device sets its own scale;
  otherwise `device_scale_factor` 1 for checks only you read, 2 for the
  ones the person will see.
- **Collect console errors, page errors and failed requests**
  (`page.on("console")`, `page.on("pageerror")`, `page.on("requestfailed")`
  and responses ≥ 400) and print them at the end; treat any as a finding.

## 3. Look

Read every screenshot (the Read tool shows the image). Judge it the way its
users will meet it, with the repo's own UI conventions (its `CLAUDE.md`
files, a design or style guide skill if one applies): does it read clearly
at a glance, is anything cramped, cut off, misaligned, or unreadable in dark
mode or on a phone, does the wording say what happens in the user's terms?
Then fix what you found and run the check again. Repeat until there's
nothing left you'd want the person to have to point out.

## 4. Hand over

- Send the person the screenshots (`SendUserFile` where it exists;
  otherwise give the files' absolute paths), the few that show the
  change best, with the steps the check went through, one line each, and
  anything you saw but deliberately left.
- Say which files show the change best. `/pr-review` puts those on the PR
  once the PR exists and the fixes are in.
- Stop the servers you started when you're done with them.

Unit and integration tests are the repo's checks' job, not this skill's.
