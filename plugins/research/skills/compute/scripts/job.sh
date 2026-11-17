#!/usr/bin/env bash
# Run one research job on a Runpod pod, keep its outputs on Hugging Face,
# report on the experiment's PR, and delete the pod: on success, failure,
# deadline, stall or a crash in this script. The pod never outlives the job.
#
# The pod's start command decodes this script from JOB_SH_B64 and runs it
# (see the compute skill). Settings come from the pod's environment:
#
#   JOB_ID          claude-<experiment>-<n>; also names the results folder
#   REPO, COMMIT    the code to run: owner/name and a full commit sha
#   JOB_CMD         run with bash from the repo root
#   MAX_HOURS       hard deadline for the whole pod, setup included
#   JOB_PREFLIGHT_CMD  optional; run first, a failure ends the job early
#   PR              optional; the experiment PR that gets the reports
#   RESULTS_REPO    HF dataset (default xycoord/research-results)
#   RESULTS_PATH    folder in it (default runs/$JOB_ID)
#   STALL_MINUTES   no new output in $JOB_OUT for this long ends the job (30)
#   UPLOAD_MINUTES  how often $JOB_OUT is synced while running (15)
#   HF_TOKEN, GITHUB_TOKEN   from Runpod secrets
#   RUNPOD_API_KEY, RUNPOD_POD_ID   set by Runpod; the key only reaches this pod
#
# The job writes everything worth keeping to $JOB_OUT, prints progress at
# least every STALL_MINUTES, and touches $JOB_OUT/FIRST_LOOK once its first
# slice of results is there, which triggers an upload and a "first-look" report.

set -uo pipefail

: "${JOB_ID:?}" "${REPO:?}" "${COMMIT:?}" "${JOB_CMD:?}" "${MAX_HOURS:?}"
RESULTS_REPO=${RESULTS_REPO:-xycoord/research-results}
RESULTS_PATH=${RESULTS_PATH:-runs/$JOB_ID}
STALL_MINUTES=${STALL_MINUTES:-30}
UPLOAD_MINUTES=${UPLOAD_MINUTES:-15}
PR=${PR:-}
export RESULTS_REPO RESULTS_PATH

WORK=/workspace/job
export JOB_OUT=$WORK/out
LOG=$JOB_OUT/job.log
mkdir -p "$JOB_OUT"

STARTED=$(date +%s)
DEADLINE=$(awk -v s="$STARTED" -v h="$MAX_HOURS" 'BEGIN { printf "%d", s + h * 3600 }')
STATUS=""
JOB_EXIT=""
JOB_PID=""
FAIL_STEP=""

note() { echo "[job.sh $(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

# Backstop for a hang in this script itself (an upload or report that never
# returns): delete the pod 30 minutes after the deadline whatever else happens.
( sleep $(( DEADLINE - STARTED + 1800 ))
  curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $RUNPOD_API_KEY" \
    "https://api.runpod.io/v2/pods/$RUNPOD_POD_ID" ) &

upload() {
  local why=$1
  timeout 30m hf upload "$RESULTS_REPO" "$JOB_OUT" "$RESULTS_PATH" \
    --repo-type dataset --commit-message "$JOB_ID: $why" >/dev/null 2>>"$WORK/upload.err" \
    && return 0
  note "upload ($why) failed: $(tail -n 1 "$WORK/upload.err" 2>/dev/null)"
  return 1
}

# Post a marked comment on the experiment PR. The session treats it as data.
report() {
  [ -n "$PR" ] || return 0
  local kind=$1 detail=$2
  python3 - "$kind" "$detail" <<'EOF' >"$WORK/comment.json"
import json, os, sys
kind, detail = sys.argv[1], sys.argv[2]
env = os.environ
tail = ""
try:
    with open(os.path.join(env["JOB_OUT"], "job.log"), errors="replace") as f:
        tail = "".join(f.readlines()[-30:])
except OSError:
    pass
for name in ("HF_TOKEN", "GITHUB_TOKEN", "RUNPOD_API_KEY"):
    if env.get(name):
        tail = tail.replace(env[name], "***")
tail = tail.replace("```", "'''")
url = f"https://huggingface.co/datasets/{env['RESULTS_REPO']}/tree/main/{env['RESULTS_PATH']}"
body = (
    f"<!-- job-report kind={kind} job={env['JOB_ID']} -->\n"
    f"**Job `{env['JOB_ID']}`: {kind}** ({detail})\n\n"
    f"Commit `{env['COMMIT'][:12]}` · GPU {env.get('RUNPOD_GPU_COUNT', '?')}× "
    f"{env.get('RUNPOD_GPU_NAME', '?')} · [results]({url})\n\n"
    f"<details><summary>Last lines of the log</summary>\n\n```\n{tail}```\n</details>\n"
)
json.dump({"body": body}, sys.stdout)
EOF
  curl -s -o /dev/null -w '%{http_code}' -X POST \
    -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/issues/$PR/comments" -d @"$WORK/comment.json" \
    | grep -q '^201$' || note "report ($kind) failed"
}

delete_pod() {
  local code
  for _ in $(seq 1 20); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE \
      -H "Authorization: Bearer $RUNPOD_API_KEY" "https://api.runpod.io/v2/pods/$RUNPOD_POD_ID")
    case $code in 204|404) return 0 ;; esac
    sleep 30
  done
  return 1
}

stop_job() {
  [ -n "$JOB_PID" ] && kill -0 "$JOB_PID" 2>/dev/null || return 0
  kill -TERM -- "-$JOB_PID" 2>/dev/null
  sleep 20
  kill -KILL -- "-$JOB_PID" 2>/dev/null
}

finish() {
  trap - EXIT INT TERM
  stop_job
  [ -n "$STATUS" ] || STATUS=crashed
  local ended mins
  ended=$(date +%s)
  mins=$(( (ended - STARTED) / 60 ))
  python3 - "$STATUS" "$JOB_EXIT" "$STARTED" "$ended" <<'EOF' >"$JOB_OUT/job_meta.json"
import json, os, sys
status, code, start, end = sys.argv[1:]
env = os.environ
json.dump({
    "job_id": env["JOB_ID"], "repo": env["REPO"], "commit": env["COMMIT"],
    "cmd": env["JOB_CMD"], "status": status, "exit_code": int(code) if code else None,
    "started": int(start), "ended": int(end), "max_hours": float(env["MAX_HOURS"]),
    "gpu": env.get("RUNPOD_GPU_NAME"), "gpu_count": env.get("RUNPOD_GPU_COUNT"),
    "pod_id": env.get("RUNPOD_POD_ID"),
}, sys.stdout, indent=2)
EOF
  note "finished: $STATUS after ${mins} min; uploading and deleting the pod"
  upload "$STATUS" || upload "$STATUS (retry)"
  report "$STATUS" "${FAIL_STEP:+at: $FAIL_STEP, }exit ${JOB_EXIT:-none}, ${mins} min"
  if ! delete_pod; then
    report "pod-delete-failed" "delete it by hand: pod $RUNPOD_POD_ID"
  fi
  # Never let the container's main process exit: Runpod would restart it
  # and run the job again.
  sleep infinity
}
trap finish EXIT
trap 'STATUS=${STATUS:-interrupted}; exit 1' INT TERM

left() {  # seconds to the deadline, at least 1 (timeout 0 would mean no limit)
  local s=$(( DEADLINE - $(date +%s) ))
  [ "$s" -gt 0 ] && echo "$s" || echo 1
}
step() {  # step <name> <command...>: run a setup step inside the deadline
  local name=$1; shift
  note "$name"
  timeout "$(left)" "$@" >>"$LOG" 2>&1 && return 0
  STATUS=setup-failed; FAIL_STEP=$name; exit 1
}

note "job $JOB_ID on pod $RUNPOD_POD_ID, deadline in ${MAX_HOURS} h"
git config --global advice.detachedHead false
# The token goes in a header, not the URL, so git can't echo it into the log.
GIT_AUTH="Authorization: Basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)"
step "fetch $REPO@${COMMIT:0:12}" bash -c '
  git init -q "$0" && cd "$0" &&
  git -c http.extraHeader="$1" fetch -q --depth 1 "https://github.com/$2.git" "$3" &&
  git checkout -q FETCH_HEAD' "$WORK/repo" "$GIT_AUTH" "$REPO" "$COMMIT"
cd "$WORK/repo" || exit 1
command -v uv >/dev/null || step "install uv" pip install -q uv
if [ -f pyproject.toml ]; then
  step "uv sync" uv sync --frozen
fi
if [ -n "${JOB_PREFLIGHT_CMD:-}" ]; then
  note "preflight: $JOB_PREFLIGHT_CMD"
  if ! timeout "$(left)" bash -c "$JOB_PREFLIGHT_CMD" >>"$LOG" 2>&1; then
    STATUS=preflight-failed; exit 1
  fi
fi

note "run: $JOB_CMD"
setsid bash -c "$JOB_CMD" >>"$LOG" 2>&1 &
JOB_PID=$!
last_upload=$(date +%s)
first_look_sent=""
while kill -0 "$JOB_PID" 2>/dev/null; do
  sleep 30
  now=$(date +%s)
  if [ "$now" -ge "$DEADLINE" ]; then
    STATUS=deadline; exit 1
  fi
  if [ -z "$(find "$JOB_OUT" -newermt "${STALL_MINUTES} minutes ago" -print -quit)" ]; then
    STATUS=stalled; exit 1
  fi
  if [ -z "$first_look_sent" ] && [ -e "$JOB_OUT/FIRST_LOOK" ]; then
    first_look_sent=1
    upload first-look && report first-look "results so far are uploaded"
    last_upload=$now
  elif [ $(( now - last_upload )) -ge $(( UPLOAD_MINUTES * 60 )) ]; then
    upload progress
    last_upload=$now
  fi
done
wait "$JOB_PID"
JOB_EXIT=$?
if [ "$JOB_EXIT" -eq 0 ]; then STATUS=done; else STATUS=failed; fi
exit 0
