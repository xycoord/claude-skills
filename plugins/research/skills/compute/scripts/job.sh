#!/usr/bin/env bash
# Run one research job on a Runpod pod, keep its outputs on Hugging Face,
# report on the experiment's PR, and delete the pod. Every way out ends in a
# delete: success, failure, deadline, stall, bad settings, a crash in this
# script, or a container restart (which is reported, never rerun).
#
# The pod's start command downloads this script from a pinned commit of
# xycoord/claude-skills and runs it (see the compute skill). Settings come from
# the pod's environment:
#
#   JOB_ID          claude-<experiment>-<n>; also names the results folder
#   REPO, COMMIT    the code to run: owner/name and a full commit sha
#   JOB_CMD         run with bash from the repo root
#   MAX_HOURS       the job's deadline, counted from the pod's creation
#   PR              the experiment PR that gets the reports
#   JOB_PREFLIGHT_CMD  optional; run first, a failure ends the job early
#   RESULTS_REPO    HF dataset for results
#   RESULTS_PATH    folder in it (default runs/$JOB_ID)
#   RESUME_FROM     optional; a folder in RESULTS_REPO (an earlier run's
#                   runs/<id>) copied into $JOB_OUT before the job starts
#   STALL_MINUTES   no new output in $JOB_OUT for this long ends the job (30)
#   UPLOAD_MINUTES  how often $JOB_OUT is synced while running (15)
#   RESCUE_MINUTES  if the final upload fails and there are results, the pod
#                   stays up this long, retrying the upload every 10 min (120)
#   HF_TOKEN, GITHUB_TOKEN   from Runpod secrets
#   RUNPOD_API_KEY, RUNPOD_POD_ID   set by Runpod; the key only reaches this pod
#
# The job's side: write everything worth keeping to $JOB_OUT, each file under
# a temporary name (*.tmp or *.partial, never uploaded) renamed when complete;
# print progress (its stdout is $JOB_OUT/job.log) at least every
# STALL_MINUTES; touch $JOB_OUT/FIRST_LOOK once its first slice of results is
# there. This script's own notes go to $JOB_OUT/wrapper.log.
#
# The pod is deleted by $DELETE_AT at the latest: the deadline, plus time for
# the final upload, the rescue window and slack. A background backstop
# enforces it even if this script hangs.

set -o pipefail   # no -u: finish must never stop on an unset variable

WORK=/workspace/job
RESULTS_PATH=${RESULTS_PATH:-runs/${JOB_ID:-unknown}}
export JOB_OUT=$WORK/out
LOG=$JOB_OUT/job.log
WLOG=$JOB_OUT/wrapper.log
mkdir -p "$JOB_OUT"
export RESULTS_REPO RESULTS_PATH PYTHONUNBUFFERED=1
STALL_MINUTES=${STALL_MINUTES:-30}
UPLOAD_MINUTES=${UPLOAD_MINUTES:-15}
RESCUE_MINUTES=${RESCUE_MINUTES:-120}
FINAL_UPLOAD_MINUTES=45
STARTED=$(date +%s)
STATUS="" JOB_EXIT="" JOB_PID="" FAIL_STEP="" NO_UPLOAD="" DELETE_AT=""
CURL=(curl -s --connect-timeout 10 --max-time 60)

note() { echo "[job.sh $(date -u +%H:%M:%S)] $*" | tee -a "$WLOG"; }
utc() { date -u -d "@$1" +%H:%M; }

# Retry until the pod is gone; never give up, since a live pod keeps billing.
delete_pod() {
  local wait=30 code
  while :; do
    code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X DELETE \
      -H "Authorization: Bearer ${RUNPOD_API_KEY:-}" \
      "https://api.runpod.io/v2/pods/${RUNPOD_POD_ID:-}")
    case $code in 204|404) return 0 ;; esac
    note "delete answered ${code:-nothing}; retrying in ${wait}s"
    sleep "$wait"
    wait=$(( wait * 2 > 600 ? 600 : wait * 2 ))
  done
}

# upload <why> <seconds>. Uploads go through Xet, which skips content the
# Hub already has, so an attempt cut off by the time limit isn't all wasted.
# Only long-standing huggingface_hub APIs: pip installs whatever is latest.
upload() {
  [ -z "$NO_UPLOAD" ] || return 1
  timeout -k 60 "$2" python3 - "$1" >/dev/null 2>>"$WORK/upload.err" <<'EOF' && return 0
import os, sys
from huggingface_hub import HfApi
HfApi().upload_folder(repo_id=os.environ["RESULTS_REPO"], repo_type="dataset",
                      folder_path=os.environ["JOB_OUT"], path_in_repo=os.environ["RESULTS_PATH"],
                      ignore_patterns=["*.tmp", "*.partial"],
                      commit_message=f"{os.environ['JOB_ID']}: {sys.argv[1]}")
EOF
  note "upload ($1) failed: $(tail -n 1 "$WORK/upload.err" 2>/dev/null)"
  return 1
}

# report <kind> <detail> [<attempts>]: a marked comment on the experiment PR,
# which wakes the session. Returns 0 only once GitHub has it.
report() {
  local kind=$1 detail=$2 attempts=${3:-8} wait=15 code i
  [ -n "${PR:-}" ] && [ -n "${GITHUB_TOKEN:-}" ] || return 1
  python3 - "$kind" "$detail" <<'EOF' >"$WORK/comment.json" || return 1
import json, os, re, sys
kind, detail = sys.argv[1:3]
env = os.environ
def tail(name, n):
    # Last lines only, read from the end: progress bars write huge \r lines.
    try:
        with open(os.path.join(env["JOB_OUT"], name), "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - 65536))
            text = f.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [l[:300] for l in re.split(r"\r\n|\r|\n", text) if l.strip()]
    return "\n".join(lines[-n:]) + "\n"
text = tail("wrapper.log", 12) + "--- job output ---\n" + tail("job.log", 20)
for name in ("HF_TOKEN", "GITHUB_TOKEN", "RUNPOD_API_KEY"):
    if env.get(name):
        text = text.replace(env[name], "***")
text = text.replace("```", "'''")[-6000:]
url = f"https://huggingface.co/datasets/{env.get('RESULTS_REPO')}/tree/main/{env.get('RESULTS_PATH')}"
body = (
    f"<!-- job-report kind={kind} job={env.get('JOB_ID')} pod={env.get('RUNPOD_POD_ID')} -->\n"
    f"**Job `{env.get('JOB_ID')}`: {kind}** ({detail})\n\n"
    f"Pod `{env.get('RUNPOD_POD_ID')}` · commit `{env.get('COMMIT', '?')[:12]}` · "
    f"{env.get('RUNPOD_GPU_COUNT', '0')}× {env.get('RUNPOD_GPU_NAME', 'CPU')} · [results]({url})\n\n"
    f"<details><summary>Last lines of the logs</summary>\n\n```\n{text}```\n</details>\n"
)
json.dump({"body": body}, sys.stdout)
EOF
  for (( i = 1; i <= attempts; i++ )); do
    code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST \
      -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$REPO/issues/$PR/comments" -d @"$WORK/comment.json")
    [ "$code" = 201 ] && return 0
    note "report ($kind) answered ${code:-nothing}"
    [ "$i" -lt "$attempts" ] && sleep "$wait"
    wait=$(( wait * 2 > 300 ? 300 : wait * 2 ))
  done
  return 1
}

stop_job() {
  [ -n "$JOB_PID" ] || return 0
  # The whole process group, even if its leader has already exited.
  kill -TERM -- "-$JOB_PID" 2>/dev/null || return 0
  for _ in $(seq 60); do
    kill -0 -- "-$JOB_PID" 2>/dev/null || return 0
    sleep 1
  done
  kill -KILL -- "-$JOB_PID" 2>/dev/null
}

has_results() {  # anything the job wrote beyond logs and markers
  [ -n "$(find "$JOB_OUT" -type f ! -name job.log ! -name wrapper.log \
    ! -name job_meta.json ! -name job_started.json ! -name FIRST_LOOK \
    ! -name '*.tmp' ! -name '*.partial' -print -quit)" ]
}

finish() {
  trap - EXIT INT TERM
  set +e
  stop_job
  [ -n "$STATUS" ] || STATUS=crashed
  local now mins detail rescue_end
  now=$(date +%s)
  mins=$(( (now - STARTED) / 60 ))
  detail="${FAIL_STEP:+at: $FAIL_STEP, }exit ${JOB_EXIT:-none}, ${mins} min"
  python3 - "$STATUS" "$JOB_EXIT" "$STARTED" "$now" <<'EOF' >"$JOB_OUT/job_meta.json"
import json, os, sys
status, code, start, end = sys.argv[1:]
env = os.environ
meta = {k: env.get(k.upper()) for k in
        ("job_id", "repo", "commit", "job_cmd", "max_hours", "resume_from",
         "runpod_pod_id", "runpod_gpu_name", "runpod_gpu_count")}
meta.update(status=status, exit_code=int(code) if code else None,
            started=int(start), ended=int(end))
json.dump(meta, sys.stdout, indent=2)
EOF
  note "finished: $STATUS after ${mins} min"
  if [ -n "$NO_UPLOAD" ]; then
    report "$STATUS" "$detail"
  elif upload final $(( FINAL_UPLOAD_MINUTES * 60 )); then
    report "$STATUS" "$detail"
  elif ! has_results; then
    report "$STATUS" "$detail; the upload failed too, but there were no results to keep"
  else
    rescue_end=$(( $(date +%s) + RESCUE_MINUTES * 60 ))
    if [ -n "$DELETE_AT" ] && [ "$rescue_end" -gt $(( DELETE_AT - 300 )) ]; then
      rescue_end=$(( DELETE_AT - 300 ))
    fi
    report upload-failed "$STATUS, $detail; results are only on this pod; retrying the upload every 10 min until $(utc "$rescue_end") UTC, then the pod is deleted" 3
    local uploaded=""
    local left_s
    while left_s=$(( rescue_end - $(date +%s) )); [ "$left_s" -gt 60 ]; do
      sleep $(( left_s < 600 ? left_s - 60 : 600 ))
      left_s=$(( rescue_end - $(date +%s) ))
      if upload rescue $(( left_s < 540 ? (left_s > 60 ? left_s : 60) : 540 )); then
        uploaded=1
        report "$STATUS" "$detail; uploaded on a later try"
        break
      fi
    done
    [ -n "$uploaded" ] \
      || report results-lost "$STATUS, $detail; the upload never got through and the pod is deleted now" 3
  fi
  note "deleting the pod"
  delete_pod
  # Never let the main process exit: Runpod would restart the container.
  sleep infinity
}
trap finish EXIT
trap 'STATUS=${STATUS:-interrupted}; exit 1' INT TERM

# Settings come first after the trap, so a mistake ends in a delete, not a
# restart loop.
for v in JOB_ID REPO COMMIT JOB_CMD MAX_HOURS PR RESULTS_REPO \
         HF_TOKEN GITHUB_TOKEN RUNPOD_API_KEY RUNPOD_POD_ID; do
  if [ -z "${!v:-}" ]; then
    STATUS=bad-settings; FAIL_STEP="$v is not set"; NO_UPLOAD=1; exit 1
  fi
done
if ! awk -v h="$MAX_HOURS" 'BEGIN { exit !(h + 0 > 0) }'; then
  STATUS=bad-settings; FAIL_STEP="MAX_HOURS=$MAX_HOURS"; NO_UPLOAD=1; exit 1
fi

# The deadline counts from the pod's creation, so a restart can't extend it.
CREATED=$("${CURL[@]}" -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/pods/$RUNPOD_POD_ID" | python3 -c '
import datetime, json, sys
t = json.load(sys.stdin)["createdAt"].replace("Z", "+00:00")
print(int(datetime.datetime.fromisoformat(t).timestamp()))' 2>/dev/null) || CREATED=$STARTED
DEADLINE=$(awk -v s="$CREATED" -v h="$MAX_HOURS" 'BEGIN { printf "%d", s + h * 3600 }')
DELETE_AT=$(( DEADLINE + (FINAL_UPLOAD_MINUTES + RESCUE_MINUTES + 15) * 60 ))
# Backstop: delete at DELETE_AT whatever this script is doing by then.
( sleep $(( DELETE_AT - $(date +%s) )); note "backstop: deleting the pod"; delete_pod ) &

left() {  # seconds to the deadline, at least 1 (timeout 0 would mean no limit)
  local s=$(( DEADLINE - $(date +%s) ))
  [ "$s" -gt 0 ] && echo "$s" || echo 1
}
step() {  # step <name> <command...>: a setup step inside the deadline
  local name=$1; shift
  note "$name"
  timeout -k 60 "$(left)" "$@" >>"$LOG" 2>&1 && return 0
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then STATUS=deadline; else STATUS=setup-failed; fi
  FAIL_STEP=$name; exit 1
}

note "job $JOB_ID on pod $RUNPOD_POD_ID; deadline $(utc "$DEADLINE") UTC, deleted by $(utc "$DELETE_AT") UTC at the latest"
python3 -c 'import huggingface_hub' 2>/dev/null \
  || step "install huggingface_hub" pip install -q huggingface_hub

# A restarted container finds the job's claim on HF and stops: never run a
# job twice. (The local marker only catches a restart that kept the disk;
# Runpod's restart gives a fresh container disk.)
if [ -e "$WORK/started" ] || python3 -c '
import os, sys
from huggingface_hub import HfApi
sys.exit(0 if HfApi().file_exists(os.environ["RESULTS_REPO"], os.environ["RESULTS_PATH"] + "/job_started.json", repo_type="dataset") else 1)' 2>>"$WORK/upload.err"; then
  STATUS=restarted; FAIL_STEP="this job already started once"; NO_UPLOAD=1; exit 1
fi
touch "$WORK/started"
printf '{"pod": "%s", "started": %s}\n' "$RUNPOD_POD_ID" "$STARTED" >"$JOB_OUT/job_started.json"
claim_note=""
upload claim 300 \
  || claim_note="; couldn't record the start on HF, so a container restart would rerun the job"
report started "deadline $(utc "$DEADLINE") UTC$claim_note" 3 || note "started report didn't go through"

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
if [ -n "${RESUME_FROM:-}" ]; then
  step "resume from $RESUME_FROM" python3 -c '
import os, shutil, tempfile
from huggingface_hub import snapshot_download
src = os.environ["RESUME_FROM"].strip("/")
tmp = tempfile.mkdtemp()
snapshot_download(os.environ["RESULTS_REPO"], repo_type="dataset", local_dir=tmp, allow_patterns=[src + "/**"])
skip = {"job.log", "wrapper.log", "job_meta.json", "job_started.json", "FIRST_LOOK"}
base = os.path.join(tmp, src)
for root, _, files in os.walk(base):
    for f in files:
        if f in skip:
            continue
        dst = os.path.join(os.environ["JOB_OUT"], os.path.relpath(os.path.join(root, f), base))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(root, f), dst)'
fi
if [ -n "${JOB_PREFLIGHT_CMD:-}" ]; then
  note "preflight: $JOB_PREFLIGHT_CMD"
  if ! timeout -k 60 "$(left)" bash -c "$JOB_PREFLIGHT_CMD" >>"$LOG" 2>&1; then
    if [ "$(date +%s)" -ge "$DEADLINE" ]; then STATUS=deadline; else STATUS=preflight-failed; fi
    exit 1
  fi
fi

note "run: ${JOB_CMD%%$'\n'*}"
set -m   # the job gets its own process group, so it can be stopped as a whole
bash -c "$JOB_CMD" >>"$LOG" 2>&1 &
JOB_PID=$!
set +m
last_upload=$(date +%s)
first_look_sent=""
while kill -0 "$JOB_PID" 2>/dev/null; do
  sleep 30
  now=$(date +%s)
  if [ "$now" -ge "$DEADLINE" ]; then
    STATUS=deadline; exit 1
  fi
  if [ -z "$(find "$JOB_OUT" -type f ! -name wrapper.log ! -name job_meta.json \
      -newermt "${STALL_MINUTES} minutes ago" -print -quit)" ]; then
    STATUS=stalled; exit 1
  fi
  if [ -z "$first_look_sent" ] && [ -e "$JOB_OUT/FIRST_LOOK" ]; then
    # Sent only once the slice is on HF and GitHub has the report.
    if upload first-look 600 && report first-look "results so far are uploaded" 3; then
      first_look_sent=1
    fi
    last_upload=$now
  elif [ $(( now - last_upload )) -ge $(( UPLOAD_MINUTES * 60 )) ]; then
    upload progress 600   # a short limit keeps the checks running
    last_upload=$now
  fi
done
wait "$JOB_PID"
JOB_EXIT=$?
if [ "$JOB_EXIT" -eq 0 ]; then STATUS=done; else STATUS=failed; fi
exit 0
