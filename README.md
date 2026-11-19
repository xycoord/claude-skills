# claude-skills

Skills for Claude. This repo is a plugin marketplace: add it once to a
claude.ai account (Customize → Plugins → Add → Add marketplace →
`xycoord/claude-skills`, with **Sync automatically** on) and every Claude Code
session on that account loads its plugins from `main`.

## Plugins

| Plugin | Skills |
|---|---|
| `research` | `research:experiment`: run one experiment from question to result: check it hasn't been done, write the plan and prediction before anything runs, run it in the session or on a GPU pod, prove the code on a tiny run, watch the first results, then hand over to `record` and propose what comes next. `research:compute`: research compute on Runpod, with the prepaid balance as the only hard limit. The few rules that protect money and data; dev pods with a movable deadline; jobs (`scripts/job.sh`) that run a pinned commit, upload results to Hugging Face, can report on a PR, and delete their own pod however they end; Runpod facts that are hard to find out. `research:record`: writing up research in the notebook and publishing it. The file format for experiments and threads (`references/format.md`), the writing rules for testing a hypothesis and looking for one (`references/writing-rules.md`), and `scripts/build_notebook.py`, which builds the notebook page from the research repo for its pinned artifact. |
| `style` | `style:functional-design`: Logan's default look for pages people work with, such as reports, dashboards, tools and notebooks, when a project has no design system of its own. Design that feels good and doesn't get in the way, rather than bold: one typeset column, a margin for labels, a small palette so emphasis means something, and a kit (`base.css`, `base.js`, an example page) to start from. |
| `dev` | `/dev:council`: independent opinions on the same thing from several model families (Opus, Fable and GPT via the Codex CLI), then weighing them. `/dev:hill-climb`: improve something round by round against a fixed measure, judged by a council or a command, until a target. `/dev:pr-review`: get a branch to ready — review it in rounds with the built-in `/code-review`, fix the clear findings, brief the driver on the calls that need a person, and open the PR with a problem-first description. `/dev:verify`: try a web UI change in a real browser and hand over screenshots. `dev:steward` (not a command): how Claude looks after a PR it opened — answers, no check-ins, staying quiet. |

`pr-review`, `verify` and `steward` are general versions of the skills in
The-Grove-Notts/The-Grove-Database. Each steps aside when a repo has its own
skill of the same name in `.claude/skills/`, so a repo's own copy (with its
people, branches and scripts) always wins. They read the repo's `CLAUDE.md`
and `CONTRIBUTING` for the checks, the base branch (an open PR's base wins;
with no docs to go on, the default branch) and who owns what (a written rule naming a
person; `CODEOWNERS` doesn't count, since GitHub already requests those
reviews). Standing review rules go in the repo's `.claude/pr-review-rules.md`.
`/dev:pr-review` runs by itself only on work headed for a PR; otherwise
Claude offers it in a line.

The council's GPT judge runs through `plugins/dev/skills/council/scripts/codex_agent.py`,
which needs the Codex CLI signed in to a ChatGPT subscription; its docstring
has the setup.

## Writing style

`output-styles/clear.md` is the "Clear" output style: how Claude should write to Logan in every session. It leads with the point, says less but in full sentences, keeps prose as the default, stays quiet while working, and asks each question once, at the end. It isn't part of a plugin, because it reaches each place a different way:

- **Claude Code on a machine:** link it into place, then set it as the default in `~/.claude/settings.json` with `"outputStyle": "Clear"`. Local sessions then follow whatever this checkout holds.

  ```bash
  mkdir -p ~/.claude/output-styles && ln -sf "$PWD/output-styles/clear.md" ~/.claude/output-styles/clear.md
  ```

- **Claude Code in the cloud:** paste `output-styles/cloud-setup.sh` into the setup script of a cloud environment that only you use. It downloads the style from `main` when the environment is built, so a change arrives within about a week, or sooner if you change the date in the script. Anthropic documents a setup script writing `~/.claude/CLAUDE.md` for personal preferences, not an output style, but a session tested on 18 Nov 2026 loaded the style this way.
- **claude.ai chat:** paste the text of `clear.md`, without the header block at the top, into your profile preferences.

## Retired skills

The older research skills that once sat at the top level of this repo (`task-discussion`,
`autonomous-execution`, `proactive-continuation`, `handoff`, `plot` and the `research-*`
set) were retired on 18 Nov 2026 without being installed by the marketplace. They're in
the history before that change, for reference when writing the `experiment` skill.
The notebook's writing rules, drafted in `drafts/`, became the `record` skill on 19 Nov 2026,
and the lie-detection glossary drafted beside them moved to the research repo's `glossary.yaml`.

## Layout

- `.claude-plugin/marketplace.json` lists the plugins.
- `plugins/<plugin>/.claude-plugin/plugin.json`, with no `version`, so each
  account follows commits.
- `plugins/<plugin>/skills/<skill>/SKILL.md`, with any `scripts/` or
  `references/` beside it.

Run `claude plugin validate .` before pushing.
