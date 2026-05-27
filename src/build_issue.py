import argparse
import json
import os
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

    max_papers = config.get("api", {}).get("max_papers_per_issue", 30)
    papers = payload.get("papers", [])[:max_papers]

    issue = {
        "title": config.get("newsletter", {}).get("title", "Behavioral & Experimental Economics Weekly"),
        "weekOf": publish_date,
        "publishDate": publish_date,
        "issueNumber": issue_number,
        "intro": {"kicker": "Editor's Note", "text": payload.get("intro", "")},
        "papers": papers,
    }
    out_path = f"{data_dir}/becon-weekly-{publish_date}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(issue, f, indent=2, ensure_ascii=False)
    print(f"[build] wrote issue #{issue_number} -> {out_path}")


if __name__ == "__main__":
    main()
