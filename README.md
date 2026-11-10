# claude-skills

Skills for Claude. This repo is a plugin marketplace: add it once to a
claude.ai account (Customize → Plugins → Add → Add marketplace →
`xycoord/claude-skills`, with **Sync automatically** on) and every Claude Code
session on that account loads its plugins from `main`.

## Plugins

| Plugin | Skills |
|---|---|
| `dev` | `/dev:council`: independent opinions on the same thing from several model families (Opus, Fable and GPT via the Codex CLI), then weighing them. `/dev:hill-climb`: improve something round by round against a fixed measure, judged by a council or a command, until a target. |

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
