#!/usr/bin/env python3
"""Run one Antigravity CLI (Gemini) agent, read-only, on the Google AI plan
agy is signed in with: a second opinion from another model family, for a
council judge, a plan or a diff.

    python3 <this skill>/scripts/gemini_agent.py --prompt PROMPT --out DIR [IMAGE ...]
        [--model gemini-4-neon] [--effort low|medium|high|xhigh] [--cwd DIR]
        [--timeout SECONDS]

The images are copied into a fresh, empty folder and agy starts there, so only
the prompt and the images are in front of it; it opens them with its file
reader, so the prompt should name them. Reads outside that folder can't be
approved in a headless run and end it without an answer. --cwd starts it
somewhere else instead (a review that has to read the repo). The images are
copied into one folder and cited by name, so their file names must be
distinct.

Read-only comes from permission rules passed for this run only: every file
write, shell command, URL fetch, browser and MCP call is denied, and a denied
call fails rather than asking. agy's own web search can't be turned off, so
the judge may search the web, as the Claude judges can.

Writes DIR/reply.md (its answer), DIR/events.jsonl (agy's event stream) and
DIR/meta.json: the model and effort each generation in the conversation was
served with (from agy's conversation store, not the model's own claim; it can't see a
reroute on the server's side) and whether that matched the request
(`model_verified`), the script's own result, token usage, seconds, any
actions agy denied, and the plan's usage windows (`five_hour` and `weekly` for
the model's group, each used_percent with its reset time), read after the
call. Measured on AI Pro, whose Antigravity limits are Google's entry tier
(Nov 2026): a review of two repo files at high effort (~16k tokens in, ~9k
out, about 90 seconds) didn't move either window by a whole percent.

Setup, once per cloud container (agy isn't kept between containers): install
agy (curl -fsSL https://antigravity.google/cli/install.sh | bash, which puts
it in ~/.local/bin), then sign in by running agy in a terminal (tmux in a
cloud session): choose Google OAuth, the person opens the link, signs in and
pastes the code back. It refuses a Google Cloud project or API-key sign-in,
and runs with API keys taken out of its environment, the Gemini API provider
switched off and AI credits switched off, so it can only use the plan's
quota. Written against agy 1.5.13.

Exit codes: 0 done · 1 failed (including a timeout, an empty answer, or a run
ended by an action it couldn't ask about) · 2 bad arguments · 3 agy missing,
not signed in, or not signed in to the Google AI plan · 4 a usage or rate limit stopped it · 5 the answer came
from a different model or effort than asked, or the conversation store
couldn't confirm which: treat the judge as not run. agy's answer is written to
reply.rejected.md, renamed reply.md only on success, so a failed run's answer
can't be read as good. Never fall back to another model: the caller reports
the failure instead.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LIMIT_RE = re.compile(r"usage limit|rate limit|too many requests|\b429\b|quota|"
                      r"resource.?exhausted", re.I)
OUTPUTS = ("reply.md", "reply.rejected.md", "events.jsonl", "meta.json")
AGY_HOME = Path.home() / ".gemini" / "antigravity-cli"
# Only for this run, never saved. Deny beats any allow rule in the person's
# own settings, and a denied call fails instead of waiting for approval.
SETTINGS = {
    "agentMode": "",                # default mode: plan mode answers with a plan file
    "toolPermission": "request-review",
    "allowNonWorkspaceAccess": False,
    "modelProvider": "",            # never the Gemini API, which bills per token
    "useG1Credits": False,          # stop at the plan's quota, never spend credits
    "disableSlashCommands": True,
    "permissions": {"deny": [
        "write_file(*)", "command(*)", "read_url(*)", "execute_url(*)",
        "download_url(*)", "mcp(*)",
    ]},
}
WINDOW_NAMES = {"five hour": "five_hour", "weekly": "weekly"}


def fail(code: int, message: str) -> int:
    print(f"gemini_agent: {message}", file=sys.stderr)
    return code


def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # already gone


def agy_env() -> dict:
    return {k: v for k, v in os.environ.items()
            if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
                         "GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS")}


def run_quick(agy: str, args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run([agy, *args], cwd=cwd, env=agy_env(), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return 1, f"agy {' '.join(args)} didn't answer within 90s"
    return done.returncode, done.stdout + done.stderr


def model_labels(listing: str) -> dict[str, str]:
    """`agy models` lines are `<id>\\t<label>`."""
    labels = {}
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            labels[parts[0].strip()] = parts[1].strip()
    return labels


def usage_windows(report: str, group: str) -> dict:
    """`agy -p /usage` lines are `<group>\\t<window> Limit Remaining\\t<n>%\\t<reset>`."""
    windows = {}
    for line in report.splitlines():
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 4 or parts[0] != group:
            continue
        name = parts[1].lower().replace(" limit remaining", "").strip()
        match = re.fullmatch(r"(\d+(?:\.\d+)?)%", parts[2])
        if not match:
            continue
        windows[WINDOW_NAMES.get(name, name.replace(" ", "_"))] = {
            "used_percent": round(100 - float(match.group(1)), 1),
            "resets_at": parts[3],
        }
    return windows


def string_fields(data: bytes, tag: bytes) -> list[str]:
    """The short printable strings stored under one protobuf field tag."""
    found = []
    for match in re.finditer(re.escape(tag) + rb"([\x01-\x7f])", data):
        value = data[match.end():match.end() + match.group(1)[0]]
        if len(value) == match.group(1)[0] and all(32 <= b < 127 for b in value):
            found.append(value.decode())
    return found


def ran_models(conversation_id: str) -> list[dict] | None:
    """The model each generation of the conversation was served by, and its label.

    Read from two fields of each generation's record, not from the text in it:
    the record also holds the prompt and every file the agent read, so a model
    name mentioned in the work being judged must not count. Field 19 is the
    model the backend ran (`gemini-4-neon`), field 21 its label with the
    effort (`Gemini 4 Neon (High)`). Found from agy 1.5.13's records.
    """
    store = AGY_HOME / "conversations" / f"{conversation_id}.db"
    if not store.is_file():
        return None
    try:
        with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as db:
            rows = db.execute("select data from gen_metadata order by idx").fetchall()
    except sqlite3.Error:
        return None
    model_name = re.compile(r"(gemini|claude|gpt)[\w.-]*")
    label_name = re.compile(r"(Gemini|Claude|GPT)[ -].*\)")
    return [{"models": sorted({v for v in string_fields(data or b"", b"\x9a\x01")
                               if model_name.fullmatch(v)}),
             "labels": sorted({v for v in string_fields(data or b"", b"\xaa\x01")
                               if label_name.fullmatch(v)})}
            for (data,) in rows]


def plan_sign_in() -> str | None:
    """Why agy might not bill the AI plan, or None when it's signed in to it."""
    if not (AGY_HOME / "antigravity-oauth-token").is_file():
        return "agy has no Google sign-in token"
    try:
        saved = json.loads((AGY_HOME / "settings.json").read_text(encoding="utf-8") or "{}")
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as error:
        return f"agy's settings.json can't be read ({error})"
    if saved.get("gcp"):
        return "agy is signed in to a Google Cloud project, which bills that project"
    if saved.get("modelProvider"):
        return f"agy is set to the {saved['modelProvider']} provider, which bills per token"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default="gemini-4-neon")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh"])
    parser.add_argument("--cwd", type=Path, help="run here instead of an empty folder")
    parser.add_argument("--timeout", type=int, default=900, help="seconds before giving up")
    parser.add_argument("images", nargs="*", type=Path)
    args = parser.parse_args()
    # agy starts in another folder, so a relative path would resolve there.
    args.prompt = args.prompt.resolve()
    args.out = args.out.resolve()
    args.images = [i.resolve() for i in args.images]
    if args.cwd:
        args.cwd = args.cwd.resolve()

    outputs = [args.out / name for name in OUTPUTS]
    if any(p in outputs for p in [args.prompt, *args.images]):
        return fail(2, f"an input is one of the files this run writes in {args.out}")
    # Clear the last run's files first, so a run that stops early can't leave
    # an earlier answer or usage figures to be read as this one's.
    args.out.mkdir(parents=True, exist_ok=True)
    for path in outputs:
        path.unlink(missing_ok=True)

    if not args.prompt.is_file():
        return fail(2, f"no prompt at {args.prompt}")
    if args.cwd and not args.cwd.is_dir():
        return fail(2, f"no folder at {args.cwd}")
    missing = [str(i) for i in args.images if not i.is_file()]
    if missing:
        return fail(2, f"missing images: {', '.join(missing)}")
    names = [i.name for i in args.images]
    clashes = sorted({n for n in names if names.count(n) > 1})
    if clashes:
        return fail(2, f"images share a name ({', '.join(clashes)}): give each a unique name")
    agy = shutil.which("agy") or shutil.which(str(Path.home() / ".local" / "bin" / "agy"))
    if agy is None:
        return fail(3, "agy isn't installed: see this script's docstring")

    model_id = f"{args.model}-{args.effort}"
    with tempfile.TemporaryDirectory(prefix="gemini-agent-check-") as check_dir:
        code, listing = run_quick(agy, ["models"], Path(check_dir))
    if "sign in" in listing.lower():
        return fail(3, "agy isn't signed in: run agy in a terminal and choose Google OAuth "
                       "(the person signs in and pastes the code)")
    if code != 0:
        return fail(1, f"agy models failed: {listing.strip()[-800:]}")
    off_plan = plan_sign_in()
    if off_plan:
        return fail(3, f"{off_plan}: sign agy in with Google OAuth instead")
    labels = model_labels(listing)
    if model_id not in labels:
        return fail(2, f"{model_id} isn't offered on this account; agy models lists: "
                       f"{', '.join(sorted(labels)) or 'nothing'}")
    want_label = labels[model_id]

    reply = args.out / "reply.rejected.md"
    timed_out = False
    with tempfile.TemporaryDirectory(prefix="gemini-agent-") as stage:
        stage_dir = Path(stage)
        for image in args.images:
            shutil.copyfile(image, stage_dir / image.name)
        # The prompt goes in on stdin, one turn, so its length isn't bound by
        # the command line's.
        command = [
            agy, "--input-format", "stream-json", "--output-format", "stream-json",
            "--model", model_id, "--settings", json.dumps(SETTINGS),
            "--disable-slash-commands",
        ]
        # Run elsewhere, the images' folder is outside its workspace, and a
        # read there would need an approval a headless run can't get.
        if args.cwd and args.images:
            command += ["--add-dir", str(stage_dir)]
        turn = json.dumps({"event": "user", "message": {
            "content": args.prompt.read_text(encoding="utf-8")}}) + "\n"
        started = time.monotonic()
        # Its own process group, so a timeout kills agy and anything it started.
        proc = subprocess.Popen(
            command, cwd=args.cwd or stage_dir, start_new_session=True, env=agy_env(),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        # Stopping this script stops agy too, rather than leaving it running
        # on the plan's quota.
        def stopped(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stopped)
        try:
            stdout, stderr = proc.communicate(turn, timeout=args.timeout)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_group(proc)
            stdout, stderr = proc.communicate()
            returncode = None
        except KeyboardInterrupt:
            kill_group(proc)
            return fail(1, "stopped before agy finished")
        except BaseException:
            kill_group(proc)
            raise
        seconds = round(time.monotonic() - started, 1)

    (args.out / "events.jsonl").write_text(stdout, encoding="utf-8")
    result, init = None, {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") == "init":
            init = event.get("init") or {}
        elif event.get("event") == "result":
            result = event.get("result") or {}
    result = result or {}
    answer = (result.get("response") or "").strip()
    if answer:
        reply.write_text(answer + "\n", encoding="utf-8")

    meta = {"requested_model": model_id, "requested_label": want_label,
            "seconds": seconds, "usage": result.get("usage"), "exit": returncode,
            "timed_out": timed_out, "status": result.get("status"),
            "conversation_id": result.get("conversation_id"),
            "permission_mode": init.get("permission_mode"),
            "denied_actions": result.get("denied_actions") or []}
    generations = ran_models(meta["conversation_id"]) if meta["conversation_id"] else None
    meta["ran_models"] = generations
    # Every generation that names a model must name the asked-for one, at the
    # asked-for effort, and at least one must name it.
    named = [g for g in (generations or []) if g["models"] or g["labels"]]
    meta["model_verified"] = bool(
        named and init.get("model") == model_id
        and all(g["models"] in ([], [args.model]) and g["labels"] in ([], [want_label])
                for g in named)
        and any(g["labels"] == [want_label] for g in named)
        and any(g["models"] == [args.model] for g in named)
    )
    with tempfile.TemporaryDirectory(prefix="gemini-agent-check-") as check_dir:
        code, report = run_quick(agy, ["-p", "/usage"], Path(check_dir))
    if code == 0:
        meta["usage_windows"] = usage_windows(report, "Gemini Models")

    def finish(code: int, message: str = "") -> int:
        meta["result"] = code
        if message:
            meta["reason"] = message
        (args.out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        if code == 0:
            reply.rename(args.out / "reply.md")
        return fail(code, message) if code else 0

    problem = ((result.get("error") or "") + "\n" + stderr).strip()
    if timed_out:
        return finish(1, f"agy didn't finish within {args.timeout}s")
    if returncode != 0 or result.get("status") != "SUCCESS" or not answer:
        limit = LIMIT_RE.search(result.get("error") or stderr)
        if not answer and meta["denied_actions"] and not limit:
            return finish(1, "agy stopped at an action it couldn't ask about ("
                             + ", ".join(a.get("action", "?") for a in meta["denied_actions"])
                             + "): keep what it needs in its folder, or use --cwd")
        return finish(4 if limit else 1,
                      f"agy failed (exit {returncode}): {problem[-800:] or 'no answer'}")
    if not meta["model_verified"]:
        return finish(5, f"asked for {want_label}; the conversation store says "
                         f"{meta['ran_models'] or 'nothing'}: treat as not run")
    finish(0)
    print(json.dumps({k: meta.get(k) for k in
                      ("requested_model", "model_verified", "seconds", "usage", "usage_windows")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
