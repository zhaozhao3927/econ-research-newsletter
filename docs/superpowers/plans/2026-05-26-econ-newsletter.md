# Behavioral & Experimental Economics Weekly — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully automated weekly newsletter that fetches new papers from top economics journals, generates AI summaries via Claude API, and publishes a searchable static HTML site to GitHub Pages every Monday.

**Architecture:** Python pipeline (fetch → filter → summarize → render → publish) orchestrated by PowerShell and driven by Windows Task Scheduler. Each stage is an independent module. HTML output uses Jinja2 templates styled after the follow-builders-newsletter reference design.

**Tech Stack:** Python 3.10+, feedparser, anthropic, jinja2, pyyaml, pytest, PowerShell 5.1, GitHub Pages

---

## File Map

| File | Responsibility |
|------|----------------|
| `config.yaml` | Feed URLs, API model, max papers, cache path |
| `data/keyword-clusters.md` | Keyword list for behavioral relevance filter |
| `src/fetch.py` | Poll RSS feeds, parse entries, deduplicate by DOI |
| `src/summarize.py` | Keyword filter, Claude API summaries, DOI cache |
| `src/build_issue.py` | Assemble weekly issue JSON from papers + summaries |
| `src/render.py` | Render issue JSON → HTML via Jinja2 |
| `src/update_index.py` | Rebuild `index.html` from all issue JSONs |
| `templates/issue.html.j2` | Issue page: masthead, filter bar, paper cards |
| `templates/index.html.j2` | Archive/cover page |
| `scripts/run_weekly.ps1` | Main orchestrator: runs all src/ steps in order |
| `scripts/publish.ps1` | `git add` + `git commit` + `git push` |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/test_fetch.py` | Tests for `src/fetch.py` |
| `tests/test_summarize.py` | Tests for keyword filter and Claude summarization |
| `tests/test_build_issue.py` | Tests for `src/build_issue.py` |
| `tests/test_render.py` | Tests for `src/render.py` |
| `tests/test_update_index.py` | Tests for `src/update_index.py` |
| `requirements.txt` | Python dependencies |
| `pytest.ini` | Python path config for tests |
| `.gitignore` | Exclude `cache/`, `logs/`, `__pycache__/` |

---

## Task 1: Project Scaffold

**Files:** `requirements.txt`, `pytest.ini`, `.gitignore`, `config.yaml`, `data/keyword-clusters.md`, `src/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

Run from `C:\Users\yu2511zh\econ-research-newsletter` in PowerShell:
```powershell
New-Item -ItemType Directory -Force src, tests, templates, "data/issues", issues, "assets/css", scripts, cache, logs | Out-Null
New-Item -ItemType File -Force src/__init__.py, tests/__init__.py | Out-Null
```

- [ ] **Step 2: Write `requirements.txt`**

```
feedparser==6.0.11
jinja2==3.1.4
pyyaml==6.0.2
anthropic==0.40.0
pytest==8.3.4
```

- [ ] **Step 3: Write `pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 4: Write `.gitignore`**

```
cache/
logs/
__pycache__/
*.pyc
.env
```

- [ ] **Step 5: Write `config.yaml`**

```yaml
newsletter:
  title: "Behavioral & Experimental Economics Weekly"
  subtitle: "New papers from top journals · weekly digest"
  github_pages_url: ""

feeds:
  - name: NBER
    url: "https://www.nber.org/rss/new_working_papers.xml"
  - name: AER
    url: "https://www.aeaweb.org/journals/aer/issues/rss"
  - name: QJE
    url: "https://academic.oup.com/rss/site_5504/3365.xml"
  - name: JPE
    url: "https://www.journals.uchicago.edu/action/showFeed?type=etoc&feed=rss&jc=jpe"
  - name: REStud
    url: "https://academic.oup.com/rss/site_5508/3367.xml"
  - name: Econometrica
    url: "https://onlinelibrary.wiley.com/action/showFeed?jc=14680262&type=etoc&feed=rss"
  - name: JEEA
    url: "https://academic.oup.com/rss/site_5505/3366.xml"
  - name: JEBO
    url: "https://www.sciencedirect.com/journal/journal-of-economic-behavior-and-organization/rss"
  - name: GEB
    url: "https://www.sciencedirect.com/journal/games-and-economic-behavior/rss"
  - name: ExperimentalEcon
    url: "https://link.springer.com/search.rss?facet-journal-id=10683"
  - name: PsychScience
    url: "https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc=pssa&type=etoc&feed=rss"
  - name: NatureHumanBehaviour
    url: "https://www.nature.com/nathumbehav.rss"
  - name: SSRN_BehavEcon
    url: "https://papers.ssrn.com/rss/harg/ECON_EC_BE.xml"

api:
  model: claude-sonnet-4-6
  max_papers_per_issue: 30
  max_tokens: 512

cache:
  path: cache/summaries.json

keyword_clusters_path: data/keyword-clusters.md
```

- [ ] **Step 6: Copy keyword-clusters.md**

```powershell
Copy-Item "C:\Users\yu2511zh\.claude\skills\bacon-research\references\keyword-clusters.md" "data\keyword-clusters.md"
```

- [ ] **Step 7: Install dependencies**

```powershell
pip install -r requirements.txt
```

Expected: `Successfully installed feedparser-6.0.11 jinja2-3.1.4 ...`

- [ ] **Step 8: git init and initial commit**

```powershell
git init
git add .
git commit -m "feat: initial project scaffold"
```

---

## Task 2: Shared Test Fixtures

**Files:** `tests/conftest.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import pytest


@pytest.fixture
def sample_paper():
    return {
        "title": "Loss Aversion in Labor Supply: Evidence from a Field Experiment",
        "authors": ["Camerer, Colin", "Babcock, Linda"],
        "journal": "AER",
        "publishedDate": "2026-05-20",
        "doi": "10.1257/aer.test.001",
        "sourceUrl": "https://www.aeaweb.org/articles?id=10.1257/aer.test.001",
        "abstract": (
            "This paper studies loss aversion and reference dependence in labor supply "
            "decisions using a field experiment with taxi drivers. We find that drivers "
            "work shorter hours on high-wage days, consistent with daily income targeting."
        ),
    }


@pytest.fixture
def sample_summary():
    return {
        "rq": "Do taxi drivers exhibit loss aversion relative to a daily income target?",
        "method": "Field experiment with real earnings data from NYC taxi drivers.",
        "keyFinding": (
            "Drivers work shorter hours on high-wage days, consistent with daily income "
            "targeting and loss aversion relative to a reference income level."
        ),
        "whyItMatters": "Provides field evidence for reference-dependent labor supply outside the lab.",
        "isBehavioral": True,
        "tags": ["labor", "risk"],
    }


@pytest.fixture
def sample_config():
    return {
        "newsletter": {
            "title": "Behavioral & Experimental Economics Weekly",
            "subtitle": "New papers from top journals · weekly digest",
            "github_pages_url": "",
        },
        "feeds": [
            {"name": "AER", "url": "https://www.aeaweb.org/journals/aer/issues/rss"},
        ],
        "api": {
            "model": "claude-sonnet-4-6",
            "max_papers_per_issue": 30,
            "max_tokens": 512,
        },
        "cache": {"path": "cache/summaries.json"},
        "keyword_clusters_path": "data/keyword-clusters.md",
    }


@pytest.fixture
def sample_issue(sample_paper, sample_summary):
    return {
        "title": "Behavioral & Experimental Economics Weekly",
        "weekOf": "2026-05-19 – 2026-05-26",
        "publishDate": "2026-05-26",
        "issueNumber": 1,
        "intro": {
            "kicker": "Editor's Note",
            "text": "This week brings field evidence on loss aversion in labor markets.",
        },
        "papers": [{**sample_paper, **sample_summary}],
    }
```

- [ ] **Step 2: Verify fixtures load**

```powershell
python -m pytest tests/ --collect-only
```

Expected: no errors, `0 tests collected`.

- [ ] **Step 3: Commit**

```powershell
git add tests/conftest.py
git commit -m "test: add shared fixtures"
```

---

## Task 3: src/fetch.py

**Files:** `tests/test_fetch.py`, `src/fetch.py`

- [ ] **Step 1: Write `tests/test_fetch.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from src.fetch import fetch_all_feeds, _extract_doi, _dedup_papers, _within_window


def _mock_entry(title="Test Paper", link="https://example.com/paper",
                doi="10.1257/test.001", published_days_ago=3, summary="Abstract text"):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.id = f"https://doi.org/{doi}"
    entry.summary = summary
    entry.author = "Smith, John"
    cutoff = datetime.now(timezone.utc) - timedelta(days=published_days_ago)
    entry.published_parsed = cutoff.timetuple()
    return entry


class TestExtractDoi:
    def test_extracts_doi_from_id_url(self):
        entry = _mock_entry(doi="10.1257/aer.2026.001")
        assert _extract_doi(entry) == "10.1257/aer.2026.001"

    def test_falls_back_to_hash_when_no_doi(self):
        entry = _mock_entry()
        entry.id = "https://example.com/no-doi"
        entry.link = "https://example.com/paper"
        assert _extract_doi(entry).startswith("hash:")


class TestWithinWindow:
    def test_recent_paper_included(self):
        assert _within_window(_mock_entry(published_days_ago=2), days=7) is True

    def test_old_paper_excluded(self):
        assert _within_window(_mock_entry(published_days_ago=10), days=7) is False


class TestDedupPapers:
    def test_deduplicates_by_doi(self, sample_paper):
        papers = [sample_paper, {**sample_paper, "title": "Duplicate"}]
        assert len(_dedup_papers(papers)) == 1

    def test_keeps_distinct_dois(self, sample_paper):
        paper2 = {**sample_paper, "doi": "10.1257/aer.test.002"}
        assert len(_dedup_papers([sample_paper, paper2])) == 2


class TestFetchAllFeeds:
    def test_returns_papers_from_feed(self, sample_config):
        mock_feed = MagicMock()
        mock_feed.entries = [_mock_entry()]
        with patch("src.fetch.feedparser.parse", return_value=mock_feed):
            papers = fetch_all_feeds(sample_config)
        assert len(papers) == 1
        assert papers[0]["journal"] == "AER"

    def test_skips_old_papers(self, sample_config):
        mock_feed = MagicMock()
        mock_feed.entries = [_mock_entry(published_days_ago=10)]
        with patch("src.fetch.feedparser.parse", return_value=mock_feed):
            papers = fetch_all_feeds(sample_config)
        assert papers == []

    def test_handles_feed_error_gracefully(self, sample_config):
        with patch("src.fetch.feedparser.parse", side_effect=Exception("Network error")):
            papers = fetch_all_feeds(sample_config)
        assert papers == []
```

- [ ] **Step 2: Run — confirm fail**

```powershell
python -m pytest tests/test_fetch.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.fetch'`

- [ ] **Step 3: Write `src/fetch.py`**

```python
import hashlib
import re
from datetime import datetime, timedelta, timezone

import feedparser


def fetch_all_feeds(config: dict) -> list[dict]:
    all_papers = []
    for feed_cfg in config.get("feeds", []):
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if not _within_window(entry, days=7):
                    continue
                paper = _parse_entry(entry, journal=name)
                if paper:
                    all_papers.append(paper)
        except Exception as exc:
            print(f"[fetch] ERROR {name}: {exc}")
    return _dedup_papers(all_papers)


def _parse_entry(entry, journal: str) -> dict | None:
    title = getattr(entry, "title", "").strip()
    if not title:
        return None
    return {
        "title": title,
        "authors": _extract_authors(entry),
        "journal": journal,
        "publishedDate": _extract_date(entry),
        "doi": _extract_doi(entry),
        "sourceUrl": getattr(entry, "link", ""),
        "abstract": _extract_abstract(entry),
    }


def _extract_doi(entry) -> str:
    for attr in ("id", "link"):
        val = getattr(entry, attr, "") or ""
        match = re.search(r"10\.\d{4,}/[^\s\"<>]+", val)
        if match:
            return match.group(0).rstrip(".")
    text = (getattr(entry, "title", "") or "") + (getattr(entry, "link", "") or "")
    return "hash:" + hashlib.md5(text.encode()).hexdigest()[:8]


def _extract_authors(entry) -> list[str]:
    if hasattr(entry, "authors") and entry.authors:
        return [a.get("name", "") for a in entry.authors if a.get("name")]
    author = getattr(entry, "author", "") or ""
    return [a.strip() for a in author.split(";") if a.strip()]


def _extract_date(entry) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extract_abstract(entry) -> str:
    for attr in ("summary", "content"):
        val = getattr(entry, attr, None)
        if isinstance(val, list) and val:
            val = val[0].get("value", "")
        if val:
            return re.sub(r"<[^>]+>", "", str(val)).strip()
    return ""


def _within_window(entry, days: int = 7) -> bool:
    if not hasattr(entry, "published_parsed") or not entry.published_parsed:
        return True
    pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return pub >= datetime.now(timezone.utc) - timedelta(days=days)


def _dedup_papers(papers: list[dict]) -> list[dict]:
    seen, result = set(), []
    for p in papers:
        doi = p.get("doi", "")
        if doi and doi not in seen:
            seen.add(doi)
            result.append(p)
    return result


if __name__ == "__main__":
    import argparse, json, yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    papers = fetch_all_feeds(config)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"[fetch] {len(papers)} papers → {args.output}")
```

- [ ] **Step 4: Run — confirm pass**

```powershell
python -m pytest tests/test_fetch.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/fetch.py tests/test_fetch.py
git commit -m "feat: RSS feed fetcher with dedup and 7-day window"
```

---

## Task 4: src/summarize.py

**Files:** `tests/test_summarize.py`, `src/summarize.py`

- [ ] **Step 1: Write `tests/test_summarize.py`**

```python
import json
import pytest
from unittest.mock import MagicMock
from src.summarize import (
    load_keywords, keyword_score, classify_behavioral,
    summarize_paper, generate_intro,
)

CLUSTERS_MD = """
## Risk & Uncertainty
- risk preferences, risk aversion, loss aversion
- prospect theory, reference dependence

## Social Preferences
- altruism, prosocial behavior, fairness
"""

MOCK_SUMMARY = json.dumps({
    "rq": "Do taxi drivers exhibit loss aversion?",
    "method": "Field experiment with NYC taxi drivers.",
    "keyFinding": "Drivers work less on high-wage days.",
    "whyItMatters": "Field evidence for reference-dependent labor supply.",
    "isBehavioral": True,
    "tags": ["labor", "risk"],
})


class TestLoadKeywords:
    def test_loads_phrases(self, tmp_path):
        f = tmp_path / "kw.md"
        f.write_text(CLUSTERS_MD, encoding="utf-8")
        kws = load_keywords(str(f))
        assert "loss aversion" in kws
        assert "fairness" in kws

    def test_excludes_headers(self, tmp_path):
        f = tmp_path / "kw.md"
        f.write_text(CLUSTERS_MD, encoding="utf-8")
        kws = load_keywords(str(f))
        assert "Risk & Uncertainty" not in kws


class TestKeywordScore:
    def test_counts_matches(self):
        kws = ["loss aversion", "prospect theory", "fairness"]
        assert keyword_score("We study loss aversion and prospect theory.", kws) == 2

    def test_zero_on_no_match(self):
        assert keyword_score("We study monetary policy.", ["loss aversion"]) == 0

    def test_case_insensitive(self):
        assert keyword_score("LOSS AVERSION is studied.", ["loss aversion"]) == 1


class TestClassifyBehavioral:
    def test_zero_matches_false(self, sample_paper):
        sample_paper["abstract"] = "We study monetary policy transmission."
        is_b, tags = classify_behavioral(sample_paper, ["loss aversion"], low=1, high=3)
        assert is_b is False and tags == []

    def test_high_matches_true(self, sample_paper):
        kws = ["loss aversion", "reference dependence", "prospect theory", "risk aversion"]
        sample_paper["abstract"] = "Loss aversion, reference dependence, prospect theory, risk aversion."
        is_b, tags = classify_behavioral(sample_paper, kws, low=1, high=3)
        assert is_b is True


class TestSummarizePaper:
    def test_returns_fields(self, sample_paper, tmp_path):
        cache = str(tmp_path / "cache.json")
        client = MagicMock()
        client.messages.create.return_value = MagicMock(content=[MagicMock(text=MOCK_SUMMARY)])
        result = summarize_paper(sample_paper, client, "claude-sonnet-4-6", cache)
        assert result["rq"] == "Do taxi drivers exhibit loss aversion?"
        assert result["isBehavioral"] is True

    def test_cache_hit_skips_api(self, sample_paper, tmp_path):
        cache = str(tmp_path / "cache.json")
        client = MagicMock()
        client.messages.create.return_value = MagicMock(content=[MagicMock(text=MOCK_SUMMARY)])
        summarize_paper(sample_paper, client, "claude-sonnet-4-6", cache)
        client.messages.create.reset_mock()
        summarize_paper(sample_paper, client, "claude-sonnet-4-6", cache)
        client.messages.create.assert_not_called()

    def test_api_error_returns_empty(self, sample_paper, tmp_path):
        cache = str(tmp_path / "cache.json")
        client = MagicMock()
        client.messages.create.side_effect = Exception("API down")
        result = summarize_paper(sample_paper, client, "claude-sonnet-4-6", cache)
        assert result["rq"] == ""
        assert result["isBehavioral"] is False


class TestGenerateIntro:
    def test_returns_string(self, sample_paper, sample_summary):
        papers = [{**sample_paper, **sample_summary}]
        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="This week features loss aversion research.")]
        )
        result = generate_intro(papers, client, "claude-sonnet-4-6")
        assert isinstance(result, str) and len(result) > 0
```

- [ ] **Step 2: Run — confirm fail**

```powershell
python -m pytest tests/test_summarize.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.summarize'`

- [ ] **Step 3: Write `src/summarize.py`**

```python
import json
import os
import re

import anthropic


_SUMMARY_PROMPT = """\
Analyze this economics paper. Return ONLY a JSON object with these fields:
- rq: Research question (1-2 sentences)
- method: Method type + brief design note (max 20 words)
- keyFinding: Key finding (2-3 sentences)
- whyItMatters: Contribution (1 sentence)
- isBehavioral: true if behavioral/experimental economics, false otherwise
- tags: list of 2-4 tags from: risk, time, social, nudges, markets, identity, cognitive, labor, finance, health

Title: {title}
Authors: {authors}
Journal: {journal}
Abstract: {abstract}

Return only valid JSON."""

_INTRO_PROMPT = """\
You are the editor of a weekly behavioral economics newsletter.
This week's papers:
{paper_list}
Write a 2-3 sentence editor's note starting with "This week". Plain text only."""


def load_keywords(path: str) -> list[str]:
    keywords = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- "):
                keywords.extend(p.strip().lower() for p in line[2:].split(",") if p.strip())
    return keywords


def keyword_score(text: str, keywords: list[str]) -> int:
    t = text.lower()
    return sum(1 for kw in keywords if kw in t)


def classify_behavioral(
    paper: dict, keywords: list[str], low: int = 1, high: int = 3
) -> tuple[bool, list[str]]:
    text = (paper.get("abstract", "") + " " + paper.get("title", "")).lower()
    matched = [kw for kw in keywords if kw in text]
    if len(matched) == 0:
        return False, []
    if len(matched) >= high:
        return True, matched[:4]
    return False, matched[:4]  # borderline — Claude decides in summarize_paper


def _load_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def summarize_paper(
    paper: dict, client: anthropic.Anthropic, model: str, cache_path: str
) -> dict:
    doi = paper.get("doi", "")
    cache = _load_cache(cache_path)
    if doi and doi in cache:
        return cache[doi]

    prompt = _SUMMARY_PROMPT.format(
        title=paper.get("title", ""),
        authors=", ".join(paper.get("authors", [])),
        journal=paper.get("journal", ""),
        abstract=paper.get("abstract", ""),
    )
    try:
        resp = client.messages.create(
            model=model, max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.content[0].text.strip())
        summary = json.loads(raw)
    except Exception as exc:
        print(f"[summarize] ERROR '{paper.get('title', '')}': {exc}")
        summary = {"rq": "", "method": "", "keyFinding": "", "whyItMatters": "",
                   "isBehavioral": False, "tags": []}

    if doi:
        cache[doi] = summary
        _save_cache(cache_path, cache)
    return summary


def generate_intro(papers: list[dict], client: anthropic.Anthropic, model: str) -> str:
    lines = [f"- {p.get('title','')} ({p.get('journal','')})" for p in papers[:20]]
    try:
        resp = client.messages.create(
            model=model, max_tokens=256,
            messages=[{"role": "user", "content": _INTRO_PROMPT.format(paper_list="\n".join(lines))}],
        )
        return resp.content[0].text.strip()
    except Exception as exc:
        print(f"[summarize] intro ERROR: {exc}")
        return f"This week's digest covers {len(papers)} new papers across top economics journals."


if __name__ == "__main__":
    import argparse, yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with open(args.input, encoding="utf-8") as f:
        papers = json.load(f)
    keywords = load_keywords(config["keyword_clusters_path"])
    client = anthropic.Anthropic()
    model = config["api"]["model"]
    cache_path = config["cache"]["path"]
    results = []
    for paper in papers:
        summary = summarize_paper(paper, client, model, cache_path)
        score = keyword_score(paper.get("abstract", "") + " " + paper.get("title", ""), keywords)
        if score == 0:
            is_b, tags = False, []
        elif score >= 3:
            is_b, tags = True, summary.get("tags", [])
        else:
            is_b = summary.get("isBehavioral", False)
            tags = summary.get("tags", [])
        results.append({**paper, **summary, "isBehavioral": is_b, "tags": tags})
    intro = generate_intro(results, client, model)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"papers": results, "intro": intro}, f, indent=2, ensure_ascii=False)
    print(f"[summarize] {len(results)} papers → {args.output}")
```

- [ ] **Step 4: Run — confirm pass**

```powershell
python -m pytest tests/test_summarize.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/summarize.py tests/test_summarize.py
git commit -m "feat: keyword filter and Claude API summarization with cache"
```

---

## Task 5: src/build_issue.py

**Files:** `tests/test_build_issue.py`, `src/build_issue.py`

- [ ] **Step 1: Write `tests/test_build_issue.py`**

```python
import json
import pytest
from pathlib import Path
from src.build_issue import build_issue, next_issue_number


class TestNextIssueNumber:
    def test_returns_1_when_empty(self, tmp_path):
        assert next_issue_number(str(tmp_path)) == 1

    def test_increments_from_existing(self, tmp_path):
        (tmp_path / "becon-weekly-2026-05-19.json").write_text(
            json.dumps({"issueNumber": 3}), encoding="utf-8"
        )
        assert next_issue_number(str(tmp_path)) == 4


class TestBuildIssue:
    def test_valid_structure(self, sample_paper, sample_summary, sample_config, tmp_path):
        papers = [{**sample_paper, **sample_summary}]
        issue = build_issue(papers, "Intro text.", sample_config, str(tmp_path), "2026-05-26")
        assert issue["issueNumber"] == 1
        assert issue["publishDate"] == "2026-05-26"
        assert len(issue["papers"]) == 1
        assert issue["intro"]["text"] == "Intro text."

    def test_writes_json(self, sample_paper, sample_summary, sample_config, tmp_path):
        build_issue([{**sample_paper, **sample_summary}], "Intro.", sample_config, str(tmp_path), "2026-05-26")
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1

    def test_respects_max_papers(self, sample_paper, sample_summary, sample_config, tmp_path):
        sample_config["api"]["max_papers_per_issue"] = 2
        papers = [{**sample_paper, **sample_summary, "doi": f"10.test/{i}"} for i in range(5)]
        issue = build_issue(papers, "Intro.", sample_config, str(tmp_path), "2026-05-26")
        assert len(issue["papers"]) == 2
```

- [ ] **Step 2: Run — confirm fail**

```powershell
python -m pytest tests/test_build_issue.py -v
```

- [ ] **Step 3: Write `src/build_issue.py`**

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def next_issue_number(data_dir: str) -> int:
    max_num = 0
    for path in Path(data_dir).glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            max_num = max(max_num, data.get("issueNumber", 0))
        except Exception:
            pass
    return max_num + 1


def build_issue(
    papers: list[dict],
    intro_text: str,
    config: dict,
    data_dir: str,
    publish_date: str | None = None,
) -> dict:
    if publish_date is None:
        publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    max_p = config.get("api", {}).get("max_papers_per_issue", 30)
    papers = papers[:max_p]
    issue_num = next_issue_number(data_dir)
    issue = {
        "title": config["newsletter"]["title"],
        "weekOf": f"{publish_date} – {publish_date}",
        "publishDate": publish_date,
        "issueNumber": issue_num,
        "intro": {"kicker": "Editor's Note", "text": intro_text},
        "papers": papers,
    }
    os.makedirs(data_dir, exist_ok=True)
    out = os.path.join(data_dir, f"becon-weekly-{publish_date}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(issue, f, indent=2, ensure_ascii=False)
    print(f"[build] {out} ({len(papers)} papers, issue #{issue_num})")
    return issue


if __name__ == "__main__":
    import argparse, yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    build_issue(data["papers"], data["intro"], config, "data/issues", args.date)
```

- [ ] **Step 4: Run — confirm pass**

```powershell
python -m pytest tests/test_build_issue.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/build_issue.py tests/test_build_issue.py
git commit -m "feat: issue builder with auto-incrementing issue number"
```

---

## Task 6: HTML Templates

**Files:** `templates/issue.html.j2`, `templates/index.html.j2`

- [ ] **Step 1: Write `templates/issue.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ issue.title }} · {{ issue.publishDate }}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root{--ink:#1a1a1a;--paper:#f6f3ed;--accent:#c0392b;--border:#d4cdc0;--muted:#7a7265;--tag-bg:#e8e2d6;--shadow:0 2px 8px rgba(0,0,0,.06)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'IBM Plex Sans',sans-serif;line-height:1.7}
.wrap{max-width:920px;margin:0 auto;padding:0 24px}
.masthead{padding-top:48px}
.masthead-rule{border:none;border-top:3px solid var(--ink);margin:0 0 12px}
.masthead-inner{display:flex;justify-content:center;align-items:baseline;gap:16px;border-bottom:1px solid var(--border);padding-bottom:12px}
.masthead-title{font-family:'Playfair Display',serif;font-size:32px;font-weight:700}
.edition-strip{margin-top:8px;padding:10px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border);color:var(--muted);font-family:'IBM Plex Mono',monospace;font-size:12px;display:flex;justify-content:space-between;align-items:center}
.edition-strip a{color:var(--accent);text-decoration:none;border:1px dashed rgba(192,57,43,.5);padding:4px 10px;border-radius:999px}
.intro{padding:24px 0}
.intro-inner{padding:0 0 0 18px;border-left:3px solid #d9cdbc}
.intro-kicker{margin:0 0 6px;color:var(--accent);font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:1.4px;text-transform:uppercase}
.intro p{margin:0;color:var(--muted);font-size:15px;line-height:1.9}
.filter-bar{padding:16px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-bottom:1px solid var(--border);margin-bottom:24px}
.filter-label{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
.filter-btn{font-family:'IBM Plex Mono',monospace;font-size:11px;padding:4px 12px;border-radius:999px;border:1px solid var(--border);background:white;color:var(--ink);cursor:pointer;transition:all 120ms}
.filter-btn:hover{border-color:var(--accent);color:var(--accent)}
.filter-btn.active{background:var(--accent);color:white;border-color:var(--accent)}
.papers{display:flex;flex-direction:column;gap:20px;padding-bottom:48px}
.paper-card{background:white;border:1px solid var(--border);border-radius:8px;overflow:hidden;box-shadow:var(--shadow)}
.card-header{padding:16px 20px 12px;border-bottom:1px solid #eee7dd;display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px}
.card-title{font-family:'Playfair Display',serif;font-size:17px;font-weight:700;line-height:1.4;margin:0 0 4px}
.card-meta{font-size:13px;color:var(--muted)}
.journal-badge{font-family:'IBM Plex Mono',monospace;font-size:11px;padding:3px 8px;border-radius:4px;background:var(--tag-bg);white-space:nowrap}
.b-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);margin-left:6px}
.card-body{padding:16px 20px;display:grid;grid-template-columns:1fr 1fr;gap:12px 20px}
.field-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.2px;text-transform:uppercase;color:var(--accent);margin-bottom:4px}
.field-value{font-size:14px;line-height:1.6}
.card-footer{padding:10px 20px;border-top:1px solid #eee7dd;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px}
.tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-family:'IBM Plex Mono',monospace;font-size:10px;padding:2px 8px;border-radius:3px;background:var(--tag-bg);color:var(--muted)}
.doi-link{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--accent);text-decoration:none}
footer{border-top:1px solid var(--border);padding:24px 0;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:640px){.card-body{grid-template-columns:1fr}.masthead-inner{flex-direction:column;align-items:center}}
</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <hr class="masthead-rule">
    <div class="masthead-inner">
      <span class="masthead-title">{{ issue.title }}</span>
      <span style="color:var(--muted);font-family:'IBM Plex Mono',monospace;font-size:12px">Issue #{{ issue.issueNumber }} · {{ issue.weekOf }}</span>
    </div>
    <div style="text-align:center;padding:8px 0;font-size:12px;color:var(--muted);font-family:'IBM Plex Mono',monospace">{{ issue.papers | length }} papers</div>
  </div>

  <div class="edition-strip">
    <span>{{ issue.publishDate }}</span>
    <a href="../index.html">← Archive</a>
  </div>

  <div class="intro">
    <div class="intro-inner">
      <p class="intro-kicker">{{ issue.intro.kicker }}</p>
      <p>{{ issue.intro.text }}</p>
    </div>
  </div>

  <div class="filter-bar">
    <span class="filter-label">Filter:</span>
    <button class="filter-btn" data-filter="all" onclick="setFilter('all')">All Papers</button>
    <button class="filter-btn" data-filter="behavioral" onclick="setFilter('behavioral')">Behavioral &amp; Experimental</button>
    {% for j in issue.papers | map(attribute='journal') | unique | list %}
    <button class="filter-btn" data-filter="{{ j | lower }}" onclick="setFilter('{{ j | lower }}')">{{ j }}</button>
    {% endfor %}
  </div>

  <div class="papers">
    {% for paper in issue.papers %}
    <div class="paper-card" data-behavioral="{{ 'true' if paper.isBehavioral else 'false' }}" data-journal="{{ paper.journal | lower }}">
      <div class="card-header">
        <div>
          <div class="card-title">{{ paper.title }}{% if paper.isBehavioral %}<span class="b-dot" title="Behavioral/Experimental"></span>{% endif %}</div>
          <div class="card-meta">{{ paper.authors | join(', ') }} · {{ paper.publishedDate }}</div>
        </div>
        <span class="journal-badge">{{ paper.journal }}</span>
      </div>
      <div class="card-body">
        <div><div class="field-label">Research Question</div><div class="field-value">{{ paper.rq or '—' }}</div></div>
        <div><div class="field-label">Method</div><div class="field-value">{{ paper.method or '—' }}</div></div>
        <div style="grid-column:1/-1"><div class="field-label">Key Finding</div><div class="field-value">{{ paper.keyFinding or '—' }}</div></div>
        <div style="grid-column:1/-1"><div class="field-label">Why It Matters</div><div class="field-value">{{ paper.whyItMatters or '—' }}</div></div>
      </div>
      <div class="card-footer">
        <div class="tags">{% for tag in paper.tags %}<span class="tag">{{ tag }}</span>{% endfor %}</div>
        {% if paper.sourceUrl %}<a class="doi-link" href="{{ paper.sourceUrl }}" target="_blank" rel="noopener">{{ paper.doi or 'View paper' }} ↗</a>{% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  <footer>{{ issue.title }} · Issue #{{ issue.issueNumber }} · Automated digest from top economics journals.</footer>
</div>
<script>
function setFilter(key){window.location.hash=key==='all'?'':key;applyFilter(key)}
function applyFilter(key){
  document.querySelectorAll('.paper-card').forEach(c=>{
    if(key==='all')c.style.display='';
    else if(key==='behavioral')c.style.display=c.dataset.behavioral==='true'?'':'none';
    else c.style.display=c.dataset.journal===key?'':'none';
  });
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.filter===key));
}
window.addEventListener('hashchange',()=>applyFilter(window.location.hash.slice(1)||'all'));
document.addEventListener('DOMContentLoaded',()=>applyFilter(window.location.hash.slice(1)||'all'));
</script>
</body>
</html>
```

- [ ] **Step 2: Write `templates/index.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Behavioral &amp; Experimental Economics Weekly</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root{--ink:#1a1a1a;--paper:#f6f3ed;--accent:#c0392b;--border:#d4cdc0;--muted:#7a7265;--shadow:0 2px 8px rgba(0,0,0,.06)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'IBM Plex Sans',sans-serif;line-height:1.7}
.wrap{max-width:820px;margin:0 auto;padding:0 24px}
.cover{padding:64px 0 40px;text-align:center;border-bottom:1px solid var(--border)}
.cover-rule{border:none;border-top:3px solid var(--ink);margin:0 auto 24px;width:80px}
.cover-title{font-family:'Playfair Display',serif;font-size:40px;font-weight:700;margin:0 0 12px}
.cover-sub{color:var(--muted);font-size:15px;max-width:480px;margin:0 auto}
.archive{padding:40px 0 64px}
.archive-title{font-family:'IBM Plex Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:2px;color:var(--accent);margin-bottom:20px}
.issue-list{display:flex;flex-direction:column;gap:12px}
.issue-row{background:white;border:1px solid var(--border);border-radius:8px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;text-decoration:none;color:inherit;box-shadow:var(--shadow);transition:box-shadow 120ms}
.issue-row:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}
.issue-num{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--accent);margin-bottom:4px}
.issue-week{font-family:'Playfair Display',serif;font-size:18px;font-weight:700}
.issue-date{font-size:13px;color:var(--muted);margin-top:2px}
.issue-count{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--muted)}
.arrow{color:var(--accent);font-size:18px}
footer{border-top:1px solid var(--border);padding:24px 0;color:var(--muted);font-size:13px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <div class="cover">
    <hr class="cover-rule">
    <h1 class="cover-title">Behavioral &amp; Experimental<br>Economics Weekly</h1>
    <p class="cover-sub">A weekly digest of new papers from top economics and psychology journals, summarized with AI.</p>
  </div>
  <div class="archive">
    <div class="archive-title">Archive</div>
    <div class="issue-list">
      {% for issue in issues %}
      <a class="issue-row" href="issues/becon-weekly-{{ issue.publishDate }}.html">
        <div>
          <div class="issue-num">Issue #{{ issue.issueNumber }}</div>
          <div class="issue-week">{{ issue.weekOf }}</div>
          <div class="issue-date">{{ issue.publishDate }}</div>
        </div>
        <div style="text-align:right">
          <div class="issue-count">{{ issue.papers | length }} papers</div>
          <div class="arrow">→</div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
  <footer>Behavioral &amp; Experimental Economics Weekly · Powered by Claude AI</footer>
</div>
</body>
</html>
```

- [ ] **Step 3: Commit**

```powershell
git add templates/
git commit -m "feat: add Jinja2 HTML templates for issue and index pages"
```

---

## Task 7: src/render.py and src/update_index.py

**Files:** `tests/test_render.py`, `src/render.py`, `tests/test_update_index.py`, `src/update_index.py`

- [ ] **Step 1: Write `tests/test_render.py`**

```python
import pytest
from pathlib import Path
from src.render import render_issue


class TestRenderIssue:
    def test_creates_html_file(self, sample_issue, tmp_path):
        out = str(tmp_path / "issue.html")
        render_issue(sample_issue, "templates/issue.html.j2", out)
        assert Path(out).exists()

    def test_contains_paper_title(self, sample_issue, tmp_path):
        out = str(tmp_path / "issue.html")
        render_issue(sample_issue, "templates/issue.html.j2", out)
        assert sample_issue["papers"][0]["title"] in Path(out).read_text(encoding="utf-8")

    def test_contains_filter_bar(self, sample_issue, tmp_path):
        out = str(tmp_path / "issue.html")
        render_issue(sample_issue, "templates/issue.html.j2", out)
        assert "filter-bar" in Path(out).read_text(encoding="utf-8")

    def test_contains_journal_badge(self, sample_issue, tmp_path):
        out = str(tmp_path / "issue.html")
        render_issue(sample_issue, "templates/issue.html.j2", out)
        assert "AER" in Path(out).read_text(encoding="utf-8")
```

- [ ] **Step 2: Write `tests/test_update_index.py`**

```python
import json
import pytest
from pathlib import Path
from src.update_index import update_index


class TestUpdateIndex:
    def test_creates_index_html(self, sample_issue, tmp_path):
        data_dir = tmp_path / "issues"
        data_dir.mkdir()
        (data_dir / "becon-weekly-2026-05-26.json").write_text(json.dumps(sample_issue), encoding="utf-8")
        out = str(tmp_path / "index.html")
        update_index(str(data_dir), "templates/index.html.j2", out)
        assert Path(out).exists()

    def test_contains_issue_date(self, sample_issue, tmp_path):
        data_dir = tmp_path / "issues"
        data_dir.mkdir()
        (data_dir / "becon-weekly-2026-05-26.json").write_text(json.dumps(sample_issue), encoding="utf-8")
        out = str(tmp_path / "index.html")
        update_index(str(data_dir), "templates/index.html.j2", out)
        assert "2026-05-26" in Path(out).read_text(encoding="utf-8")

    def test_newest_issue_first(self, sample_issue, tmp_path):
        data_dir = tmp_path / "issues"
        data_dir.mkdir()
        old = {**sample_issue, "publishDate": "2026-05-19", "issueNumber": 1}
        new = {**sample_issue, "publishDate": "2026-05-26", "issueNumber": 2}
        (data_dir / "becon-weekly-2026-05-19.json").write_text(json.dumps(old), encoding="utf-8")
        (data_dir / "becon-weekly-2026-05-26.json").write_text(json.dumps(new), encoding="utf-8")
        out = str(tmp_path / "index.html")
        update_index(str(data_dir), "templates/index.html.j2", out)
        content = Path(out).read_text(encoding="utf-8")
        assert content.index("2026-05-26") < content.index("2026-05-19")
```

- [ ] **Step 3: Run — confirm fail**

```powershell
python -m pytest tests/test_render.py tests/test_update_index.py -v
```

- [ ] **Step 4: Write `src/render.py`**

```python
import os
from jinja2 import Environment, FileSystemLoader


def render_issue(issue: dict, template_path: str, output_path: str) -> None:
    tdir = os.path.dirname(os.path.abspath(template_path))
    tfile = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(tdir), autoescape=True)
    html = env.get_template(tfile).render(issue=issue)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[render] {output_path}")


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as f:
        issue = json.load(f)
    render_issue(issue, args.template, args.output)
```

- [ ] **Step 5: Write `src/update_index.py`**

```python
import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def update_index(data_dir: str, template_path: str, output_path: str) -> None:
    issues = []
    for path in sorted(Path(data_dir).glob("*.json"), reverse=True):
        try:
            issues.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"[index] WARNING {path}: {exc}")
    tdir = os.path.dirname(os.path.abspath(template_path))
    tfile = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(tdir), autoescape=True)
    html = env.get_template(tfile).render(issues=issues)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[index] {output_path} ({len(issues)} issues)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    update_index(args.data_dir, args.template, args.output)
```

- [ ] **Step 6: Run full test suite**

```powershell
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/render.py src/update_index.py tests/test_render.py tests/test_update_index.py
git commit -m "feat: add renderer and index rebuilder"
```

---

## Task 8: PowerShell Scripts

**Files:** `scripts/run_weekly.ps1`, `scripts/publish.ps1`

- [ ] **Step 1: Write `scripts/run_weekly.ps1`**

```powershell
param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$SkipPublish
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Log = Join-Path $LogDir "$Date.log"

function Log($msg) { "$([datetime]::Now.ToString('HH:mm:ss')) $msg" | Tee-Object -Append $Log }

Log "=== Weekly run $Date ==="
if (-not $env:ANTHROPIC_API_KEY) { Log "ERROR: ANTHROPIC_API_KEY not set"; exit 1 }
Set-Location $Root

try {
    Log "1/5 Fetching feeds..."
    python src/fetch.py --config config.yaml --output cache/papers_raw.json
    Log "1/5 done"

    Log "2/5 Summarizing..."
    python src/summarize.py --config config.yaml --input cache/papers_raw.json --output cache/papers_summarized.json
    Log "2/5 done"

    Log "3/5 Building issue..."
    python src/build_issue.py --config config.yaml --input cache/papers_summarized.json --date $Date
    Log "3/5 done"

    Log "4/5 Rendering HTML..."
    python src/render.py --template templates/issue.html.j2 --input "data/issues/becon-weekly-$Date.json" --output "issues/becon-weekly-$Date.html"
    Log "4/5 done"

    Log "5/5 Updating index..."
    python src/update_index.py --data-dir data/issues --template templates/index.html.j2 --output index.html
    Log "5/5 done"

    if (-not $SkipPublish) {
        & "$PSScriptRoot\publish.ps1" -Date $Date
    } else {
        Log "Publish skipped"
    }
    Log "=== Done ==="
} catch {
    Log "ERROR: $_"
    exit 1
}
```

- [ ] **Step 2: Write `scripts/publish.ps1`**

```powershell
param([string]$Date = (Get-Date -Format "yyyy-MM-dd"))
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Count = 0
$Json = "data/issues/becon-weekly-$Date.json"
if (Test-Path $Json) {
    $Count = (Get-Content $Json | ConvertFrom-Json).papers.Count
}
git add data/ issues/ index.html
git commit -m "chore: weekly issue $Date ($Count papers)"
git push origin main
Write-Output "[publish] Pushed $Date"
```

- [ ] **Step 3: Commit**

```powershell
git add scripts/
git commit -m "feat: PowerShell orchestration and publish scripts"
```

---

## Task 9: GitHub Setup

- [ ] **Step 1: Create GitHub repo**

Go to `github.com` → New repository → name: `econ-research-newsletter` → Public → no README.

- [ ] **Step 2: Push**

```powershell
git remote add origin https://github.com/<your-username>/econ-research-newsletter.git
git branch -M main
git push -u origin main
```

- [ ] **Step 3: Enable GitHub Pages**

Repo → Settings → Pages → Source: `Deploy from branch` → `main` → `/ (root)` → Save.

- [ ] **Step 4: Update config with Pages URL, commit**

Edit `config.yaml` line: `github_pages_url: "https://<your-username>.github.io/econ-research-newsletter"`

```powershell
git add config.yaml
git commit -m "chore: set GitHub Pages URL"
git push origin main
```

---

## Task 10: Windows Task Scheduler

- [ ] **Step 1: Register job (run PowerShell as Administrator)**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File `"C:\Users\yu2511zh\econ-research-newsletter\scripts\run_weekly.ps1`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 08:00AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
Register-ScheduledTask `
    -TaskName "EconNewsletterWeekly" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Weekly behavioral econ newsletter" -RunLevel Highest
```

- [ ] **Step 2: Set API key as machine environment variable (Admin PowerShell)**

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "<your-key>", "Machine")
```

- [ ] **Step 3: Verify**

```powershell
Get-ScheduledTask -TaskName "EconNewsletterWeekly"
```

Expected: `Ready` state.

---

## Task 11: First Manual Run

- [ ] **Step 1: Verify RSS feeds**

```powershell
python -c "
import feedparser, yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
for feed in cfg['feeds']:
    r = feedparser.parse(feed['url'])
    print(f\"{feed['name']}: {len(r.entries)} entries, status={getattr(r,'status','N/A')}\")
"
```

Fix any URLs returning 0 entries in `config.yaml` by searching for `<journal name> RSS feed`.

- [ ] **Step 2: Dry run (no publish)**

```powershell
.\scripts\run_weekly.ps1 -SkipPublish
```

Expected: HTML written to `issues/` and `index.html` updated, no git push.

- [ ] **Step 3: Open in browser**

```powershell
$d = Get-Date -Format "yyyy-MM-dd"
Start-Process "issues\becon-weekly-$d.html"
Start-Process "index.html"
```

Verify: paper cards visible, filter toggle works, journal badges correct.

- [ ] **Step 4: Publish**

```powershell
.\scripts\run_weekly.ps1
```

- [ ] **Step 5: Verify live site**

Open `https://<your-username>.github.io/econ-research-newsletter` — allow ~2 minutes for GitHub Pages to deploy.
