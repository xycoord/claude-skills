#!/bin/bash
# Installs the "Clear" writing style in a Claude Code cloud session and makes it the default output style.
# Paste this into the setup script of a cloud environment that only you use.
#
# It downloads the style from this repo's main branch. A cloud environment runs its setup script once
# and caches the result, rebuilding when the script changes or after about seven days. So a change to
# the style reaches cloud sessions within a week. To send it sooner, change the date below and save the
# environment.
#
# Last forced refresh: 2026-11-18
set -uo pipefail

url="${CLEAR_STYLE_URL:-https://raw.githubusercontent.com/xycoord/claude-skills/main/output-styles/clear.md}"
dir="$HOME/.claude/output-styles"
mkdir -p "$dir"

# Only install a file that downloaded fully and is the style. If GitHub can't be reached, sessions
# start with Claude Code's default style and the rest of the setup carries on.
if curl -fsSL --retry 2 --max-time 20 "$url" -o "$dir/clear.md.part" && grep -q '^name: Clear$' "$dir/clear.md.part"; then
  mv "$dir/clear.md.part" "$dir/clear.md"
  python3 - <<'PY'
import json, os
path = os.path.expanduser("~/.claude/settings.json")
settings = {}
if os.path.exists(path):
    with open(path) as f:
        settings = json.load(f)
settings["outputStyle"] = "Clear"
with open(path, "w") as f:
    json.dump(settings, f, indent=2)
PY
else
  rm -f "$dir/clear.md.part"
  echo "Couldn't download the Clear style from $url, so sessions will use the default style." >&2
fi
exit 0
