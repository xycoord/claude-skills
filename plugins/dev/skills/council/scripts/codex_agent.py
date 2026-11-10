#!/usr/bin/env python3
"""Run one Codex (GPT) agent, read-only, on the ChatGPT subscription Codex is
signed in with: a second opinion from another model family, for a council
judge, a plan or a diff.

    python3 <this skill>/scripts/codex_agent.py --prompt PROMPT --out DIR [IMAGE ...]
        [--model gpt-6.1-sol] [--effort low|medium|high|xhigh] [--cwd DIR]
        [--timeout SECONDS]

The images are copied into a fresh, empty folder and Codex starts there, so
only the prompt and the images are in front of it. Codex's read-only sandbox
blocks writes, not reads: never put a path to a run folder or earlier answers
in the prompt. --cwd starts it somewhere else instead (a review that has to
read the repo), still read-only. The images are copied into one folder and
cited by name, so their file names must be distinct.

Writes DIR/reply.md (its answer), DIR/events.jsonl (Codex's event stream) and
DIR/meta.json: the model and effort Codex ran the turn with (from its session
log, not the model's own claim; it can't see a reroute on the server's side)
and whether that matched the request (`model_verified`), the script's own
result, token usage, seconds, and the subscription's usage windows
(`five_hour` and `weekly`, each used_percent with its reset time), so callers
can budget. The windows lag one call: they count the calls before this one.
Measured on Plus (Nov 2026): one judgement of 30 screenshots at high effort
(~60k tokens in, ~5k out, about 2.5 minutes) took roughly 1-2% of the
five-hour window.

Setup, once per cloud container (Codex isn't kept between containers):
npm install -g @openai/codex, then codex login --device-auth in the
background; the person approves the link and code on their phone. It runs
with the user config ignored and API keys taken out of its environment, and
refuses an API-key login, so it can only bill the subscription. Written
against codex-cli 0.167.

Exit codes: 0 done · 1 failed (including a timeout or an empty answer) · 2 bad
arguments · 3 Codex missing, not signed in, or not on the ChatGPT
subscription · 4 a usage or rate limit stopped it · 5 the answer came from a
different model or effort than asked, or the session log couldn't confirm
which: treat the judge as not run. Codex writes its answer to
reply.rejected.md, renamed reply.md only on success, so a failed run's answer
can't be read as good. Never fall
back to another model: the caller reports the failure instead.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LIMIT_RE = re.compile(r"usage limit|rate limit|too many requests|\b429\b|quota", re.I)
WINDOW_NAMES = {300: "five_hour", 10080: "weekly"}
OUTPUTS = ("reply.md", "reply.rejected.md", "events.jsonl", "meta.json")


def fail(code: int, message: str) -> int:
    print(f"codex_agent: {message}", file=sys.stderr)
    return code


def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # already gone


def session_log(thread_id: str) -> Path | None:
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    hits = sorted((home / "sessions").rglob(f"rollout-*{thread_id}.jsonl"))
    return hits[-1] if hits else None


def read_session(path: Path) -> dict:
    """The model and effort the session ran, and its last usage windows."""
    model = effort = None
    limits = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = entry.get("payload") or {}
        if entry.get("type") == "turn_context":
            model = payload.get("model", model)
            settings = (payload.get("collaboration_mode") or {}).get("settings") or {}
            effort = settings.get("reasoning_effort") or payload.get("effort") or effort
        if payload.get("type") == "token_count" and payload.get("rate_limits"):
            limits = payload["rate_limits"]
    windows = {}
    for window in (limits or {}).values():
        if not isinstance(window, dict) or not window.get("window_minutes"):
            continue
        minutes = window["window_minutes"]
        windows[WINDOW_NAMES.get(minutes, f"{minutes}_minutes")] = {
            "used_percent": window.get("used_percent"),
            "window_minutes": minutes,
            "resets_at": window.get("resets_at"),
        }
    return {"model": model, "effort": effort, "usage_windows": windows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default="gpt-6.1-sol")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh"])
    parser.add_argument("--cwd", type=Path, help="run here instead of an empty folder")
    parser.add_argument("--timeout", type=int, default=900, help="seconds before giving up")
    parser.add_argument("images", nargs="*", type=Path)
    args = parser.parse_args()
    # Codex starts in another folder, so a relative path would resolve there:
    # the reply was written nowhere and the verdict lost.
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
    if shutil.which("codex") is None:
        return fail(3, "Codex isn't installed: npm install -g @openai/codex")
    try:
        status = subprocess.run(["codex", "login", "status"], capture_output=True, text=True,
                                timeout=60)
    except subprocess.TimeoutExpired:
        return fail(3, "codex login status didn't answer within 60s")
    said = status.stdout + status.stderr
    if status.returncode != 0 or "Logged in" not in said:
        return fail(3, "Codex isn't signed in: codex login --device-auth (the person approves it)")
    if not re.search(r"Logged in using ChatGPT", said):
        return fail(3, "Codex is signed in with an API key, not the ChatGPT subscription")

    # Written under the rejected name, and renamed only once the run checks
    # out, so no way of stopping can leave an unchecked answer as reply.md.
    reply = args.out / "reply.rejected.md"
    timed_out = False
    with tempfile.TemporaryDirectory(prefix="codex-agent-") as stage:
        stage_dir = Path(stage)
        staged = []
        for image in args.images:
            target = stage_dir / image.name
            shutil.copyfile(image, target)
            staged.append(target)
        # The user config is ignored, so no provider set there can turn this
        # into an API-billed run; "-" (the prompt from stdin) comes before the
        # images, since -i takes several values and would swallow it.
        command = [
            "codex", "exec", "--skip-git-repo-check", "--ignore-user-config",
            "-s", "read-only", "-m", args.model,
            "-c", f"model_reasoning_effort={args.effort}",
            "--json", "-o", str(reply), "-",
        ]
        for image in staged:
            command += ["-i", str(image)]
        env = {k: v for k, v in os.environ.items()
               if k not in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")}
        started = time.monotonic()
        # Its own process group: npm's codex is a launcher that starts the
        # real binary, so a timeout has to kill the group, or the binary
        # keeps the pipes open and the wait never ends.
        proc = subprocess.Popen(
            command, cwd=args.cwd or stage_dir, start_new_session=True, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        # Stopping this script (a timeout, a SIGTERM, Ctrl-C) stops Codex too,
        # rather than leaving it running on the subscription.
        def stopped(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stopped)
        try:
            stdout, stderr = proc.communicate(args.prompt.read_text(encoding="utf-8"),
                                              timeout=args.timeout)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_group(proc)
            stdout, stderr = proc.communicate()
            returncode = None
        except KeyboardInterrupt:
            kill_group(proc)
            return fail(1, "stopped before Codex finished")
        except BaseException:
            kill_group(proc)
            raise
        seconds = round(time.monotonic() - started, 1)

    (args.out / "events.jsonl").write_text(stdout, encoding="utf-8")
    thread_id, usage, errors, turn_failed = None, None, [], False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        elif kind == "turn.completed":
            usage = event.get("usage")
        elif kind in ("error", "turn.failed"):
            errors.append(json.dumps(event))
            turn_failed = turn_failed or kind == "turn.failed"

    meta = {"requested_model": args.model, "requested_effort": args.effort,
            "seconds": seconds, "usage": usage, "exit": returncode, "timed_out": timed_out}
    log = session_log(thread_id) if thread_id else None
    if log:
        meta.update(read_session(log))
        meta["session_log"] = str(log)
    ran_model, ran_effort = meta.get("model"), meta.get("effort")
    # The asked-for model exactly, or a dated alias of it; never a longer
    # name (gpt-6.1 must not pass as gpt-6.1-mini). Effort must be confirmed.
    alias = re.escape(args.model) + r"(-\d{4}-\d{2}-\d{2}|-\d{8})?"
    meta["model_verified"] = bool(
        ran_model and re.fullmatch(alias, ran_model) and ran_effort == args.effort
    )

    def finish(code: int, message: str = "") -> int:
        meta["result"] = code
        if message:
            meta["reason"] = message
        (args.out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        if code == 0:
            reply.rename(args.out / "reply.md")
        return fail(code, message) if code else 0

    problem = ("\n".join(errors) + "\n" + stderr).strip()
    if timed_out:
        return finish(1, f"Codex didn't finish within {args.timeout}s")
    answered = reply.is_file() and reply.read_text(encoding="utf-8", errors="replace").strip()
    if returncode != 0 or turn_failed or usage is None or not answered:
        # A limit is read from Codex's own error events first; stderr only
        # when there are none, so a stray "429" in a log line doesn't count.
        limit = LIMIT_RE.search("\n".join(errors) if errors else stderr)
        return finish(4 if limit else 1,
                      f"Codex failed (exit {returncode}): {problem[-800:] or 'no answer'}")
    if not meta["model_verified"]:
        return finish(5, f"asked for {args.model} at {args.effort}; the session log says "
                         f"{ran_model or 'unknown'} at {ran_effort or 'unknown'}: treat as not run")
    finish(0)
    print(json.dumps({k: meta.get(k) for k in
                      ("model", "effort", "model_verified", "seconds", "usage", "usage_windows")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
