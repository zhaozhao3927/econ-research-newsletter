import argparse
import json
import os
import re

import yaml

try:
    import anthropic
except Exception:  # pragma: no cover
    anthropic = None


def _load_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _fallback_summary(paper: dict) -> dict:
    return {
        "rq": "",
        "method": "",
        "keyFinding": "",
        "whyItMatters": "",
        "isBehavioral": False,
        "tags": [],
    }


def _is_empty_summary(summary: dict) -> bool:
    return not (summary.get("rq") or summary.get("keyFinding"))


def _extract_message_text(resp) -> str:
    parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text" and getattr(block, "text", None):
            parts.append(block.text)
    return "\n".join(parts).strip()


def _parse_json_response(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty model response")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError(f"no JSON object in response: {text[:120]!r}")
        return json.loads(match.group(0))


def _normalize_summary(data: dict) -> dict:
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif not isinstance(tags, list):
        tags = []
    return {
        "rq": str(data.get("rq", "") or ""),
        "method": str(data.get("method", "") or ""),
        "keyFinding": str(data.get("keyFinding", "") or ""),
        "whyItMatters": str(data.get("whyItMatters", "") or ""),
        "isBehavioral": bool(data.get("isBehavioral", False)),
        "tags": [str(t) for t in tags[:4]],
    }


def _call_claude(client, model: str, paper: dict) -> dict:
    title = paper.get("title", "")
    journal = paper.get("journal", "")
    abstract = paper.get("abstract", "") or "(no abstract in feed)"

    system = (
        "You are a concise economics newsletter editor. "
        "Respond with a single JSON object only. No markdown, no preamble."
    )
    user_prompt = (
        "Summarize this paper. JSON keys: rq, method, keyFinding, whyItMatters, isBehavioral, tags.\n"
        f"title: {title}\n"
        f"journal: {journal}\n"
        f"abstract: {abstract}\n"
    )
    strict_prompt = user_prompt + (
        '\nExample shape: {"rq":"...","method":"...","keyFinding":"...",'
        '"whyItMatters":"...","isBehavioral":true,"tags":["lab","politics"]}'
    )

    last_err: Exception | None = None
    for attempt, prompt in enumerate((user_prompt, strict_prompt), start=1):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=700,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = _extract_message_text(resp)
            if not raw:
                raise ValueError("empty model response")
            data = _parse_json_response(raw)
            return _normalize_summary(data)
        except Exception as exc:
            last_err = exc
            if attempt == 1:
                continue
    raise last_err or ValueError("failed to summarize")


def summarize_all(
    config: dict, papers: list[dict], *, force_refresh: bool = False
) -> tuple[list[dict], str]:
    cache_path = config.get("cache", {}).get("path", "cache/summaries.json")
    cache = _load_cache(cache_path)
    model = config.get("api", {}).get("model", "claude-sonnet-4-6")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    use_api = bool(api_key and anthropic is not None)
    if not api_key:
        print("[summarize] WARNING: ANTHROPIC_API_KEY is not set — summaries will be empty.")
    elif anthropic is None:
        print("[summarize] WARNING: anthropic package not installed — run: pip install anthropic")
    else:
        print(f"[summarize] Using Claude model: {model}")

    client = anthropic.Anthropic(api_key=api_key) if use_api else None

    out: list[dict] = []
    api_success = 0
    api_fail = 0
    cache_hits = 0
    total = len(papers)
    for i, p in enumerate(papers, start=1):
        doi = p.get("doi", "")
        cached = cache.get(doi) if doi and not force_refresh else None
        if cached and not _is_empty_summary(cached):
            summary = cached
            cache_hits += 1
        elif use_api:
            if i == 1 or i % 10 == 0 or i == total:
                print(f"[summarize] progress {i}/{total}")
            try:
                summary = _call_claude(client, model, p)
                if _is_empty_summary(summary):
                    print(f"[summarize] WARNING: empty response for: {p.get('title', '')[:60]}")
                    api_fail += 1
                else:
                    api_success += 1
            except Exception as exc:
                print(f"[summarize] ERROR for '{p.get('title', '')[:50]}': {exc}")
                summary = _fallback_summary(p)
                api_fail += 1
            if doi and not _is_empty_summary(summary):
                cache[doi] = summary
        else:
            summary = _fallback_summary(p)
            # Do not cache fallback empties when API is unavailable.
        out.append({**p, **summary})

    _save_cache(cache_path, cache)
    print(
        f"[summarize] stats: cache_hits={cache_hits}, api_success={api_success}, api_fail={api_fail}, total={len(papers)}"
    )
    intro = f"This week we tracked {len(out)} papers across major economics and related journals."
    return out, intro


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and re-summarize all papers (use after fixing API key)",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with open(args.input, "r", encoding="utf-8") as f:
        papers = json.load(f)

    papers_with_summaries, intro = summarize_all(config, papers, force_refresh=args.force)
    payload = {"papers": papers_with_summaries, "intro": intro}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[summarize] wrote {len(papers_with_summaries)} papers -> {args.output}")


if __name__ == "__main__":
    main()
