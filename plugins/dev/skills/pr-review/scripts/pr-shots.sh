#!/usr/bin/env bash
# Put screenshots where a PR description can show them.
#
#   pr-shots.sh push FILE...      commit the images, alone, to the side branch
#                                 shots/<current branch>, and print one
#                                 markdown image line per file
#                                 (two files with one name each take
#                                 their folder's name: a/x.png and b/x.png
#                                 go up as a-x.png and b-x.png)
#   pr-shots.sh delete [BRANCH]   delete shots/<BRANCH> (default: the current
#                                 branch's). The steward skill runs it
#
# The side branch is an orphan: one commit holding only the images, never
# merged, with no workflows in it, so pushing it runs no GitHub Actions (a
# host that builds every branch, such as Vercel or Netlify, may need
# shots/* ignored). A second
# `push` replaces the set, so put the new lines in the description. The
# lines address the commit, not the branch, so they don't change under a
# reader. The steward skill runs `delete` when the PR merges or closes; a
# cloud session's git access may refuse branch deletes, and then it's for a
# laptop, or the GitHub UI.
#
# Refuses to run on the repo's default branch, on a branch named in
# PR_SHOTS_PROTECTED (space-separated, e.g. "dev main"), or on shots/*.
#
# Only screenshots of sample data: these are readable by everyone with the
# repo, and GitHub keeps them. Never one that shows a real person's details.
set -euo pipefail

die() { echo "pr-shots: $*" >&2; exit 1; }

cmd="${1:-}"; [ $# -gt 0 ] && shift
root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not in a git checkout"
current="$(git -C "$root" branch --show-current)"

# owner/repo from origin, whatever form the URL takes (https, ssh, a proxy).
slug="$(git -C "$root" remote get-url origin | sed -E 's#/+$##; s#\.git$##; s#^.*[:/]([^/:]+/[^/]+)$#\1#')"
[[ "$slug" =~ ^[^/:]+/[^/:]+$ ]] || die "can't read owner/repo from origin"

case "$cmd" in
push)
    [ $# -gt 0 ] || die "push needs at least one image file"
    [ -n "$current" ] || die "not on a branch"
    default="$(git -C "$root" ls-remote --symref origin HEAD 2>/dev/null | sed -nE 's#^ref: refs/heads/([^[:space:]]+)[[:space:]]+HEAD$#\1#p' || true)"
    for protected in $default ${PR_SHOTS_PROTECTED:-} main master; do
        [ "$current" != "$protected" ] || die "not from '$current': screenshots belong to a feature branch"
    done
    case "$current" in shots/*) die "not from '$current': screenshots belong to a feature branch" ;; esac
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    export GIT_INDEX_FILE="$tmp/index"
    # Every path is made absolute first: the files are named from where the
    # caller stands, and git reads from the repo's root.
    files=(); names=()
    for f in "$@"; do
        [ -f "$f" ] || die "no such file: $f"
        files+=("$(cd -- "$(dirname -- "$f")" && pwd)/$(basename -- "$f")")
    done
    for f in "${files[@]}"; do
        name="${f##*/}"
        # A before and an after run are the same file names in two folders:
        # a name more than one file has gets its folder's name in front.
        same=0
        for g in "${files[@]}"; do [ "${g##*/}" != "$name" ] || same=$((same + 1)); done
        if [ "$same" -gt 1 ]; then
            dir="${f%/*}"; dir="${dir##*/}"
            [[ "$dir" =~ ^[A-Za-z0-9._-]+$ ]] || die "two files are called '$name', and the folder '$dir' can't go in a file name: rename the folder or the file"
            name="$dir-$name"
        fi
        shopt -s nocasematch
        case "$name" in
            *.png|*.jpg|*.jpeg|*.webp|*.gif) ;;
            *) die "not an image: $f" ;;
        esac
        shopt -u nocasematch
        [[ "$name" =~ ^[A-Za-z0-9._-]+$ ]] || die "rename '$name': letters, digits, dots, dashes and underscores only"
        for seen in "${names[@]:-}"; do [ "$seen" != "$name" ] || die "two files would both be called '$name'"; done
        names+=("$name")
    done
    # Nothing is written until every file has passed.
    for i in "${!files[@]}"; do
        blob="$(git -C "$root" hash-object -w -- "${files[$i]}")"
        git -C "$root" update-index --add --cacheinfo "100644,$blob,${names[$i]}"
    done
    tree="$(git -C "$root" write-tree)"
    commit="$(git -C "$root" commit-tree "$tree" -m "Screenshots for $current (not for merging)")"
    unset GIT_INDEX_FILE
    git -C "$root" -c push.negotiate=false push --quiet --force origin "$commit:refs/heads/shots/$current" \
        || die "couldn't push shots/$current"
    echo "Pushed ${#names[@]} to shots/$current. Lines for the PR description:" >&2
    for name in "${names[@]}"; do
        echo "![${name%.*}](https://github.com/$slug/blob/$commit/$name?raw=true)"
    done
    ;;
delete)
    branch="${1:-$current}"
    [ -n "$branch" ] || die "which branch's screenshots?"
    branch="${branch#shots/}"
    found="$(git -C "$root" ls-remote --heads origin "shots/$branch")" || die "couldn't reach origin"
    if [ -n "$found" ]; then
        git -C "$root" -c push.negotiate=false push --quiet origin --delete "shots/$branch" || die "couldn't delete shots/$branch"
        echo "Deleted shots/$branch." >&2
    else
        echo "No shots/$branch on origin: nothing to delete." >&2
    fi
    ;;
*)
    die "usage: pr-shots.sh push FILE... | pr-shots.sh delete [BRANCH]"
    ;;
esac
