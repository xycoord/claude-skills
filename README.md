# claude-skills

Skills for Claude. This repo is a plugin marketplace: add it once to a
claude.ai account (Customize → Plugins → Add → Add marketplace →
`xycoord/claude-skills`, with **Sync automatically** on) and every Claude Code
session on that account loads its plugins from `main`.

## Plugins

| Plugin | Skills |
|---|---|
| `dev` | `/dev:council`: independent opinions on the same thing from several model families (Opus, Fable and GPT via the Codex CLI), then weighing them. `/dev:hill-climb`: improve something round by round against a fixed measure, judged by a council or a command, until a target. `/dev:pr-review`: get a branch to ready — review it in rounds with the built-in `/code-review`, fix the clear findings, brief the driver on the calls that need a person, and open the PR with a problem-first description. `/dev:verify`: try a web UI change in a real browser and hand over screenshots. `dev:steward` (not a command): how Claude looks after a PR it opened — answers, no check-ins, staying quiet. |

`pr-review`, `verify` and `steward` are general versions of the skills in
The-Grove-Notts/The-Grove-Database. Each steps aside when a repo has its own
skill of the same name in `.claude/skills/`, so a repo's own copy (with its
people, branches and scripts) always wins. They read the repo's `CLAUDE.md`,
`CONTRIBUTING` and `CODEOWNERS` for the base branch, the checks and who owns
what; standing review rules go in the repo's `.claude/pr-review-rules.md`.

The council's GPT judge runs through `plugins/dev/skills/council/scripts/codex_agent.py`,
which needs the Codex CLI signed in to a ChatGPT subscription; its docstring
has the setup.

## Not yet in a plugin

The research skills at the top level (`task-discussion`,
`autonomous-execution`, `proactive-continuation`, `handoff`, `research-*`,
`plot`) predate the marketplace and aren't installed by it. They're due an
update, and will move into a plugin of their own when they get one.

## Layout

- `.claude-plugin/marketplace.json` lists the plugins.
- `plugins/<plugin>/.claude-plugin/plugin.json`, with no `version`, so each
  account follows commits.
- `plugins/<plugin>/skills/<skill>/SKILL.md`, with any `scripts/` or
  `references/` beside it.

Run `claude plugin validate .` before pushing.
