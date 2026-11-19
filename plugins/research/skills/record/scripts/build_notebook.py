#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6", "markdown>=3.5"]
# ///
"""Build the research notebook page from a research repo.

    uv run <record skill>/scripts/build_notebook.py <repo-dir> -o notebook.html

Reads threads/, experiments/, glossary.yaml and notebook.yaml (the format is in
references/format.md beside this script's folder) and writes one self-contained
page for the claude.ai artifact: the functional-design kit pasted in, the
notebook's data embedded as JSON, and the script that renders it. The page has
no doctype, html, head or body tags, because the artifact publisher adds them.

The kit (base.css, base.js, charts.js, interp.js) is found in this order:
  1. the folder named by the FD_KIT environment variable;
  2. an installed style plugin under ~/.claude/plugins/;
  3. this repo's own copy, at ../../../style/skills/functional-design/references
     relative to the record skill's folder;
  4. a download from the claude-skills repo's main branch.

The input is checked first. Every problem is printed with its file, and the
build stops without writing anything if there are errors.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import markdown
import yaml

KIT_FILES = ["base.css", "base.js", "charts.js", "interp.js"]
KIT_URL = "https://raw.githubusercontent.com/xycoord/claude-skills/main/plugins/style/skills/functional-design/references/{}"
VIEWS = {"dotChart", "lineChart", "barChart", "distChart", "tokenText", "topExamples", "heatmap",
         "lensExplorer", "logitLens", "graph", "table"}
SECTIONS = {
    "test": ["Why we ran it", "What was compared", "Result", "Method", "Checks", "Examples", "Caveats"],
    "explore": ["Why we looked", "The data", "Patterns", "Looked at and found nothing", "Method"],
}
THREAD_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXP_ID = re.compile(r"^E-(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
F_ID = re.compile(r"^F-[a-z0-9]+(?:-[a-z0-9]+)*$")
Q_ID = re.compile(r"^Q-[a-z0-9]+(?:-[a-z0-9]+)*$")
VERDICT = re.compile(r"^(Yes|No answer yet|No answer|Not yet|No|Partly)([.,:])")


class Problems:
    def __init__(self, root: Path):
        self.root, self.errors, self.warnings = root, [], []

    def _where(self, path):
        try:
            return str(Path(path).relative_to(self.root))
        except ValueError:
            return str(path)

    def error(self, path, msg):
        self.errors.append(f"{self._where(path)}: {msg}")

    def warn(self, path, msg):
        self.warnings.append(f"{self._where(path)}: {msg}")


# ---------- reading files ----------

def plain(v):
    """YAML dates become ISO strings, so the data can be compared and turned into JSON."""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()[:10]
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [plain(x) for x in v]
    return v


def read_front(path: Path, p: Problems):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?$", text, re.S)
    if not m:
        p.error(path, "should start with YAML front matter between two --- lines")
        return None, ""
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        p.error(path, f"front matter isn't valid YAML: {e}")
        return None, ""
    if not isinstance(data, dict):
        p.error(path, "front matter should be a mapping of fields")
        return None, ""
    return plain(data), m.group(2) or ""


def read_yaml(path: Path, p: Problems):
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        p.error(path, f"isn't valid YAML: {e}")
        return {}
    if not isinstance(data, dict):
        p.error(path, "should be a mapping of fields")
        return {}
    return plain(data)


# ---------- markdown ----------

FIG_LINE = re.compile(r"^::fig[ \t]+(\S+)[ \t]*$", re.M)
FENCE = re.compile(r"(^```.*?^```[ \t]*$|^~~~.*?^~~~[ \t]*$)", re.M | re.S)
# A code span whose text starts or ends with a space is a model's token: it keeps its spaces and is set as a token.
TOKEN_SPAN = re.compile(r"(?<!`)`((?: [^`\n]*)|(?:[^`\n]* ))`(?!`)")
HASH_LINK = re.compile(r'href="#([^"]*)"')


class Markdown:
    def __init__(self):
        self.md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
        self.links = []  # (path, target) for every in-page link, checked once everything is read

    def _protect(self, text):
        toks = []

        def tok(m):
            toks.append(m.group(1))
            return f"\u27e6NBTOK{len(toks) - 1}\u27e7"

        parts = FENCE.split(text)
        for i in range(0, len(parts), 2):  # outside fenced code only
            s = TOKEN_SPAN.sub(tok, parts[i])
            s = re.sub(r"\bn = (?=[\d,.]+)", "n = ", s)
            parts[i] = s
        return "".join(parts), toks

    def _restore(self, out, toks):
        return re.sub(r"\u27e6NBTOK(\d+)\u27e7", lambda m: f'<span class="tok">{html.escape(toks[int(m.group(1))])}</span>', out)

    def block(self, text, path):
        figs = []

        def fig(m):
            figs.append(m.group(1))
            return f"\n\nNBFIG{len(figs) - 1}NBFIG\n\n"

        text, toks = self._protect(FIG_LINE.sub(fig, text))
        out = self._restore(self.md.reset().convert(text), toks)
        out = re.sub(r"<p>NBFIG(\d+)NBFIG</p>", lambda m: f'<div class="nb-fig" data-fig="{html.escape(figs[int(m.group(1))])}"></div>', out)
        out = out.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
        self.links += [(path, t) for t in HASH_LINK.findall(out)]
        return out, figs

    def inline(self, text, path):
        if text is None:
            return None
        text, toks = self._protect(str(text))
        out = self._restore(self.md.reset().convert(text), toks).strip()
        m = re.fullmatch(r"<p>(.*)</p>", out, re.S)
        if m and "<p>" not in m.group(1):
            out = m.group(1)
        self.links += [(path, t) for t in HASH_LINK.findall(out)]
        return out


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or ""))


def verdict(s):
    """Bolds the one-word verdict that opens a test's answer, so a reader can stop there."""
    return VERDICT.sub(r"<b>\1\2</b>", s) if s else s


def change_line(s):
    """A history line reads "status change: gist"; the status change is bold."""
    m = re.match(r"^(.+?[.:])(\s|$)", s or "")
    return f"<b>{m.group(1)}</b>{s[len(m.group(1)):]}" if m else s


# ---------- the repo ----------

def load(root: Path, p: Problems):
    md = Markdown()
    nb = read_yaml(root / "notebook.yaml", p)
    gl = read_yaml(root / "glossary.yaml", p)
    figs, threads, exps = {}, [], []
    bad = set()  # figure files that exist but couldn't be used; their own error already says why

    # Experiments and their figures.
    edir = root / "experiments"
    for d in sorted(edir.iterdir()) if edir.is_dir() else []:
        if not d.is_dir():
            continue
        readme = d / "README.md"
        if not readme.exists():
            p.error(d, "has no README.md")
            continue
        fm, body = read_front(readme, p)
        if fm is None:
            continue
        e = dict(fm)
        e["_path"] = readme
        if e.get("id") != d.name:
            p.error(readme, f"id {e.get('id')!r} doesn't match its folder name {d.name!r}")
            e["id"] = d.name
        m = EXP_ID.match(e["id"])
        if not m:
            p.error(readme, f"id {e['id']!r} should look like E-YYYY-MM-DD-<slug>")
        elif e.get("date") and str(e["date"]) != m.group(1):
            p.warn(readme, f"date {e['date']} differs from the date in its id")
        for k in ("thread", "mode", "status", "date", "question"):
            if not e.get(k):
                p.error(readme, f"is missing {k}")
        if e.get("mode") not in (None, "test", "explore"):
            p.error(readme, f"mode {e['mode']!r} should be test or explore")
        if e.get("status") not in (None, "planned", "running", "done", "abandoned", "retracted"):
            p.error(readme, f"status {e['status']!r} should be planned, running, done, abandoned or retracted")
        if e.get("status") == "done" and not e.get("answer"):
            p.error(readme, "is done but has no answer")
        if not e.get("short"):
            p.warn(readme, "has no short name, so sentences that mention it use its id")
        if e.get("prediction") and e.get("mode") == "explore":
            p.warn(readme, "has a prediction, but predictions belong to test mode")
        for fpath in sorted((d / "figs").glob("*.json")) if (d / "figs").is_dir() else []:
            key = f"{e['id']}/{fpath.stem}"
            bad.add(key)
            try:
                fig = json.loads(fpath.read_text(encoding="utf-8"))
            except json.JSONDecodeError as err:
                p.error(fpath, f"isn't valid JSON: {err}")
                continue
            if not isinstance(fig, dict):
                p.error(fpath, "should be a JSON object")
                continue
            view = fig.get("view")
            if view not in VIEWS:
                p.error(fpath, f"unknown figure view {view!r}; use one of {', '.join(sorted(VIEWS))}")
                continue
            if view == "table":
                if not isinstance(fig.get("head"), list) or not isinstance(fig.get("rows"), list):
                    p.error(fpath, "a table needs a head list and a rows list")
            elif not isinstance(fig.get("options"), dict):
                p.error(fpath, f"a {view} figure needs an options object, the arguments of {view}()")
            fig["title"] = md.inline(fig.get("title"), fpath)
            fig["caption"] = md.inline(fig.get("caption"), fpath)
            if view == "table":
                fig["rows"] = [[md.inline(c, fpath) if isinstance(c, str) else c for c in r] for r in fig.get("rows", [])]
                fig["head"] = [md.inline(c, fpath) if isinstance(c, str) else c for c in fig.get("head", [])]
            figs[key] = fig
            bad.discard(key)

        # The write-up: one entry per ## section, in the mode's order.
        chunks = re.split(r"^##[ \t]+(.+?)[ \t]*$", body, flags=re.M)
        if chunks[0].strip():
            p.warn(readme, "has text before its first ## heading, which the notebook doesn't show")
        found = {}
        for i in range(1, len(chunks), 2):
            label = chunks[i].strip()
            if label in found:
                p.error(readme, f"has two ## {label} sections")
            out, used = md.block(chunks[i + 1], readme)
            for name in used:
                if f"{e['id']}/{name}" not in figs and f"{e['id']}/{name}" not in bad:
                    p.error(readme, f"::fig {name} has no file figs/{name}.json")
            found[label] = out
        order = SECTIONS.get(e.get("mode"), [])
        extra = [k for k in found if k not in order]
        for k in extra:
            p.warn(readme, f"## {k} isn't one of the {e.get('mode')} sections ({', '.join(order)}); it's shown after them")
        e["sections"] = [{"label": k, "parts": split_bleed(found[k], e["id"], figs)} for k in order + extra if k in found]
        e["_text"] = " ".join(strip_tags(v) for v in found.values())
        exps.append(e)

    ids = {e["id"]: e for e in exps}

    # Threads.
    tdir = root / "threads"
    fids, qids = {}, {}
    for f in sorted(tdir.glob("*.md")) if tdir.is_dir() else []:
        fm, _notes = read_front(f, p)
        if fm is None:
            continue
        t = dict(fm)
        t["_path"] = f
        if t.get("id") != f.stem:
            p.error(f, f"thread id {t.get('id')!r} doesn't match its file name {f.stem!r}")
            t["id"] = f.stem
        if not THREAD_ID.match(t["id"]):
            p.error(f, f"thread id {t['id']!r} should be a short kebab-case slug")
        if not t.get("title"):
            p.error(f, "is missing title")
        for key in ("findings", "next", "history"):
            if t.get(key) is None:
                t[key] = []
            elif not isinstance(t[key], list):
                p.error(f, f"{key} should be a list")
                t[key] = []
        for fd in t["findings"]:
            fid = fd.get("id", "")
            if not F_ID.match(str(fid)):
                p.error(f, f"finding id {fid!r} should look like F-<slug>")
            if fid in fids:
                p.error(f, f"finding {fid} is also in {fids[fid]}; finding ids are unique across the repo")
            fids[fid] = f.name
            for k in ("status", "strength", "date", "claim"):
                if not fd.get(k):
                    p.error(f, f"finding {fid} is missing {k}")
            if fd.get("status") not in (None, "current", "superseded", "retracted"):
                p.error(f, f"finding {fid}: status {fd['status']!r} should be current, superseded or retracted")
            if fd.get("strength") not in (None, "strong", "moderate", "tentative"):
                p.error(f, f"finding {fid}: strength {fd['strength']!r} should be strong, moderate or tentative")
            if fd.get("status") == "retracted" and not fd.get("retracted"):
                p.error(f, f"finding {fid} is retracted but doesn't say why (retracted: ...)")
            if fd.get("status") == "superseded" and not fd.get("replaced_by"):
                p.warn(f, f"finding {fid} is superseded but doesn't say what replaced it (replaced_by: ...)")
            ev = fd.get("evidence") or []
            if not ev:
                p.error(f, f"finding {fid} cites no experiments (evidence: ...)")
            fd["evidence"] = []
            for x in ev:
                x = x if isinstance(x, dict) else {"experiment": x}
                if x.get("experiment") not in ids:
                    p.error(f, f"finding {fid} cites experiment {x.get('experiment')!r}, which doesn't exist")
                fd["evidence"].append(x)
            if fd.get("figure"):
                if fd["figure"] not in figs and fd["figure"] not in bad:
                    p.error(f, f"finding {fid}: figure {fd['figure']!r} doesn't exist (expected experiments/<id>/figs/<name>.json)")
            for k in ("claim", "method", "confidence", "caveats", "implication", "retracted"):
                fd[k] = md.inline(fd.get(k), f)
        for q in t["next"]:
            qid = q.get("id", "")
            if not Q_ID.match(str(qid)):
                p.error(f, f"next item id {qid!r} should look like Q-<slug>")
            if qid in qids:
                p.error(f, f"next item {qid} is also in {qids[qid]}")
            qids[qid] = f.name
            if not q.get("question"):
                p.error(f, f"next item {qid} is missing question")
            if q.get("state", "open") not in ("open", "running", "parked"):
                p.error(f, f"next item {qid}: state {q.get('state')!r} should be open, running or parked")
            q["state"] = q.get("state", "open")
            for k in ("experiment", "from"):
                if q.get(k) and q[k] not in ids:
                    p.error(f, f"next item {qid}: {k} {q[k]!r} doesn't exist")
            if q["state"] == "running" and not q.get("experiment"):
                p.warn(f, f"next item {qid} is running but doesn't name its experiment")
            q["_text"] = " ".join(str(q.get(k) or "") for k in ("question", "action", "settles", "parked"))
            for k in ("question", "action", "settles", "parked"):
                q[k] = md.inline(q.get(k), f)
        for h in t["history"]:
            if h.get("experiment") not in ids:
                p.error(f, f"history line on {h.get('date')} names experiment {h.get('experiment')!r}, which doesn't exist")
            if not h.get("line"):
                p.error(f, f"history entry for {h.get('experiment')} has no line")
            h["line"] = change_line(md.inline(h.get("line"), f))
        threads.append(t)

    tids = {t["id"]: t for t in threads}
    for t in threads:
        for fd in t["findings"]:
            if fd.get("replaced_by") and fd["replaced_by"] not in fids:
                p.error(t["_path"], f"finding {fd.get('id')}: replaced_by {fd['replaced_by']!r} doesn't exist")
    for e in exps:
        if e.get("thread") and e["thread"] not in tids:
            p.error(e["_path"], f"thread {e['thread']!r} doesn't exist (no threads/{e['thread']}.md)")

    # Front-matter prose for experiments.
    for e in exps:
        path = e["_path"]
        e["_plain"] = " ".join(str(e.get(k) or "") for k in ("id", "short", "question", "answer"))
        e["question"] = md.inline(e.get("question"), path)
        e["answer"] = md.inline(e.get("answer"), path)
        if e.get("mode") == "test":
            e["answer"] = verdict(e["answer"])
        if isinstance(e.get("prediction"), dict):
            pr = e["prediction"]
            pr["text"] = md.inline(pr.get("text"), path)
            pr["how"] = md.inline(pr.get("how"), path)
        e["since"] = [{"date": s.get("date"), "line": md.inline(s.get("line"), path)} for s in (e.get("since") or [])]
        if isinstance(e.get("results"), str):
            e["results"] = [e["results"]]

    # Every in-page link must lead somewhere.
    targets = {"threads", "next", "experiments"} | {f"t-{t}" for t in tids} | set(ids) | set(fids) | set(qids)
    for path, target in md.links:
        if target not in targets:
            p.error(path, f"links to #{target}, which isn't a thread (#t-<id>), experiment, finding or next item")

    glossary = []
    for section, key in (("terms", "term"), ("datasets", "name")):
        for g in gl.get(section) or []:
            forms = [g.get(key)] + list(g.get("synonyms") or [])
            forms = [str(x) for x in forms if x]
            if len(forms) > 1:
                glossary.append(forms)
    return nb, threads, exps, figs, glossary, gl


def split_bleed(out, eid, figs):
    """Splits a section's HTML at full-width figures, which sit between sections rather than inside one."""
    parts, last = [], 0
    for m in re.finditer(r'<div class="nb-fig" data-fig="([^"]+)"></div>', out):
        key = f"{eid}/{html.unescape(m.group(1))}"
        if figs.get(key, {}).get("bleed"):
            parts.append({"html": out[last:m.start()]})
            parts.append({"bleed": key})
            last = m.end()
    parts.append({"html": out[last:]})
    for part in parts:
        if "html" in part:
            part["html"] = re.sub(r'<div class="nb-fig" data-fig="([^"]+)"></div>',
                                  lambda m: f'<div class="nb-fig" data-fig="{eid}/{m.group(1)}"></div>', part["html"])
    return [x for x in parts if x.get("bleed") or x["html"].strip()]


def derive(threads, exps):
    """What the notebook generates rather than stores: who cites what, and each experiment's dated lines since."""
    ids = {e["id"]: e for e in exps}
    for e in exps:
        e["findings"] = []
    for t in threads:
        for fd in t["findings"]:
            for x in fd["evidence"]:
                if x.get("experiment") in ids:
                    ids[x["experiment"]]["findings"].append({"id": fd["id"], "role": x.get("role")})
    findings = {fd["id"]: fd for t in threads for fd in t["findings"]}
    for t in threads:
        hist = t["history"]
        for fd in t["findings"]:
            ev = [x["experiment"] for x in fd["evidence"] if x.get("experiment") in ids]
            for eid in ev:
                e = ids[eid]
                # A later change of belief caused by another run this finding rests on.
                for h in hist:
                    if h.get("experiment") in ev and h["experiment"] != eid and str(h.get("date")) > str(e.get("date")):
                        e["since"].append({"date": h["date"], "line": h["line"], "via": h["experiment"]})
                if fd.get("status") == "superseded":
                    new = findings.get(fd.get("replaced_by"))
                    line = f'The finding it supports was replaced by <a href="#{new["id"]}">{html.escape(new.get("short") or new["id"])}</a>.' if new else "The finding it supports was superseded."
                    e["since"].append({"date": fd.get("date"), "line": line})
                if fd.get("status") == "retracted":
                    e["since"].append({"date": fd.get("date"), "line": f'<b>The finding it supports was retracted.</b> {fd.get("retracted") or ""}'})
    for e in exps:
        seen, out = set(), []
        for s in sorted(e["since"], key=lambda s: str(s.get("date"))):
            k = (s.get("date"), s.get("line"))
            if k not in seen:
                seen.add(k)
                out.append(s)
        e["since"] = out


def search_text(e, threads):
    t = next((t for t in threads if t["id"] == e.get("thread")), None)
    claims = [strip_tags(fd["claim"]) for t2 in threads for fd in t2["findings"]
              if any(x.get("experiment") == e["id"] for x in fd["evidence"])]
    return " ".join([e["_plain"], t["title"] if t else "", e.get("mode") or "", " ".join(claims), e["_text"]])


# ---------- the kit ----------

def find_kit():
    def ok(d):
        return d and all((d / f).is_file() for f in KIT_FILES)

    if os.environ.get("FD_KIT"):
        d = Path(os.environ["FD_KIT"]).expanduser()
        if not ok(d):
            sys.exit(f"error: FD_KIT is {d}, which doesn't hold {', '.join(KIT_FILES)}")
        return {f: (d / f).read_text(encoding="utf-8") for f in KIT_FILES}, str(d)
    plugins = Path.home() / ".claude" / "plugins"
    if plugins.is_dir():
        hits = [h.parent for h in plugins.glob("**/skills/functional-design/references/base.css") if ok(h.parent)]
        if hits:
            d = max(hits, key=lambda h: (h / "base.css").stat().st_mtime)
            return {f: (d / f).read_text(encoding="utf-8") for f in KIT_FILES}, str(d)
    d = (Path(__file__).resolve().parents[1] / "../../../style/skills/functional-design/references").resolve()
    if ok(d):
        return {f: (d / f).read_text(encoding="utf-8") for f in KIT_FILES}, str(d)
    out = {}
    for f in KIT_FILES:
        try:
            with urllib.request.urlopen(KIT_URL.format(f), timeout=30) as r:
                out[f] = r.read().decode("utf-8")
        except Exception as err:
            sys.exit(f"error: couldn't find the functional-design kit locally or download {f}: {err}. Set FD_KIT to its references folder.")
    return out, "xycoord/claude-skills main (downloaded)"


# ---------- the page ----------

def git_commit(root: Path):
    try:
        run = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
        if Path(run("rev-parse", "--show-toplevel")).resolve() != root:
            return None
        return run("rev-parse", "--short", "HEAD") or None
    except Exception:
        return None


def build(root: Path, kit):
    p = Problems(root)
    nb, threads, exps, figs, glossary, _gl = load(root, p)
    if not p.errors:
        derive(threads, exps)
    for e in exps:
        e["search"] = search_text(e, threads)
    clean = lambda x: {k: v for k, v in x.items() if not k.startswith("_")}
    data = {
        "title": nb.get("title") or "Research notebook",
        "repo": nb.get("repo") or "xycoord/ai-research",
        "results": nb.get("results") or "xycoord/research-results",
        "last_visit": nb.get("last_visit"),
        "built": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M"),
        "commit": git_commit(root),
        "threads": [{**clean(t), "file": f"threads/{t['id']}.md"} for t in threads],
        "experiments": sorted([clean(e) for e in exps], key=lambda e: (str(e.get("date")), e["id"]), reverse=True),
        "figs": figs,
        "glossary": glossary,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
    title = html.escape(data["title"])
    page = PAGE
    for k, v in {"%TITLE%": title, "%BASECSS%": kit["base.css"], "%CSS%": CSS, "%DATA%": blob,
                 "%BASEJS%": kit["base.js"], "%CHARTSJS%": kit["charts.js"], "%INTERPJS%": kit["interp.js"], "%JS%": JS}.items():
        page = page.replace(k, v)
    return page, p, data


PAGE = """<title>%TITLE%</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Albert+Sans:wght@400;500;600&family=Fira+Code:wght@400;500&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&text=0123456789-&display=swap">
<style>
%BASECSS%
/* ---------- the notebook's own additions ---------- */
%CSS%
</style>
<header class="top"><div class="wrap">
  <a class="brand" href="#threads">%TITLE%</a>
  <span class="status" id="nb-live"></span>
  <nav class="tabs" aria-label="Views"><a href="#threads">Threads</a><a href="#next">Next</a><a href="#experiments">Experiments</a></nav>
</div></header>
<main class="wrap" id="view"></main>
<footer class="wrap" id="nb-foot"></footer>
<!-- Built by the record skill's build_notebook.py from the research repo. Never edit this page by hand: change the repo and rebuild. -->
<script type="application/json" id="nb-data">%DATA%</script>
<script>
%BASEJS%
</script>
<script>
%CHARTSJS%
</script>
<script>
%INTERPJS%
</script>
<script>
%JS%
</script>
"""

CSS = r"""
main { padding-block: 36px 64px; }
.mg, section[id], li[id] { scroll-margin-top: 72px; }
.nb-page > * + * { margin-top: 28px; }
.nb-sub { font-size: 14px; color: var(--muted); margin-top: 8px; max-width: 640px; }
.mg > .ml .nb-new { color: var(--ink); font-weight: 600; }
.md > * + * { margin-top: 10px; }
.md > figure, .md > .tablewrap, .md > figure + * { margin-top: 18px; }
.md ul { list-style: disc; padding-left: 22px; }
.md ol { list-style: decimal; padding-left: 22px; }
.md li + li { margin-top: 4px; }
.md h3 { font-size: 16px; font-weight: 600; margin-top: 20px; }
.md blockquote { border-left: 2px solid var(--line-2); padding-left: 14px; color: var(--ink-2); }
.mc.wide > :not(figure):not(.tablewrap) { max-width: 640px; }
figure.bleed { margin-top: 28px; }
.nb-home { display: grid; gap: 44px; }
.nb-thread { display: grid; gap: 12px; }
.nb-thread h2 { font-size: 17px; }
.nb-thread .nb-claim { font-weight: 400; }
.nb-thread .nb-fig-home { margin-top: 12px; }
.nb-ev li + li { margin-top: 4px; }
.nb-ev { margin-top: 10px; font-size: 15px; }
details.nb-earlier { margin-top: 16px; }
details.nb-earlier > summary { cursor: pointer; color: var(--accent); font-size: 15px; list-style: none; display: inline-block; }
details.nb-earlier > summary::-webkit-details-marker { display: none; }
details.nb-earlier[open] > summary { margin-bottom: 18px; }
.nb-search label { color: var(--ink); font-size: 15px; font-weight: 600; }
.nb-search input { max-width: 640px; margin-top: 2px; }
.nb-also { font-size: 14px; color: var(--muted); margin-top: 8px; }
.nb-list > li + li { margin-top: 18px; }
.nb-gone .t { color: var(--muted); }
.rows .nb-tl { color: var(--muted); font-size: 14px; margin-top: 2px; }
.md blockquote p + p, .md blockquote + blockquote { margin-top: 8px; }
.dbody .id, .dbody code { white-space: normal; overflow-wrap: anywhere; }
"""

JS = r"""
// The notebook's rendering script. The data above is generated from the research repo by build_notebook.py;
// everything on the page is drawn from it, so the page is never edited by hand.
const NB = JSON.parse(document.getElementById("nb-data").textContent);
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const day = iso => { if (!iso) return ""; const [, m, d] = String(iso).split("-"); return `${+d} ${MON[+m - 1]}`; };
const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : "";
const EXP = Object.fromEntries(NB.experiments.map(e => [e.id, e]));
const THR = Object.fromEntries(NB.threads.map(t => [t.id, t]));
const FND = {}, QS = {};
NB.threads.forEach(t => { t.findings.forEach(f => { f.thread = t.id; FND[f.id] = f; }); t.next.forEach(q => { q.thread = t.id; QS[q.id] = q; }); });
const shortOf = e => e.short || e.id;
const isNew = iso => NB.last_visit && iso && String(iso) > String(NB.last_visit);
const builtDay = day(NB.built.slice(0, 10));
const GH = path => `https://github.com/${NB.repo}/${path}`;
const HF = path => `https://huggingface.co/datasets/${NB.results}/tree/main/${String(path).replace(/^\/+/, "")}`;

const sec = (label, body, o = {}) => `<section class="mg"${o.id ? ` id="${o.id}"` : ""}><div class="ml">${label}</div><div class="mc${o.wide ? " wide" : ""}${o.md ? " md" : ""}">${body}</div></section>`;
const two = (a, b) => `<span>${a}</span>${b ? `<span>${b}</span>` : ""}`;
const head = (crumb, title, sub) => `<div class="mg"><div class="ml"></div><div class="mc">${crumb ? `<p class="crumb">${crumb}</p>` : ""}<h1>${title}</h1>${sub ? `<p class="nb-sub">${sub}</p>` : ""}</div></div>`;
const up = (href, text) => `<a href="${href}" data-up>${text}</a>`;
const weeds = body => `<div class="mg"><div class="ml"></div><div class="mc"><details class="more" data-remember><summary>Code, data and records</summary><div class="dbody">${body}</div></details></div></div>`;
const block = (h, body) => body ? `<div><h2>${h}</h2>${body}</div>` : "";
const kv = rows => { const r = rows.filter(x => x && x[1]); return r.length ? `<dl class="kv">${r.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>` : ""; };
const strengthWord = f => cap(f.strength);
// A finding's dated status: when it was written or raised, marked when that's newer than the last visit.
const fstatus = f => { const w = f.raised ? "Raised" : isNew(f.date) ? "New" : "Since"; return isNew(f.date) ? `<span class="nb-new">${w} ${day(f.date)}</span>` : `${w} ${day(f.date)}`; };
const gpu = q => q.cost_gpu_min ? `<span class="muted nw">, ${q.cost_gpu_min}&nbsp;GPU-min</span>` : "";
// A step to take: the action and its cost as one sentence, then what its result would settle.
const step = q => { const a = String(q.action || q.question || "").replace(/\.$/, ""); return `${a}${gpu(q)}.${q.settles ? " " + q.settles : ""}`; };
const expLink = (id, text) => EXP[id] ? `<a href="#${id}">${text || esc(shortOf(EXP[id]))}</a>` : `<span class="id">${esc(id)}</span>`;
const threadActivity = t => [...t.findings.map(f => f.date), ...t.history.map(h => h.date), ...NB.experiments.filter(e => e.thread === t.id).map(e => e.date)].map(String).sort().pop() || "";
const threadsByActivity = () => [...NB.threads].sort((a, b) => threadActivity(b).localeCompare(threadActivity(a)));
const runningExps = () => NB.experiments.filter(e => e.status === "running");

// ---------- figures: the arguments of one call into the design kit ----------
const fmtOf = o => {
  if (o.digits == null && !o.prefix && !o.suffix && !o.percent) return undefined;
  const d = o.digits ?? (o.percent ? 0 : 2);
  return v => `${o.prefix || ""}${(o.percent ? v * 100 : v).toFixed(d)}${o.percent ? "%" : ""}${o.suffix || ""}`;
};
const figHtml = key => {
  const F = NB.figs[key];
  if (!F) return `<p class="err">Missing figure ${esc(key)}</p>`;
  return `<figure${F.bleed ? ` class="bleed"` : ""}>${F.title ? `<div class="ftitle">${F.title}</div>` : ""}<div class="nb-slot" data-fig="${esc(key)}"></div>${F.caption ? `<figcaption>${F.caption}</figcaption>` : ""}</figure>`;
};
const withFigs = s => s.replace(/<div class="nb-fig" data-fig="([^"]+)"><\/div>/g, (_, k) => figHtml(k.replace(/&amp;/g, "&")));
function tableHtml(F) {
  const num = F.numeric || [];
  // JSON drops trailing zeros (0.80 arrives as 0.8), so each column's numbers get the most decimals any of them has,
  // unless the figure sets digits.
  const dec = v => typeof v === "number" && !Number.isInteger(v) ? String(v).split(".")[1].length : 0;
  const places = F.head.map((_, i) => F.digits ?? Math.max(0, ...F.rows.map(r => dec(r[i]))));
  const show = (v, i) => typeof v === "number" ? v.toLocaleString("en-GB", { minimumFractionDigits: places[i], maximumFractionDigits: places[i] }) : v;
  const cell = (v, i, tag) => `<${tag}${num[i] ? ` class="r"` : ""}>${v == null ? "" : tag === "td" ? show(v, i) : v}</${tag}>`;
  return `<div class="tablewrap"><table${F.main ? ` class="main"` : ""}><thead><tr>${F.head.map((h, i) => cell(h, i, "th")).join("")}</tr></thead><tbody>${F.rows.map(r => `<tr>${r.map((v, i) => cell(v, i, "td")).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function drawFigs(root) {
  root.querySelectorAll(".nb-slot:not([data-drawn])").forEach(el => {
    el.dataset.drawn = "1";
    const F = NB.figs[el.dataset.fig]; if (!F) return;
    try {
      if (F.view === "table") { el.innerHTML = tableHtml(F); return; }
      const o = { ...F.options }, fmt = fmtOf(o); if (fmt) o.fmt = fmt;
      if (F.view === "heatmap" && o.mask === "causal") o.mask = (i, j) => j > i;
      else if (F.view === "heatmap") delete o.mask;
      if (F.view === "graph") el.classList.add("tablewrap");
      ({ dotChart, lineChart, barChart, distChart, tokenText, topExamples, heatmap, lensExplorer, logitLens, graph })[F.view](el, o);
    } catch (err) { el.innerHTML = `<p class="err">This figure couldn't be drawn: ${esc(err.message)}</p>`; }
  });
}
// The numbers behind a chart, for the bookkeeping disclosure.
function valuesTable(key) {
  const F = NB.figs[key]; if (!F) return "";
  const o = F.options || {}, f = fmtOf(o) || (v => typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : esc(v));
  const t = (h, rows) => `<div class="tablewrap"><table><thead><tr>${h.map((x, i) => `<th${i ? ` class="r"` : ""}>${esc(x)}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr>${r.map((x, i) => `<td${i ? ` class="r"` : ""}>${x}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  const title = `<p class="small muted">${F.title || esc(key)}</p>`;
  if (F.view === "dotChart") return title + t(["", o.metric || "Value", "Range"], [...(o.rows || []), ...(o.refs || [])].map(d => [esc(d.label), f(d.v), d.lo != null ? `${f(d.lo)}–${f(d.hi)}` : ""]));
  if (F.view === "lineChart") return title + t([o.xLabel || "x", ...o.series.map(s => s.name)], o.x.map((x, i) => [esc(x), ...o.series.map(s => s.ys[i] == null ? "" : f(s.ys[i]))]));
  if (F.view === "barChart") return title + t(["", ...o.parts.map(p => p.name)], o.cats.map((c, i) => [esc(c), ...o.parts.map(p => f(p.values[i]))]));
  return "";
}

// ---------- the Threads home ----------
function viewHome() {
  if (!NB.threads.length) return `<div class="nb-page">${head("", "No threads yet")}${sec("", `<p>A thread is one research question, written as a file in <code>threads/</code> of the research repo. Once one is merged to <code>main</code> and the notebook is rebuilt, it appears here with its findings.</p>`)}</div>`;
  const row = (ml, mc) => `<div class="mg"><div class="ml">${ml}</div><div class="mc">${mc}</div></div>`;
  const blocks = threadsByActivity().map(t => {
    const cur = t.findings.filter(f => f.status === "current");
    let h = row("", `<h2><a class="item" href="#t-${t.id}"><span class="t">${esc(t.title)}</span></a></h2>`);
    if (cur.length) h += cur.map(f => row(two(strengthWord(f), fstatus(f)), `<a class="item" href="#${f.id}"><span class="t nb-claim">${f.claim}</span></a>${isNew(f.date) && f.figure ? `<div class="nb-fig-home">${figHtml(f.figure)}</div>` : ""}`)).join("");
    else {
      const r = t.findings.find(f => f.status === "retracted");
      h += row("No finding", `<p class="muted">${r ? `No finding yet. The one written was retracted on ${day(r.date)}.` : "No finding yet."}</p>`);
    }
    const nl = nextLine(t); if (nl) h += row(nl[0], `<p>${nl[1]}</p>`);
    return `<section class="nb-thread">${h}</section>`;
  });
  return `<div class="nb-home">${blocks.join("")}</div>`;
}
// One line for the home page: what's running, else the first open step with its cost, else what's parked.
function nextLine(t) {
  const run = t.next.find(q => q.state === "running"), open = t.next.filter(q => q.state === "open"), parked = t.next.filter(q => q.state === "parked");
  const more = n => n > 0 ? ` <span class="muted">${n} more ${n > 1 ? "steps" : "step"} open.</span>` : "";
  if (run) { const e = EXP[run.experiment]; return ["Running", `${e ? cap(esc(shortOf(e))) + ", since " + day(e.date) : run.question}.${more(open.length)}`]; }
  if (open.length) { const q = open[0], a = String(q.action || q.question).replace(/\.$/, ""); return ["Next", `${a}${gpu(q)}.${more(open.length - 1)}`]; }
  if (parked.length) return ["Parked", `${parked[0].question}${parked[0].parked ? ` <span class="muted">${cap(parked[0].parked)}.</span>` : ""}`];
  return null;
}

// ---------- a thread ----------
function viewThread(t) {
  const cur = t.findings.filter(f => f.status === "current"), old = t.findings.filter(f => f.status !== "current");
  const contents = cur.length > 1 ? `<nav class="contents" aria-label="Findings">${cur.map(f => `<a href="#${f.id}">${esc(f.short || f.id)}</a>`).join("")}</nav>` : "";
  let h = head(up("#threads", "Threads"), esc(t.title)) + (contents ? `<div class="mg"><div class="ml"></div><div class="mc">${contents}</div></div>` : "");
  if (!cur.length) h += sec("Finding", `<p class="lead">None yet.${old.some(f => f.status === "retracted") ? " The one written was retracted; it's at the end of this page." : ""}</p>`);
  cur.forEach(f => {
    h += sec(two(strengthWord(f), fstatus(f)), `<p class="lead">${f.claim}</p>`, { id: f.id });
    if (f.figure) h += NB.figs[f.figure] && NB.figs[f.figure].bleed ? figHtml(f.figure) : sec("Result", figHtml(f.figure), { wide: true });
    const ev = f.evidence.map(x => { const e = EXP[x.experiment]; return e ? `<li><span class="d">${day(e.date)}</span><span>${expLink(e.id, cap(esc(shortOf(e))))}${x.role ? `<span class="muted">, ${esc(x.role)}</span>` : ""}</span></li>` : ""; }).join("");
    h += sec("Method", `${f.method ? `<p>${f.method}</p>` : ""}<ul class="log nb-ev">${ev}</ul>`);
    if (f.confidence) h += sec("Confidence", `<p>${f.confidence}</p>`);
    if (f.caveats) h += sec("Caveats", `<p>${f.caveats}</p>`);
    if (f.implication) h += sec("Implication", `<p>${f.implication}</p>`);
  });
  h += sec("Next", nextList(t));
  h += sec("History", historyList(t));
  old.forEach(f => {
    const label = f.status === "retracted" ? two(`<span class="crit">Retracted</span>`, day(f.date)) : two("Superseded", day(f.date));
    const why = f.status === "retracted" ? `<p>${f.retracted}</p>` : FND[f.replaced_by] ? `<p>Replaced by <a href="#${f.replaced_by}">${esc(FND[f.replaced_by].short || f.replaced_by)}</a>.</p>` : "";
    const ev = f.evidence.map(x => expLink(x.experiment, esc(shortOf(EXP[x.experiment] || { id: x.experiment })))).join(", ");
    h += sec(label, `<p class="muted">${f.claim}</p>${why}<p class="small muted">From ${ev}.</p>`, { id: f.id });
  });
  const vals = cur.filter(f => f.figure).map(f => valuesTable(f.figure)).join("");
  h += weeds([
    block("Record", kv([["Source", `<a class="id" href="${GH(`blob/main/${t.file}`)}">${esc(t.file)}</a>`],
      ...t.findings.map(f => [f.status === "current" ? "Finding" : cap(f.status), `<span class="id">${esc(f.id)}</span>`]),
      ...t.next.map(q => ["Next", `<span class="id">${esc(q.id)}</span>`])])),
    vals && block("Values", vals),
  ].join(""));
  return `<div class="nb-page">${h}</div>`;
}
// Next, in the thread's own order (by value): what's running, open questions with their cost, parked ones with why.
function nextList(t) {
  if (!t.next.length) return `<p class="muted">Nothing queued as of ${builtDay}.</p>`;
  return `<ul class="rows">${t.next.map(q => {
    let a;
    if (q.state === "running") { const e = EXP[q.experiment]; a = `${e ? `Running as ${expLink(e.id)} since ${day(e.date)}.` : "Running."}${q.settles ? " " + q.settles : ""}`; }
    else if (q.state === "parked") a = `Parked: ${q.parked || "no reason given"}.`;
    else a = step(q);
    if (q.lead) a += ` <span class="muted">A lead from ${q.from ? expLink(q.from) : "looking at data"}, not yet tested.</span>`;
    return `<li id="${q.id}"${q.state === "parked" ? ` class="dim"` : ""}><span class="t">${q.question}</span><p class="a">${a}</p></li>`;
  }).join("")}</ul>`;
}
// History: one row per finished run, newest first, with the change of belief it caused, if any.
function historyList(t) {
  const runs = NB.experiments.filter(e => e.thread === t.id && e.status !== "running" && e.status !== "planned");
  const changes = {}; t.history.forEach(h => (changes[h.experiment] ||= []).push(h));
  Object.keys(changes).forEach(id => { if (EXP[id] && !runs.includes(EXP[id])) runs.push(EXP[id]); });
  runs.sort((a, b) => String(b.date).localeCompare(String(a.date)));
  if (!runs.length) return `<p class="muted">No finished runs yet.</p>`;
  const row = e => `<li${e.status === "retracted" || e.status === "abandoned" ? ` class="dim"` : ""}><span class="d">${day(e.date)}</span><a class="item" href="#${e.id}"><span class="t">${e.question}</span><p class="a">${e.answer || ""}</p>${(changes[e.id] || []).map(c => `<p class="a">${c.line}</p>`).join("")}</a></li>`;
  const shown = runs.slice(0, 6).map(row).join(""), rest = runs.slice(6).map(row).join("");
  return `<ul class="rows log">${shown}</ul>${rest ? `<details class="nb-earlier"><summary>${runs.length - 6} earlier runs</summary><ul class="rows log">${rest}</ul></details>` : ""}`;
}

// ---------- an experiment ----------
function viewExperiment(e) {
  const t = THR[e.thread], explore = e.mode === "explore";
  const when = e.status === "planned" ? `Planned ${day(e.date)}` : e.status === "running" ? `Running since ${day(e.date)}` : `Run ${day(e.date)}`;
  let h = head(up("#experiments", "Experiments"), e.question, `${when}${t ? `, for <a href="#t-${t.id}">${esc(t.title)}</a>` : ""}.`);
  if (e.since.length) h += sec("Since then", `<ul class="log">${e.since.map(s => `<li><span class="d">${day(s.date)}</span><span>${s.via ? `${expLink(s.via, cap(esc(shortOf(EXP[s.via]))))}: ` : ""}${s.line}</span></li>`).join("")}</ul>`);
  const opening = e.answer || (e.status === "planned" ? "Not run yet." : e.status === "running" ? "<b>Not yet.</b> Still running." : "");
  const ml = e.status === "retracted" ? two(explore ? "What was seen" : "Answer", `<span class="crit">Retracted</span>`) : e.status === "abandoned" ? two(explore ? "What was seen" : "Answer", "Abandoned") : explore ? "What was seen" : "Answer";
  if (opening) h += sec(ml, `<p class="lead">${opening}</p>`);
  const S = Object.fromEntries(e.sections.map(s => [s.label, s]));
  const P = e.prediction;
  const pred = P && P.text ? `<p>The prediction, written ${day(P.written)} before the run: ${P.text}${P.held === true ? ` <b>It held:</b> ${P.how || ""}.` : P.held === false ? ` <b>It didn't hold:</b> ${P.how || ""}.` : ""}</p>` : "";
  const done = new Set();
  const body = (label, extra = "") => {
    const s = S[label]; done.add(label);
    if (!s && !extra) return "";
    const parts = s ? s.parts : [];
    const wide = parts.some(p => p.html && /nb-fig|tablewrap/.test(p.html));
    let out = "", buf = "", first = true;
    const flush = () => { out += sec(first ? label : "", withFigs(buf), { wide, md: true }); buf = ""; first = false; };
    parts.forEach(p => { if (p.bleed) { if (buf || first) flush(); out += figHtml(p.bleed); } else buf += p.html; });
    buf += extra;
    if (buf || first) flush();
    return out;
  };
  if (explore) ["Why we looked", "The data", "Patterns", "Looked at and found nothing", "Method"].forEach(l => h += body(l));
  else { h += body("Why we ran it", pred); ["What was compared", "Result", "Method", "Checks", "Examples", "Caveats"].forEach(l => h += body(l)); }
  e.sections.filter(s => !done.has(s.label)).forEach(s => h += body(s.label));
  // Generated: the findings this run supports, or for exploration the leads it handed to the thread's Next.
  const cites = e.findings.map(x => { const f = FND[x.id]; return f ? `<li><a class="item" href="#${f.id}"><span class="t">${f.claim}</span><p class="a">${[x.role && cap(esc(x.role)), f.status === "current" ? `${strengthWord(f)}, since ${day(f.date)}` : `${cap(f.status)} ${day(f.date)}`].filter(Boolean).join(". ")}.</p></a></li>` : ""; }).join("");
  if (cites) h += sec(e.findings.length > 1 ? "Findings" : "Finding", `<ul class="rows">${cites}</ul>`);
  if (explore) {
    const leads = Object.values(QS).filter(q => q.from === e.id);
    h += sec("Leads", leads.length ? `<ul class="rows">${leads.map(q => `<li><a class="item" href="#${q.id}"><span class="t">${q.question}</span><p class="a">${q.state === "running" && EXP[q.experiment] ? `Running as ${esc(shortOf(EXP[q.experiment]))} since ${day(EXP[q.experiment].date)}.` : q.state === "parked" ? `Parked: ${q.parked || ""}.` : step(q)}</p></a></li>`).join("")}</ul>` : `<p class="muted">No leads taken forward from this look.</p>`);
  }
  // Figures in the order the page shows them, then any the write-up doesn't place.
  const placed = e.sections.flatMap(s => s.parts.flatMap(p => p.bleed ? [p.bleed] : [...(p.html || "").matchAll(/data-fig="([^"]+)"/g)].map(m => m[1])));
  const figKeys = [...new Set([...placed, ...Object.keys(NB.figs).filter(k => k.startsWith(e.id + "/")).sort()])].filter(k => NB.figs[k]);
  const vals = figKeys.map(valuesTable).join("");
  h += weeds([
    block("Code", kv([["Commit", e.commit && `<a class="id" href="${GH(`commit/${e.commit}`)}">${esc(e.commit)}</a>`], ["Pull request", e.pr && `<a href="${GH(`pull/${e.pr}`)}">${esc(NB.repo)}#${esc(e.pr)}</a>`], ["Rerun", e.rerun && `<code>${esc(e.rerun)}</code>`]])),
    block("Data", kv([["Results", (e.results || []).map(r => `<a class="id" href="${HF(r)}">${esc(r)}</a>`).join("<br>") || "No results folder"], ["Figures", figKeys.length ? figKeys.map(k => `<span class="id">figs/${esc(k.split("/")[1])}.json</span>`).join("<br>") : ""]])),
    vals && block("Values", vals),
    block("Record", kv([["ID", `<span class="id">${esc(e.id)}</span>`], ["Mode", explore ? "Looking for a hypothesis" : "Testing a hypothesis"], ["Status", cap(e.status)], ["Cost", e.cost_usd != null ? `$${Number(e.cost_usd).toFixed(2)}` : ""], ["Source", `<a class="id" href="${GH(`blob/main/experiments/${e.id}/README.md`)}">experiments/${esc(e.id)}/README.md</a>`]])),
  ].join(""));
  return `<div class="nb-page">${h}</div>`;
}

// ---------- Next, across threads ----------
function viewNext() {
  const order = threadsByActivity(), items = { running: [], open: [], parked: [] };
  order.forEach(t => t.next.forEach(q => items[q.state].push(q)));
  const claimed = new Set(Object.values(QS).map(q => q.experiment).filter(Boolean));
  const loose = NB.experiments.filter(e => (e.status === "running" || e.status === "planned") && !claimed.has(e.id));
  const tline = id => THR[id] ? `<p class="nb-tl">${esc(THR[id].title)}</p>` : "";
  const qrow = q => {
    const e = EXP[q.experiment];
    const a = q.state === "running" ? `${e ? `Running as ${esc(shortOf(e))} since ${day(e.date)}.` : "Running."}${q.settles ? " " + q.settles : ""}` : q.state === "parked" ? `Parked: ${q.parked || ""}.` : step(q);
    return `<li${q.state === "parked" ? ` class="dim"` : ""}><a class="item" href="#${q.state === "running" && e ? e.id : q.id}"><span class="t">${q.question}</span><p class="a">${a}</p>${tline(q.thread)}</a></li>`;
  };
  const erow = e => `<li><a class="item" href="#${e.id}"><span class="t">${e.question}</span><p class="a">${e.status === "running" ? `Running since ${day(e.date)}.` : `Planned ${day(e.date)}.`}</p>${tline(e.thread)}</a></li>`;
  const run = [...items.running.map(qrow), ...loose.filter(e => e.status === "running").map(erow)];
  const open = [...items.open.map(qrow), ...loose.filter(e => e.status === "planned").map(erow)];
  const parked = items.parked.map(qrow);
  let h = head("", "What's next", `Gathered from each thread's Next, as of ${builtDay}. Within a thread, the order is the thread's own, best first.`);
  if (!run.length && !open.length && !parked.length) h += sec("", `<p>Nothing is running or queued as of ${builtDay}. Steps are added to a thread's <code>next</code> list in the research repo.</p>`);
  if (run.length) h += sec("Running", `<ul class="rows">${run.join("")}</ul>`);
  if (open.length) h += sec("Open", `<ul class="rows">${open.join("")}</ul>`);
  if (parked.length) h += sec("Parked", `<ul class="rows">${parked.join("")}</ul>`);
  return `<div class="nb-page">${h}</div>`;
}

// ---------- Experiments, with search ----------
// Search expands a query through the glossary's synonyms, so "mean aggregation" also finds mean-pool.
const norm = s => " " + String(s).toLowerCase().replace(/[^a-z0-9%.]+/g, " ").replace(/\s+/g, " ").trim() + " ";
const GROUPS = NB.glossary.map(forms => ({ forms, keys: forms.map(f => norm(f).trim()) }));
const HAY = Object.fromEntries(NB.experiments.map(e => [e.id, norm(e.search)]));
const QHAY = Object.fromEntries(Object.values(QS).map(q => [q.id, norm(q._text || "")]));
function parseQuery(q) {
  let s = norm(q); const reqs = [];
  const phrases = GROUPS.flatMap(g => g.keys.map(k => [k, g])).filter(([k]) => k).sort((a, b) => b[0].length - a[0].length);
  for (const [k, g] of phrases) while (s.includes(" " + k + " ")) { s = s.replace(" " + k + " ", " "); reqs.push({ alts: g.keys, said: k, g }); }
  s.trim().split(" ").filter(Boolean).forEach(w => reqs.push({ alts: [w] }));
  return reqs;
}
const matches = (hay, reqs) => reqs.every(r => r.alts.some(a => r.g ? hay.includes(" " + a) : hay.includes(a)));
let QUERY = "";
function results() {
  const reqs = parseQuery(QUERY), any = reqs.length > 0;
  const exps = NB.experiments.filter(e => matches(HAY[e.id], reqs));
  const qs = any ? Object.values(QS).filter(q => q.state !== "running" && matches(QHAY[q.id], reqs)) : [];
  const and = xs => xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
  const also = reqs.filter(r => r.g).map(r => `“${esc(r.said)}” also matches ${and(r.g.forms.filter(f => norm(f).trim() !== r.said).map(esc))}.`);
  let h = also.length ? `<p class="nb-also">${also.join(" ")}</p>` : "";
  if (!NB.experiments.length && !any) return `<p class="muted" style="margin-top:12px">No experiments yet. Each one is a folder in <code>experiments/</code> of the research repo, and appears here once it's merged and the notebook is rebuilt.</p>`;
  if (!exps.length && !qs.length) return h + `<p style="margin-top:12px">Nothing matches “${esc(QUERY.trim())}”. As far as the notebook knows, it hasn't been run or queued.</p>`;
  const qrow = q => `<li class="mg${q.state === "parked" ? " dim" : ""}"><div class="ml">${q.state === "parked" ? "Parked" : "Not run yet"}</div><div class="mc"><a class="item" href="#${q.id}"><span class="t">${q.question}</span><p class="a">${q.state === "parked" ? `Parked: ${q.parked || ""}.` : step(q)}</p></a></div></li>`;
  const erow = e => `<li class="mg${e.status === "retracted" || e.status === "abandoned" ? " dim" : ""}"><div class="ml">${two(day(e.date), e.status === "running" ? "Running" : e.status === "planned" ? "Planned" : e.status === "retracted" ? `<span class="crit">Retracted</span>` : e.status === "abandoned" ? "Abandoned" : "")}</div><div class="mc"><a class="item" href="#${e.id}"><span class="t">${e.question}</span><p class="a">${e.answer || (e.status === "running" ? `Running since ${day(e.date)}.` : e.status === "planned" ? "Not run yet." : "")}</p></a></div></li>`;
  return h + `<ul class="rows nb-list" style="margin-top:20px">${qs.map(qrow).join("")}${exps.map(erow).join("")}</ul>`;
}
function viewExperiments() {
  return `<div class="nb-page"><div class="mg"><div class="ml"></div><div class="mc nb-search"><label>Have I tested this?<input type="search" id="nb-q" value="${esc(QUERY)}" placeholder="Search experiments and queued questions" autocomplete="off"></label></div></div><div id="nb-results">${results()}</div></div>`;
}
document.addEventListener("input", ev => { if (ev.target.id === "nb-q") { QUERY = ev.target.value; const r = document.getElementById("nb-results"); r.innerHTML = results(); } });

// ---------- routing: one hash per view, and a way back on every page ----------
function resolve(hash) {
  const id = decodeURIComponent(hash.replace(/^#/, "")) || "threads";
  if (id === "threads") return { tab: "threads", html: viewHome };
  if (id === "next") return { tab: "next", html: viewNext };
  if (id === "experiments") return { tab: "experiments", html: viewExperiments };
  if (id.startsWith("t-") && THR[id.slice(2)]) return { tab: "threads", html: () => viewThread(THR[id.slice(2)]) };
  if (EXP[id]) return { tab: "experiments", html: () => viewExperiment(EXP[id]) };
  if (FND[id]) return { tab: "threads", html: () => viewThread(THR[FND[id].thread]), target: id };
  if (QS[id]) return { tab: "threads", html: () => viewThread(THR[QS[id].thread]), target: id };
  return { tab: null, html: () => `<div class="nb-page">${head(up("#threads", "Threads"), "Nothing here", `<span class="id">#${esc(id)}</span> isn't a page in this notebook. It may have been renamed or removed.`)}</div>` };
}
const KEY = "logan-details-open";
function render() {
  const r = resolve(location.hash), view = document.getElementById("view");
  view.innerHTML = r.html();
  document.querySelectorAll(".tabs a").forEach(a => a.getAttribute("href") === "#" + r.tab ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  // The bookkeeping disclosure stays open once opened, as in base.js, which only sees the page as first loaded.
  let open = false; try { open = localStorage.getItem(KEY) === "1"; } catch (e) {}
  view.querySelectorAll("details[data-remember]").forEach(d => { d.open = open; d.addEventListener("toggle", () => { try { localStorage.setItem(KEY, d.open ? "1" : "0"); } catch (e) {} }); });
  drawFigs(view);
  return r;
}
// Each history entry remembers its depth in the page and its scroll position, so a way-back link returns
// through the history to where the reader was, and opens its parent page when there's nothing to go back to.
const state = () => history.state || {};
const save = extra => { try { history.replaceState({ ...state(), ...extra }, ""); } catch (e) {} };
let depth = 0, scrollT;
history.scrollRestoration = "manual";
addEventListener("hashchange", () => {
  const fresh = history.state == null || history.state.d == null;
  if (fresh) save({ d: depth + 1, y: 0 });
  depth = state().d;
  const r = render();
  const el = r.target && document.getElementById(r.target);
  if (fresh) { if (el) el.scrollIntoView(); else scrollTo(0, 0); }
  else scrollTo(0, state().y || 0);
});
addEventListener("scroll", () => { clearTimeout(scrollT); scrollT = setTimeout(() => save({ y: scrollY }), 150); }, { passive: true });
document.addEventListener("click", ev => {
  const a = ev.target.closest && ev.target.closest("a[data-up]");
  if (a && depth > 0) { ev.preventDefault(); history.back(); }
});

// ---------- header, footer, first draw ----------
(() => {
  const run = runningExps(), live = document.getElementById("nb-live");
  if (run.length === 1) live.innerHTML = `<a href="#${run[0].id}">1 experiment running, as of ${builtDay}</a>`;
  else if (run.length) live.innerHTML = `<a href="#next">${run.length} experiments running, as of ${builtDay}</a>`;
  else live.remove();
  const when = `${day(NB.built.slice(0, 10))} ${NB.built.slice(0, 4)}, ${NB.built.slice(11, 16)} UTC`;
  document.getElementById("nb-foot").innerHTML = `Built ${when} from <span class="id">${esc(NB.repo.split("/").pop())}${NB.commit ? "@" + esc(NB.commit) : ""}</span>. This page is generated from the research repo; change the repo, not the page.`;
  if (state().d == null) save({ d: 0, y: 0 });
  depth = state().d || 0;
  const r = render(), el = r.target && document.getElementById(r.target);
  if (el) el.scrollIntoView(); else if (state().y) scrollTo(0, state().y);
})();
"""


def main():
    ap = argparse.ArgumentParser(description="Build the research notebook page from a research repo.")
    ap.add_argument("repo", help="the research repo's folder (holds threads/, experiments/, glossary.yaml, notebook.yaml)")
    ap.add_argument("-o", "--out", default="notebook.html", help="where to write the page (default notebook.html)")
    a = ap.parse_args()
    root = Path(a.repo).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"error: {root} isn't a folder")
    kit, where = find_kit()
    page, p, data = build(root, kit)
    for w in p.warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in p.errors:
        print(f"error: {e}", file=sys.stderr)
    if p.errors:
        sys.exit(f"{len(p.errors)} error(s); nothing written.")
    Path(a.out).write_text(page, encoding="utf-8")
    print(f"Wrote {a.out}: {len(data['threads'])} threads, {len(data['experiments'])} experiments, "
          f"{len(data['figs'])} figures, {len(page) // 1024} KB. Kit from {where}.")


if __name__ == "__main__":
    main()
