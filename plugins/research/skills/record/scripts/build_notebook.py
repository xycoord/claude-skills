#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6", "markdown>=3.5"]
# ///
"""Build the research notebook page from a research repo.

    uv run <record skill>/scripts/build_notebook.py <repo-dir> -o notebook.html            a preview of any checkout
    uv run <record skill>/scripts/build_notebook.py <repo-dir> -o notebook.html --publish  the page to publish

Reads threads/, experiments/, glossary.yaml and notebook.yaml (the format is in
references/format.md beside this script's folder) and writes one self-contained
page for the claude.ai artifact: the functional-design kit pasted in, the
notebook's data embedded as JSON, and the script that renders it. The page has
no doctype, html, head or body tags, because the artifact publisher adds them.

With --publish, it refuses to build unless the repo is a clean checkout of
origin/main, so the published page always matches main. Without it, the page's
footer says it's a preview of the branch it was built from.

The kit (base.css, base.js, charts.js, interp.js) is found in this order:
  1. the folder named by the FD_KIT environment variable;
  2. the style plugin beside this one in the same checkout or plugin install,
     at ../../../style/skills/functional-design/references from the record
     skill's folder, so the kit is the same version as this script;
  3. the newest installed style plugin under ~/.claude/plugins/;
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
# Each view and the options it can't draw without: (key, type).
VIEWS = {
    "dotChart": [("rows", list)],
    "lineChart": [("x", list), ("series", list)],
    "barChart": [("cats", list), ("parts", list)],
    "distChart": [("upper", dict), ("lower", dict)],
    "tokenText": [("tokens", list)],
    "topExamples": [("examples", list)],
    "heatmap": [("rows", list), ("cols", list), ("values", list)],
    "lensExplorer": [("tokens", list), ("layers", list), ("top", list)],
    "logitLens": [("tokens", list), ("layers", list), ("top", list)],
    "graph": [("columns", list), ("edges", list)],
    "table": [],
}
# Keys every item of a list option needs, where a missing one would stop the chart drawing.
ITEM_KEYS = {
    ("dotChart", "rows"): ["label", "v"], ("dotChart", "refs"): ["label", "v"], ("dotChart", "lines"): ["v"],
    ("lineChart", "series"): ["name", "ys"], ("lineChart", "lines"): ["v"],
    ("barChart", "parts"): ["name", "values"], ("barChart", "lines"): ["v"],
    ("topExamples", "examples"): ["tokens", "max"], ("graph", "columns"): ["label", "nodes"], ("graph", "edges"): ["from", "to", "w"],
}
SECTIONS = {
    "test": ["Why we ran it", "What was compared", "Result", "Method", "Checks", "Examples", "Caveats"],
    "explore": ["Why we looked", "The data", "Patterns", "Looked at and found nothing", "Method"],
}
THREAD_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXP_ID = re.compile(r"^E-(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
F_ID = re.compile(r"^F-[a-z0-9]+(?:-[a-z0-9]+)*$")
Q_ID = re.compile(r"^Q-[a-z0-9]+(?:-[a-z0-9]+)*$")
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
VERDICT = re.compile(r"^(Yes|No answer yet|No answer|Not yet|No|Partly)([.,:])")
QUOTE_HINT = "Quote it, or write it as a block scalar (>-), because YAML reads some plain words as other types."

# Prose fields, which must be text. YAML turns an unquoted No into false and cuts a value at " #".
EXP_PROSE = ["short", "question", "answer", "rerun"]
FINDING_PROSE = ["claim", "short", "method", "confidence", "caveats", "implication", "retracted"]
NEXT_PROSE = ["question", "action", "settles", "parked"]


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


PROSE_KEYS = sorted(set(EXP_PROSE + FINDING_PROSE + NEXT_PROSE + ["line", "text", "how", "title"]))
# A plain (unquoted) prose value with " #" in it: YAML keeps only what comes before, as a comment starts there.
CUT_COMMENT = re.compile(r"^\s*(?:-\s+)?(?:\{\s*)?(?:" + "|".join(PROSE_KEYS) + r"):[ \t]+(?!['\"|>])[^\n#]*[^\s#][ \t]+#")


def read_front(path: Path, p: Problems):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?$", text, re.S)
    if not m:
        p.error(path, "should start with YAML front matter between two --- lines")
        return None, ""
    for n, line in enumerate(m.group(1).splitlines(), start=2):
        if CUT_COMMENT.match(line):
            p.error(path, f"line {n}: YAML drops everything after \" #\" in an unquoted value, so this text is cut short. {QUOTE_HINT}")
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


class Check:
    """Field checks for one file, reporting through Problems with the file's name."""

    def __init__(self, p: Problems, path):
        self.p, self.path = p, path

    def text(self, obj, keys, what):
        for k in keys:
            v = obj.get(k)
            if v is not None and not isinstance(v, str):
                self.p.error(self.path, f"{what}{k} should be text, but YAML read it as {type(v).__name__} {v!r}. {QUOTE_HINT}")
                obj[k] = str(v)

    def date(self, obj, key, what, required=False):
        v = obj.get(key)
        if v is None:
            if required:
                self.p.error(self.path, f"{what}is missing {key}")
            return
        try:
            dt.date.fromisoformat(str(v))
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
                raise ValueError
        except ValueError:
            self.p.error(self.path, f"{what}{key} {v!r} should be an ISO date, such as 2026-11-14")
            obj[key] = None

    def mappings(self, obj, key, what):
        """A list whose items must be mappings; keeps the good ones and reports the rest."""
        v = obj.get(key)
        if v is None:
            obj[key] = []
            return []
        if not isinstance(v, list):
            self.p.error(self.path, f"{what}{key} should be a list")
            obj[key] = []
            return []
        good = []
        for i, x in enumerate(v, start=1):
            if isinstance(x, dict):
                good.append(x)
            else:
                self.p.error(self.path, f"{what}{key} item {i} should be a mapping of fields, not {x!r}")
        obj[key] = good
        return good


# ---------- markdown ----------

FIG_LINE = re.compile(r"^::fig[ \t]+(\S+)[ \t]*$")
FENCE_OPEN = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
# A code span whose text starts or ends with a space is a model's token: it keeps its spaces and is set as a token.
TOKEN_SPAN = re.compile(r"(?<!`)`((?: [^`\n]*)|(?:[^`\n]* ))`(?!`)")
HASH_LINK = re.compile(r'href="#([^"]*)"')


def fenced(text):
    """Splits text into (is_fenced_code, chunk) runs of whole lines, so markers inside code blocks are left alone."""
    runs, fence = [], None
    for line in text.splitlines(keepends=True):
        m = FENCE_OPEN.match(line)
        inside = fence is not None
        if fence is None and m:
            fence, inside = m.group(1), True
        elif fence is not None and m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
            fence = None
        if runs and runs[-1][0] == inside:
            runs[-1][1].append(line)
        else:
            runs.append((inside, [line]))
    return [(f, "".join(lines)) for f, lines in runs]


def split_sections(body):
    """The write-up's ## sections, found outside fenced code only: (text before the first heading, [(label, text)])."""
    pre, secs = [], []
    for code, chunk in fenced(body):
        for line in chunk.splitlines(keepends=True):
            m = None if code else re.match(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$", line)
            if m and not line.startswith("###"):
                secs.append((m.group(1).strip(), []))
            elif secs:
                secs[-1][1].append(line)
            else:
                pre.append(line)
    return "".join(pre), [(label, "".join(lines)) for label, lines in secs]


class Markdown:
    def __init__(self):
        self.md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
        # Raw HTML in a file is shown as text, exactly as written: quoted model output such as <think> stays
        # visible, and nothing in a file can run on the page.
        self.md.preprocessors.deregister("html_block")
        self.md.inlinePatterns.deregister("html")
        self.links = []  # (path, target) for every in-page link, checked once everything is read

    def _protect(self, text):
        toks = []

        def tok(m):
            toks.append(m.group(1))
            return f"⟦NBTOK{len(toks) - 1}⟧"

        out = []
        for code, chunk in fenced(text):
            if not code:
                chunk = TOKEN_SPAN.sub(tok, chunk)
                chunk = re.sub(r"\bn = (?=[\d,.]+)", "n = ", chunk)
            out.append(chunk)
        return "".join(out), toks

    def _restore(self, out, toks):
        return re.sub(r"⟦NBTOK(\d+)⟧", lambda m: f'<span class="tok">{html.escape(toks[int(m.group(1))])}</span>', out)

    def block(self, text, path):
        figs, out = [], []
        for code, chunk in fenced(text):
            if not code:
                lines = []
                for line in chunk.splitlines(keepends=True):
                    m = FIG_LINE.match(line.rstrip("\n"))
                    if m:
                        figs.append(m.group(1))
                        line = f"\n\nNBFIG{len(figs) - 1}NBFIG\n\n"
                    lines.append(line)
                chunk = "".join(lines)
            out.append(chunk)
        text, toks = self._protect("".join(out))
        res = self._restore(self.md.reset().convert(text), toks)
        res = re.sub(r"<p>NBFIG(\d+)NBFIG</p>", lambda m: f'<div class="nb-fig" data-fig="{html.escape(figs[int(m.group(1))])}"></div>', res)
        res = res.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
        self.links += [(path, t) for t in HASH_LINK.findall(res)]
        return res, figs

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


def skipped(path: Path):
    """Folders and files that aren't notebook content: hidden or tool folders, and a README explaining a folder."""
    return path.name.startswith((".", "_")) or path.name.lower() == "readme.md"


# ---------- figures ----------

def check_figure(fig, fpath, c: Check):
    view = fig.get("view")
    if view not in VIEWS:
        c.p.error(fpath, f"unknown figure view {view!r}; use one of {', '.join(sorted(VIEWS))}")
        return False
    ok = True
    if view == "table":
        head, rows = fig.get("head"), fig.get("rows")
        if not isinstance(head, list) or not isinstance(rows, list):
            c.p.error(fpath, "a table needs a head list and a rows list")
            return False
        for i, r in enumerate(rows, start=1):
            if not isinstance(r, list):
                c.p.error(fpath, f"table row {i} should be a list of cells, not {r!r}")
                ok = False
            elif any(x is not None and (isinstance(x, bool) or not isinstance(x, (str, int, float))) for x in r):
                c.p.error(fpath, f"table row {i}: each cell should be text, a number or null")
                ok = False
        if any(x is not None and not isinstance(x, (str, int, float)) for x in head):
            c.p.error(fpath, "each heading should be text")
            ok = False
        if fig.get("numeric") is not None and not isinstance(fig["numeric"], list):
            c.p.error(fpath, "numeric should be a list of true and false, one per column")
            ok = False
        return ok
    o = fig.get("options")
    if not isinstance(o, dict):
        c.p.error(fpath, f"a {view} figure needs an options object, the arguments of {view}()")
        return False
    for key, typ in VIEWS[view]:
        if not isinstance(o.get(key), typ):
            c.p.error(fpath, f"{view} needs options.{key}, a {'list' if typ is list else 'mapping'}")
            ok = False
    for (v, key), need in ITEM_KEYS.items():
        if v != view or o.get(key) is None:
            continue
        if not isinstance(o[key], list):
            c.p.error(fpath, f"options.{key} should be a list")
            ok = False
            continue
        for i, item in enumerate(o[key], start=1):
            missing = [k for k in need if not isinstance(item, dict) or k not in item]
            if missing:
                c.p.error(fpath, f"options.{key} item {i} is missing {', '.join(missing)}")
                ok = False
    if view == "distChart":
        for k in ("upper", "lower"):
            if isinstance(o.get(k), dict) and not isinstance(o[k].get("counts"), list):
                c.p.error(fpath, f"options.{k} needs counts, a list")
                ok = False
    if view == "lineChart" and isinstance(o.get("x"), list) and isinstance(o.get("series"), list):
        for i, s in enumerate(o["series"], start=1):
            if isinstance(s, dict) and isinstance(s.get("ys"), list) and len(s["ys"]) != len(o["x"]):
                c.p.error(fpath, f"options.series item {i} has {len(s['ys'])} values for {len(o['x'])} x positions")
                ok = False
    for k in ("digits",):
        if o.get(k) is not None and (not isinstance(o[k], int) or isinstance(o[k], bool)):
            c.p.error(fpath, f"options.{k} should be a whole number")
            ok = False
    return ok


# ---------- the repo ----------

def load(root: Path, p: Problems):
    md = Markdown()
    nb = read_yaml(root / "notebook.yaml", p)
    gl = read_yaml(root / "glossary.yaml", p)
    Check(p, root / "notebook.yaml").date(nb, "last_visit", "")
    for k in ("title", "repo", "results"):
        Check(p, root / "notebook.yaml").text(nb, [k], "")
    for k in ("repo", "results"):
        if nb.get(k) and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", nb[k]):
            p.error(root / "notebook.yaml", f"{k} {nb[k]!r} should be owner/name")
    figs, threads, exps = {}, [], []
    bad = set()  # figure files that exist but couldn't be used; their own error already says why

    # Experiments and their figures.
    edir = root / "experiments"
    for d in sorted(edir.iterdir()) if edir.is_dir() else []:
        if not d.is_dir() or skipped(d):
            continue
        readme = d / "README.md"
        if not readme.exists():
            p.error(d, "has no README.md")
            continue
        fm, body = read_front(readme, p)
        if fm is None:
            continue
        c = Check(p, readme)
        e = dict(fm)
        e["_path"] = readme
        if e.get("id") != d.name:
            p.error(readme, f"id {e.get('id')!r} doesn't match its folder name {d.name!r}")
        e["id"] = d.name
        m = EXP_ID.match(e["id"])
        if not m:
            p.error(readme, f"id {e['id']!r} should look like E-YYYY-MM-DD-<slug>")
        c.text(e, ["thread", "mode", "status"] + EXP_PROSE, "")
        c.date(e, "date", "", required=True)
        c.date(e, "started", "")
        if m and e.get("date") and str(e["date"]) != m.group(1):
            p.warn(readme, f"date {e['date']} differs from the date in its id; date is when it was planned, and started when it ran")
        for k in ("thread", "mode", "status", "question"):
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
        if e.get("commit") is not None and not COMMIT.match(str(e["commit"])):
            p.error(readme, f"commit {e['commit']!r} should be a git commit hash")
            e["commit"] = None
        if e.get("pr") is not None and (isinstance(e["pr"], bool) or not isinstance(e["pr"], int)):
            p.error(readme, f"pr {e['pr']!r} should be a pull request number")
            e["pr"] = None
        if e.get("cost_usd") is not None and (isinstance(e["cost_usd"], bool) or not isinstance(e["cost_usd"], (int, float))):
            p.error(readme, f"cost_usd {e['cost_usd']!r} should be a number")
            e["cost_usd"] = None
        if isinstance(e.get("results"), str):
            e["results"] = [e["results"]]
        if e.get("results") is not None and (not isinstance(e["results"], list) or not all(isinstance(r, str) for r in e["results"])):
            p.error(readme, "results should be a list of paths in the results dataset")
            e["results"] = []
        pr = e.get("prediction")
        if pr is not None:
            if not isinstance(pr, dict):
                p.error(readme, "prediction should be a mapping with text, written, held and how")
                e["prediction"] = None
            else:
                c.text(pr, ["text", "how"], "prediction ")
                c.date(pr, "written", "prediction ")
                if pr.get("held") not in (None, True, False, "partly"):
                    p.error(readme, f"prediction held {pr['held']!r} should be true, false or partly")
                if e.get("mode") == "explore":
                    p.warn(readme, "has a prediction, but predictions belong to test mode")
        for i, s in enumerate(c.mappings(e, "since", ""), start=1):
            c.date(s, "date", f"since item {i} ", required=True)
            c.text(s, ["line"], f"since item {i} ")

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
            fc = Check(p, fpath)
            fc.text(fig, ["title", "caption"], "")
            if not check_figure(fig, fpath, fc):
                continue
            fig["title"] = md.inline(fig.get("title"), fpath)
            fig["caption"] = md.inline(fig.get("caption"), fpath)
            if fig["view"] == "table":
                fig["rows"] = [[md.inline(x, fpath) if isinstance(x, str) else x for x in r] for r in fig["rows"]]
                fig["head"] = [md.inline(x, fpath) if isinstance(x, str) else x for x in fig["head"]]
            figs[key] = fig
            bad.discard(key)

        # The write-up: one entry per ## section, in the mode's order.
        pre, secs = split_sections(body)
        if pre.strip():
            p.warn(readme, "has text before its first ## heading, which the notebook doesn't show")
        found = {}
        for label, text in secs:
            if label in found:
                p.error(readme, f"has two ## {label} sections")
            out, used = md.block(text, readme)
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
        if skipped(f):
            continue
        fm, _notes = read_front(f, p)
        if fm is None:
            continue
        c = Check(p, f)
        t = dict(fm)
        t["_path"] = f
        if t.get("id") != f.stem:
            p.error(f, f"thread id {t.get('id')!r} doesn't match its file name {f.stem!r}")
        t["id"] = f.stem
        if not THREAD_ID.match(t["id"]):
            p.error(f, f"thread id {t['id']!r} should be a short kebab-case slug")
        c.text(t, ["title"], "")
        if not t.get("title"):
            p.error(f, "is missing title")
        for i, fd in enumerate(c.mappings(t, "findings", ""), start=1):
            fid = fd.get("id")
            what = f"finding {fid} " if fid else f"finding {i} "
            if not isinstance(fid, str) or not F_ID.match(fid):
                p.error(f, f"{what}needs an id like F-<slug>")
                fd["id"] = fid = f"F-unnamed-{i}"
            if fid in fids:
                p.error(f, f"finding {fid} is also in {fids[fid]}; finding ids are unique across the repo")
            fids[fid] = f.name
            c.text(fd, ["status", "strength", "figure", "replaced_by"] + FINDING_PROSE, what)
            c.date(fd, "date", what, required=True)
            for k in ("status", "strength", "claim"):
                if not fd.get(k):
                    p.error(f, f"{what}is missing {k}")
            if fd.get("status") not in (None, "current", "superseded", "retracted"):
                p.error(f, f"{what}status {fd['status']!r} should be current, superseded or retracted")
            if fd.get("strength") not in (None, "strong", "moderate", "tentative"):
                p.error(f, f"{what}strength {fd['strength']!r} should be strong, moderate or tentative")
            if fd.get("raised") not in (None, True, False):
                p.error(f, f"{what}raised should be true or false")
            if fd.get("status") == "retracted" and not fd.get("retracted"):
                p.error(f, f"{what}is retracted but doesn't say why (retracted: ...)")
            if fd.get("status") == "superseded" and not fd.get("replaced_by"):
                p.warn(f, f"{what}is superseded but doesn't say what replaced it (replaced_by: ...)")
            ev = fd.get("evidence")
            if not isinstance(ev, list) or not ev:
                p.error(f, f"{what}cites no experiments (evidence: a list)")
                ev = []
            fd["evidence"] = []
            for j, x in enumerate(ev, start=1):
                x = {"experiment": x} if isinstance(x, str) else x
                if not isinstance(x, dict):
                    p.error(f, f"{what}evidence item {j} should be a mapping with experiment and role")
                    continue
                c.text(x, ["experiment", "role"], f"{what}evidence item {j} ")
                if x.get("experiment") not in ids:
                    p.error(f, f"{what}cites experiment {x.get('experiment')!r}, which doesn't exist")
                fd["evidence"].append(x)
            if fd.get("figure") and fd["figure"] not in figs and fd["figure"] not in bad:
                p.error(f, f"{what}figure {fd['figure']!r} doesn't exist (expected experiments/<id>/figs/<name>.json)")
            for k in ("claim", "method", "confidence", "caveats", "implication", "retracted"):
                fd[k] = md.inline(fd.get(k), f)
        for i, q in enumerate(c.mappings(t, "next", ""), start=1):
            qid = q.get("id")
            what = f"next item {qid} " if qid else f"next item {i} "
            if not isinstance(qid, str) or not Q_ID.match(qid):
                p.error(f, f"{what}needs an id like Q-<slug>")
                q["id"] = qid = f"Q-unnamed-{i}"
            if qid in qids:
                p.error(f, f"next item {qid} is also in {qids[qid]}")
            qids[qid] = f.name
            c.text(q, ["state", "experiment", "from"] + NEXT_PROSE, what)
            if not q.get("question"):
                p.error(f, f"{what}is missing question")
            q["state"] = q.get("state") or "open"
            if q["state"] not in ("open", "running", "parked"):
                p.error(f, f"{what}state {q['state']!r} should be open, running or parked")
            cost = q.get("cost_gpu_min")
            if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0):
                p.error(f, f"{what}cost_gpu_min {cost!r} should be a number of GPU-minutes")
                q["cost_gpu_min"] = None
            if q.get("lead") not in (None, True, False):
                p.error(f, f"{what}lead should be true or false")
            for k in ("experiment", "from"):
                if q.get(k) and q[k] not in ids:
                    p.error(f, f"{what}{k} {q[k]!r} doesn't exist")
            if q["state"] == "running" and not q.get("experiment"):
                p.warn(f, f"{what}is running but doesn't name its experiment")
            q["_text"] = " ".join(str(q.get(k) or "") for k in NEXT_PROSE)
            for k in NEXT_PROSE:
                q[k] = md.inline(q.get(k), f)
        for i, h in enumerate(c.mappings(t, "history", ""), start=1):
            what = f"history item {i} "
            c.text(h, ["experiment", "line"], what)
            c.date(h, "date", what, required=True)
            if h.get("experiment") not in ids:
                p.error(f, f"{what}names experiment {h.get('experiment')!r}, which doesn't exist")
            if not h.get("line"):
                p.error(f, f"{what}has no line")
            h["line"] = change_line(md.inline(h.get("line"), f))
        threads.append(t)

    tids = {t["id"]: t for t in threads}
    for t in threads:
        for fd in t["findings"]:
            if fd.get("replaced_by") and fd["replaced_by"] not in fids:
                p.error(t["_path"], f"finding {fd['id']}: replaced_by {fd['replaced_by']!r} doesn't exist")
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
        e["since"] = [{"date": s.get("date"), "line": md.inline(s.get("line"), path)} for s in e["since"]]

    # Every in-page link must lead somewhere.
    targets = {"threads", "next", "experiments"} | {f"t-{t}" for t in tids} | set(ids) | set(fids) | set(qids)
    for path, target in md.links:
        if target not in targets:
            p.error(path, f"links to #{target}, which isn't a thread (#t-<id>), experiment, finding or next item")

    glossary = []
    gc = Check(p, root / "glossary.yaml")
    for section, key in (("terms", "term"), ("datasets", "name")):
        for g in gc.mappings(gl, section, ""):
            syn = g.get("synonyms") or []
            if not isinstance(syn, list):
                p.error(root / "glossary.yaml", f"{section}: synonyms of {g.get(key)!r} should be a list")
                syn = []
            forms = [str(x) for x in [g.get(key)] + syn if x is not None]
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
                    line = f'The finding it supports was replaced by <a href="#{html.escape(new["id"])}">{html.escape(new.get("short") or new["id"])}</a>.' if new else "The finding it supports was superseded."
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

    def read(d):
        return {f: (d / f).read_text(encoding="utf-8") for f in KIT_FILES}, str(d)

    if os.environ.get("FD_KIT"):
        d = Path(os.environ["FD_KIT"]).expanduser()
        if not ok(d):
            sys.exit(f"error: FD_KIT is {d}, which doesn't hold {', '.join(KIT_FILES)}")
        return read(d)
    # The style plugin beside this one, in the same checkout or install, is the version this script was written with.
    d = (Path(__file__).resolve().parents[1] / "../../../style/skills/functional-design/references").resolve()
    if ok(d):
        return read(d)
    plugins = Path.home() / ".claude" / "plugins"
    if plugins.is_dir():
        hits = [h.parent for h in plugins.glob("**/skills/functional-design/references/base.css") if ok(h.parent)]
        if hits:
            return read(max(hits, key=lambda h: max((h / f).stat().st_mtime for f in KIT_FILES)))
    out = {}
    for f in KIT_FILES:
        try:
            with urllib.request.urlopen(KIT_URL.format(f), timeout=30) as r:
                out[f] = r.read().decode("utf-8")
        except Exception as err:
            sys.exit(f"error: couldn't find the functional-design kit locally or download {f}: {err}. Set FD_KIT to its references folder.")
    return out, "xycoord/claude-skills main (downloaded)"


# ---------- where the page comes from ----------

def git(root: Path, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()


def source(root: Path, publish: bool):
    """What the footer says the page was built from. With publish, refuses anything but a clean origin/main."""
    try:
        top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    except Exception:
        top = None
    if top != root:
        if publish:
            sys.exit(f"error: {root} isn't the top of a git checkout, so it can't be published. Publish from a clean checkout of main.")
        return {"publish": False, "commit": None, "branch": None, "dirty": False}
    commit = git(root, "rev-parse", "--short", "HEAD")
    try:
        branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    except Exception:
        branch = None
    # Uncommitted changes to tracked files anywhere, or new files the notebook would read.
    dirty = bool(git(root, "status", "--porcelain", "--untracked-files=no")
                 or git(root, "status", "--porcelain", "--untracked-files=all", "--", "threads", "experiments", "glossary.yaml", "notebook.yaml"))
    if publish:
        try:
            git(root, "fetch", "--quiet", "origin", "main")
            main = git(root, "rev-parse", "origin/main")
        except Exception as err:
            sys.exit(f"error: couldn't fetch origin/main to check against: {getattr(err, 'stderr', err)}".strip())
        head = git(root, "rev-parse", "HEAD")
        if head != main:
            sys.exit(f"error: HEAD ({commit}{', on ' + branch if branch else ''}) isn't origin/main ({main[:7]}). "
                     "Check out main and pull before publishing, so the page matches main.")
        if dirty:
            sys.exit("error: the checkout has uncommitted changes, or new files in the notebook's folders. Publish only what's on main.")
    return {"publish": publish, "commit": commit, "branch": branch, "dirty": dirty}


# ---------- the page ----------

def build(root: Path, kit, src):
    p = Problems(root)
    nb, threads, exps, figs, glossary, _gl = load(root, p)
    if p.errors:
        return None, p, None
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
        "source": src,
        "threads": [{**clean(t), "file": f"threads/{t['id']}.md"} for t in threads],
        "experiments": sorted([clean(e) for e in exps], key=lambda e: (str(e.get("date")), e["id"]), reverse=True),
        "figs": figs,
        "glossary": glossary,
    }
    # Every < in the data is written as <, so nothing in a file can end the script tag or open a comment in it.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    parts = {"TITLE": html.escape(data["title"]), "BASECSS": kit["base.css"], "CSS": CSS, "DATA": blob,
             "BASEJS": kit["base.js"], "CHARTSJS": kit["charts.js"], "INTERPJS": kit["interp.js"], "JS": JS}
    # One pass over the template, so a placeholder's name inside the data or the kit is never replaced.
    page = re.sub(r"%(" + "|".join(parts) + r")%", lambda m: parts[m.group(1)], PAGE)
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
// Links out, escaped for an attribute; a results path is encoded one segment at a time.
const GH = path => esc(`https://github.com/${NB.repo}/${path}`);
const HF = path => esc(`https://huggingface.co/datasets/${NB.results}/tree/main/${String(path).replace(/^\/+/, "").split("/").map(encodeURIComponent).join("/")}`);
const ran = e => e.started || e.date;

const sec = (label, body, o = {}) => `<section class="mg"${o.id ? ` id="${esc(o.id)}"` : ""}><div class="ml">${label}</div><div class="mc${o.wide ? " wide" : ""}${o.md ? " md" : ""}">${body}</div></section>`;
const two = (a, b) => `<span>${a}</span>${b ? `<span>${b}</span>` : ""}`;
const head = (crumb, title, sub) => `<div class="mg"><div class="ml"></div><div class="mc">${crumb ? `<p class="crumb">${crumb}</p>` : ""}<h1>${title}</h1>${sub ? `<p class="nb-sub">${sub}</p>` : ""}</div></div>`;
const up = (href, text) => `<a href="${href}" data-up>${text}</a>`;
const weeds = body => `<div class="mg"><div class="ml"></div><div class="mc"><details class="more" data-remember><summary>Code, data and records</summary><div class="dbody">${body}</div></details></div></div>`;
const block = (h, body) => body ? `<div><h2>${h}</h2>${body}</div>` : "";
const kv = rows => { const r = rows.filter(x => x && x[1]); return r.length ? `<dl class="kv">${r.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>` : ""; };
const strengthWord = f => cap(f.strength);
// A finding's dated status: when it was written or raised, marked when that's newer than the last visit.
const fstatus = f => { const w = f.raised ? "Raised" : isNew(f.date) ? "New" : "Since"; return isNew(f.date) ? `<span class="nb-new">${w} ${day(f.date)}</span>` : `${w} ${day(f.date)}`; };
const gpu = q => q.cost_gpu_min ? `<span class="muted nw">, ${esc(q.cost_gpu_min)}&nbsp;GPU-min</span>` : "";
// A step to take: the action and its cost as one sentence, then what its result would settle.
const step = q => { const a = String(q.action || q.question || "").replace(/\.$/, ""); return `${a}${gpu(q)}.${q.settles ? " " + q.settles : ""}`; };
// What a Next item's row says: running, parked, planned as an experiment, or the step that would answer it.
// name(e) renders the experiment's name, as a link or as plain text inside a row that is already a link.
const nextState = (q, name) => {
  const e = EXP[q.experiment], settles = q.settles ? " " + q.settles : "";
  if (q.state === "running") return `${e ? `Running as ${name(e)} since ${day(ran(e))}.` : "Running."}${settles}`;
  if (q.state === "parked") return `Parked: ${q.parked || "no reason given"}.`;
  if (e && e.status === "planned") return `Planned as ${name(e)} on ${day(e.date)}.${settles}`;
  return step(q);
};
const expLink = (id, text) => EXP[id] ? `<a href="#${esc(id)}">${text || esc(shortOf(EXP[id]))}</a>` : `<span class="id">${esc(id)}</span>`;
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
// The numbers behind a chart, for the bookkeeping disclosure. A figure that can't be tabulated says so rather than stopping the page.
function valuesTable(key) {
  try { return valuesTable0(key); } catch (err) { return `<p class="err">The values of ${esc(key)} couldn't be listed: ${esc(err.message)}</p>`; }
}
function valuesTable0(key) {
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
    if (cur.length) h += cur.map(f => row(two(strengthWord(f), fstatus(f)), `<a class="item" href="#${esc(f.id)}"><span class="t nb-claim">${f.claim}</span></a>${isNew(f.date) && f.figure ? `<div class="nb-fig-home">${figHtml(f.figure)}</div>` : ""}`)).join("");
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
  if (run) { const e = EXP[run.experiment]; return ["Running", `${e ? cap(esc(shortOf(e))) + ", since " + day(ran(e)) : run.question}.${more(open.length)}`]; }
  if (open.length) { const q = open[0], a = String(q.action || q.question).replace(/\.$/, ""); return ["Next", `${a}${gpu(q)}.${more(open.length - 1)}`]; }
  if (parked.length) return ["Parked", `${parked[0].question}${parked[0].parked ? ` <span class="muted">${cap(parked[0].parked)}.</span>` : ""}`];
  return null;
}

// ---------- a thread ----------
function viewThread(t) {
  const cur = t.findings.filter(f => f.status === "current"), old = t.findings.filter(f => f.status !== "current");
  const contents = cur.length > 1 ? `<nav class="contents" aria-label="Findings">${cur.map(f => `<a href="#${esc(f.id)}">${esc(f.short || f.id)}</a>`).join("")}</nav>` : "";
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
    const why = f.status === "retracted" ? `<p>${f.retracted}</p>` : FND[f.replaced_by] ? `<p>Replaced by <a href="#${esc(f.replaced_by)}">${esc(FND[f.replaced_by].short || f.replaced_by)}</a>.</p>` : "";
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
    let a = nextState(q, e => expLink(e.id));
    if (q.lead) a += ` <span class="muted">A lead from ${q.from ? expLink(q.from) : "looking at data"}, not yet tested.</span>`;
    return `<li id="${esc(q.id)}"${q.state === "parked" ? ` class="dim"` : ""}><span class="t">${q.question}</span><p class="a">${a}</p></li>`;
  }).join("")}</ul>`;
}
// History: one row per finished run, newest first, with the change of belief it caused, if any.
function historyList(t) {
  const runs = NB.experiments.filter(e => e.thread === t.id && e.status !== "running" && e.status !== "planned");
  const changes = {}; t.history.forEach(h => (changes[h.experiment] ||= []).push(h));
  Object.keys(changes).forEach(id => { if (EXP[id] && !runs.includes(EXP[id])) runs.push(EXP[id]); });
  runs.sort((a, b) => String(b.date).localeCompare(String(a.date)));
  if (!runs.length) return `<p class="muted">No finished runs yet.</p>`;
  const row = e => `<li${e.status === "retracted" || e.status === "abandoned" ? ` class="dim"` : ""}><span class="d">${day(ran(e))}</span><a class="item" href="#${esc(e.id)}"><span class="t">${e.question}</span><p class="a">${e.answer || ""}</p>${(changes[e.id] || []).map(c => `<p class="a">${c.line}</p>`).join("")}</a></li>`;
  const shown = runs.slice(0, 6).map(row).join(""), rest = runs.slice(6).map(row).join("");
  return `<ul class="rows log">${shown}</ul>${rest ? `<details class="nb-earlier"><summary>${runs.length - 6} earlier runs</summary><ul class="rows log">${rest}</ul></details>` : ""}`;
}

// ---------- an experiment ----------
function viewExperiment(e) {
  const t = THR[e.thread], explore = e.mode === "explore";
  const when = e.status === "planned" ? `Planned ${day(e.date)}` : e.status === "running" ? `Running since ${day(ran(e))}` : `Run ${day(ran(e))}`;
  let h = head(up("#experiments", "Experiments"), e.question, `${when}${t ? `, for <a href="#t-${t.id}">${esc(t.title)}</a>` : ""}${t && /[?.!]$/.test(t.title) ? "" : "."}`);
  if (e.since.length) h += sec("Since then", `<ul class="log">${e.since.map(s => `<li><span class="d">${day(s.date)}</span><span>${s.via ? `${expLink(s.via, cap(esc(shortOf(EXP[s.via]))))}: ` : ""}${s.line}</span></li>`).join("")}</ul>`);
  const opening = e.answer || (e.status === "planned" ? "Not run yet." : e.status === "running" ? "<b>Not yet.</b> Still running." : "");
  const ml = e.status === "retracted" ? two(explore ? "What was seen" : "Answer", `<span class="crit">Retracted</span>`) : e.status === "abandoned" ? two(explore ? "What was seen" : "Answer", "Abandoned") : explore ? "What was seen" : "Answer";
  if (opening) h += sec(ml, `<p class="lead">${opening}</p>`);
  const S = Object.fromEntries(e.sections.map(s => [s.label, s]));
  const P = e.prediction;
  const pred = P && P.text ? `<p>The prediction, written ${day(P.written)} before the run: ${P.text}${P.held === true ? ` <b>It held:</b> ${P.how || ""}.` : P.held === false ? ` <b>It didn't hold:</b> ${P.how || ""}.` : P.held === "partly" ? ` <b>It partly held:</b> ${P.how || ""}.` : P.how ? ` <b>The run couldn't tell:</b> ${P.how}.` : ""}</p>` : "";
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
  const cites = e.findings.map(x => { const f = FND[x.id]; return f ? `<li><a class="item" href="#${esc(f.id)}"><span class="t">${f.claim}</span><p class="a">${[x.role && cap(esc(x.role)), f.status === "current" ? `${strengthWord(f)}, since ${day(f.date)}` : `${cap(f.status)} ${day(f.date)}`].filter(Boolean).join(". ")}.</p></a></li>` : ""; }).join("");
  if (cites) h += sec(e.findings.length > 1 ? "Findings" : "Finding", `<ul class="rows">${cites}</ul>`);
  if (explore) {
    const leads = Object.values(QS).filter(q => q.from === e.id);
    h += sec("Leads", leads.length ? `<ul class="rows">${leads.map(q => `<li><a class="item" href="#${esc(q.id)}"><span class="t">${q.question}</span><p class="a">${nextState(q, e => esc(shortOf(e)))}</p></a></li>`).join("")}</ul>` : `<p class="muted">No leads taken forward from this look.</p>`);
  }
  // Figures in the order the page shows them, then any the write-up doesn't place.
  const placed = e.sections.flatMap(s => s.parts.flatMap(p => p.bleed ? [p.bleed] : [...(p.html || "").matchAll(/data-fig="([^"]+)"/g)].map(m => m[1])));
  const figKeys = [...new Set([...placed, ...Object.keys(NB.figs).filter(k => k.startsWith(e.id + "/")).sort()])].filter(k => NB.figs[k]);
  const vals = figKeys.map(valuesTable).join("");
  h += weeds([
    block("Code", kv([["Commit", e.commit && `<a class="id" href="${GH(`commit/${e.commit}`)}">${esc(e.commit)}</a>`], ["Pull request", e.pr && `<a href="${GH(`pull/${e.pr}`)}">${esc(NB.repo)}#${esc(e.pr)}</a>`], ["Rerun", e.rerun && `<code>${esc(e.rerun)}</code>`]])),
    block("Data", kv([["Results", (e.results || []).map(r => `<a class="id" href="${HF(r)}">${esc(r)}</a>`).join("<br>") || "No results folder"], ["Figures", figKeys.length ? figKeys.map(k => `<span class="id">figs/${esc(k.split("/")[1])}.json</span>`).join("<br>") : ""]])),
    vals && block("Values", vals),
    block("Record", kv([["ID", `<span class="id">${esc(e.id)}</span>`], ["Mode", explore ? "Looking for a hypothesis" : "Testing a hypothesis"], ["Status", esc(cap(e.status))], ["Planned", day(e.date)], ["Started", e.started ? day(e.started) : ""], ["Cost", e.cost_usd != null ? `$${Number(e.cost_usd).toFixed(2)}` : ""], ["Source", `<a class="id" href="${GH(`blob/main/experiments/${e.id}/README.md`)}">experiments/${esc(e.id)}/README.md</a>`]])),
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
    const a = nextState(q, e => esc(shortOf(e)));
    const toExp = e && (q.state === "running" || (q.state === "open" && e.status === "planned"));
    return `<li${q.state === "parked" ? ` class="dim"` : ""}><a class="item" href="#${esc(toExp ? e.id : q.id)}"><span class="t">${q.question}</span><p class="a">${a}</p>${tline(q.thread)}</a></li>`;
  };
  const erow = e => `<li><a class="item" href="#${esc(e.id)}"><span class="t">${e.question}</span><p class="a">${e.status === "running" ? `Running since ${day(ran(e))}.` : `Planned ${day(e.date)}.`}</p>${tline(e.thread)}</a></li>`;
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
  if (!NB.experiments.length && !any) return `<p class="muted" style="margin-top:12px">No experiments yet. Each one is a folder in <code>experiments/</code> of the research repo, and appears here once it's on main and the notebook is rebuilt.</p>`;
  if (!exps.length && !qs.length) return h + `<p style="margin-top:12px">Nothing matches “${esc(QUERY.trim())}”. As far as the notebook knows, it hasn't been run or queued.</p>`;
  const qrow = q => `<li class="mg${q.state === "parked" ? " dim" : ""}"><div class="ml">${q.state === "parked" ? "Parked" : "Not run yet"}</div><div class="mc"><a class="item" href="#${esc(q.id)}"><span class="t">${q.question}</span><p class="a">${q.state === "parked" ? `Parked: ${q.parked || ""}.` : step(q)}</p></a></div></li>`;
  const erow = e => `<li class="mg${e.status === "retracted" || e.status === "abandoned" ? " dim" : ""}"><div class="ml">${two(day(e.status === "planned" ? e.date : ran(e)), e.status === "running" ? "Running" : e.status === "planned" ? "Planned" : e.status === "retracted" ? `<span class="crit">Retracted</span>` : e.status === "abandoned" ? "Abandoned" : "")}</div><div class="mc"><a class="item" href="#${esc(e.id)}"><span class="t">${e.question}</span><p class="a">${e.answer || (e.status === "running" ? `Running since ${day(ran(e))}.` : e.status === "planned" ? "Not run yet." : "")}</p></a></div></li>`;
  return h + `<ul class="rows nb-list" style="margin-top:20px">${qs.map(qrow).join("")}${exps.map(erow).join("")}</ul>`;
}
function viewExperiments() {
  return `<div class="nb-page"><div class="mg"><div class="ml"></div><div class="mc nb-search"><label>Have I tested this?<input type="search" id="nb-q" value="${esc(QUERY)}" placeholder="Search experiments and queued questions" autocomplete="off"></label></div></div><div id="nb-results">${results()}</div></div>`;
}
document.addEventListener("input", ev => { if (ev.target.id === "nb-q") { QUERY = ev.target.value; const r = document.getElementById("nb-results"); r.innerHTML = results(); } });

// ---------- routing: one hash per view, and a way back on every page ----------
function resolve(hash) {
  let id; try { id = decodeURIComponent(hash.replace(/^#/, "")); } catch (err) { id = ""; }  // a malformed address opens the home view
  id = id || "threads";
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
  if (run.length === 1) live.innerHTML = `<a href="#${esc(run[0].id)}">1 experiment running, as of ${builtDay}</a>`;
  else if (run.length) live.innerHTML = `<a href="#next">${run.length} experiments running, as of ${builtDay}</a>`;
  else live.remove();
  const when = `${day(NB.built.slice(0, 10))} ${NB.built.slice(0, 4)}, ${NB.built.slice(11, 16)} UTC`, S = NB.source || {}, name = esc(NB.repo.split("/").pop());
  // A page built for publishing comes from a clean origin/main; anything else says it's a preview of what it was built from.
  document.getElementById("nb-foot").innerHTML = S.publish
    ? `Built ${when} from <span class="id">${name}@${esc(S.commit)}</span>, the main branch. This page is generated from the research repo; change the repo, not the page.`
    : `<b class="warn">Preview</b>, not the published notebook: built ${when} from ${S.commit ? `<span class="id">${name}@${esc(S.commit)}</span>${S.branch ? ` on branch <span class="id">${esc(S.branch)}</span>` : ", a detached checkout"}${S.dirty ? ", with uncommitted changes" : ""}` : "a folder that isn't a git checkout"}.`;
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
    ap.add_argument("--publish", action="store_true",
                    help="build the page to publish: refuses unless the repo is a clean checkout of origin/main")
    a = ap.parse_args()
    root = Path(a.repo).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"error: {root} isn't a folder")
    src = source(root, a.publish)
    kit, where = find_kit()
    page, p, data = build(root, kit, src)
    for w in p.warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in p.errors:
        print(f"error: {e}", file=sys.stderr)
    if p.errors:
        sys.exit(f"{len(p.errors)} error(s); nothing written.")
    Path(a.out).write_text(page, encoding="utf-8")
    what = "to publish" if a.publish else "as a preview"
    print(f"Wrote {a.out} {what}: {len(data['threads'])} threads, {len(data['experiments'])} experiments, "
          f"{len(data['figs'])} figures, {len(page) // 1024} KB. Kit from {where}.")


if __name__ == "__main__":
    main()
