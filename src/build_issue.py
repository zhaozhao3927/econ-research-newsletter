import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml


def _next_issue_number(data_dir: str) -> int:
    max_issue = 0
    for p in Path(data_dir).glob("becon-weekly-*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            max_issue = max(max_issue, int(data.get("issueNumber", 0)))
        except Exception:
            pass
    return max_issue + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--date", required=False)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    publish_date = args.date or datetime.now().strftime("%Y-%m-%d")
    data_dir = "data/issues"
    os.makedirs(data_dir, exist_ok=True)
    issue_number = _next_issue_number(data_dir)

    all_papers = payload.get("papers", [])
    journal_order = config.get("newsletter", {}).get("journal_vitality_order", [])
    order_index = {j: i for i, j in enumerate(journal_order)}
    other_index = order_index.get("Other", len(journal_order))

    def _date_rank(s: str) -> int:
        try:
            return -datetime.strptime(s, "%Y-%m-%d").toordinal()
        except Exception:
            return 0

    def _order_key(p: dict) -> tuple[int, int, str]:
        j = p.get("journal", "")
        idx = order_index.get(j, other_index)
        # Keep deterministic order inside a journal by newest date then title.
        return (idx, _date_rank(p.get("publishedDate", "")), p.get("title", ""))

    papers = sorted(all_papers, key=_order_key)
    max_papers = config.get("api", {}).get("max_papers_per_issue", 0)
    if isinstance(max_papers, int) and max_papers > 0:
        papers = papers[:max_papers]

    known = {j for j in journal_order if j != "Other"}
    grouped = [p.get("journal", "") if p.get("journal", "") in known else "Other" for p in papers]
    journal_counts = dict(Counter(grouped))

    issue = {
        "title": config.get("newsletter", {}).get("title", "Behavioral & Experimental Economics Weekly"),
        "weekOf": publish_date,
        "publishDate": publish_date,
        "issueNumber": issue_number,
        "intro": {"kicker": "Editor's Note", "text": payload.get("intro", "")},
        "papers": papers,
        "journalOrder": journal_order,
        "journalCounts": journal_counts,
        "feedDiagnostics": payload.get("feedDiagnostics", []),
    }
    out_path = f"{data_dir}/becon-weekly-{publish_date}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(issue, f, indent=2, ensure_ascii=False)
    print(f"[build] wrote issue #{issue_number} -> {out_path}")


if __name__ == "__main__":
    main()
