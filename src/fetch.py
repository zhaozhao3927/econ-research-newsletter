import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

import feedparser
import yaml


DOI_REGEX = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
AUTHOR_BLOCK_REGEX = re.compile(r"Author\(s\):\s*(.+)$", re.IGNORECASE)


def _extract_doi(text: str) -> str:
    if not text:
        return ""
    m = DOI_REGEX.search(text)
    return m.group(0) if m else ""


def _date_from_entry(entry) -> str:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        dt = datetime(*parsed[:6], tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def _within_days(entry, days: int = 7) -> bool:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return True
    dt = datetime(*parsed[:6], tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def _extract_authors(entry, abstract: str) -> list[str]:
    # Prefer structured feedparser author list when available.
    if hasattr(entry, "authors") and entry.authors:
        names: list[str] = []
        for a in entry.authors:
            if isinstance(a, dict):
                n = (a.get("name", "") or "").strip()
            else:
                n = str(a).strip()
            if n:
                names.append(n)
        if names:
            return names

    # Fallback to single author field.
    author = (getattr(entry, "author", "") or "").strip()
    if author:
        if ";" in author:
            return [a.strip() for a in author.split(";") if a.strip()]
        if " and " in author.lower():
            return [a.strip() for a in re.split(r"\band\b", author, flags=re.IGNORECASE) if a.strip()]
        # Heuristic: if there are multiple commas, treat as a list.
        if author.count(",") >= 2:
            return [a.strip() for a in author.split(",") if a.strip()]
        return [author]

    # Some feeds (e.g. ScienceDirect RSS) include authors in summary text.
    m = AUTHOR_BLOCK_REGEX.search(abstract or "")
    if m:
        raw = m.group(1).strip()
        raw = re.split(r"(?:\s{2,}|$)", raw)[0].strip()
        if raw:
            return [a.strip() for a in raw.split(",") if a.strip()]

    return []


def fetch_papers(config: dict) -> tuple[list[dict], list[dict]]:
    papers: list[dict] = []
    diagnostics: list[dict] = []
    for feed in config.get("feeds", []):
        name = feed.get("name", "Unknown")
        url = feed.get("url", "")
        if not url:
            continue
        try:
            parsed = feedparser.parse(url)
            total_entries = len(getattr(parsed, "entries", []))
            recent_entries = 0
            for entry in parsed.entries:
                if not _within_days(entry, 7):
                    continue
                recent_entries += 1
                title = (getattr(entry, "title", "") or "").strip()
                if not title:
                    continue
                link = (getattr(entry, "link", "") or "").strip()
                abstract = re.sub(r"<[^>]+>", "", (getattr(entry, "summary", "") or "")).strip()
                authors = _extract_authors(entry, abstract)
                raw = " ".join(
                    [
                        getattr(entry, "id", "") or "",
                        link,
                        title,
                    ]
                )
                doi = _extract_doi(raw)
                if not doi:
                    doi = "hash:" + hashlib.md5((title + link).encode("utf-8")).hexdigest()[:12]
                papers.append(
                    {
                        "title": title,
                        "authors": authors,
                        "journal": name,
                        "publishedDate": _date_from_entry(entry),
                        "doi": doi,
                        "sourceUrl": link,
                        "abstract": abstract,
                    }
                )
            diagnostics.append(
                {
                    "journal": name,
                    "url": url,
                    "status": getattr(parsed, "status", None),
                    "totalEntries": total_entries,
                    "recentEntries": recent_entries,
                    "error": "",
                }
            )
        except Exception as exc:
            print(f"[fetch] skipped {name}: {exc}")
            diagnostics.append(
                {
                    "journal": name,
                    "url": url,
                    "status": None,
                    "totalEntries": 0,
                    "recentEntries": 0,
                    "error": str(exc),
                }
            )
    # Dedup by DOI
    dedup: dict[str, dict] = {}
    for p in papers:
        dedup[p["doi"]] = p
    return list(dedup.values()), diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    papers, diagnostics = fetch_papers(config)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"papers": papers, "feedDiagnostics": diagnostics}, f, indent=2, ensure_ascii=False)
    print(f"[fetch] wrote {len(papers)} papers -> {args.output}")


if __name__ == "__main__":
    main()
