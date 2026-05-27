import argparse
import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    issues: list[dict] = []
    for p in Path(args.data_dir).glob("becon-weekly-*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                issues.append(json.load(f))
        except Exception:
            pass
    issues.sort(key=lambda x: x.get("publishDate", ""), reverse=True)

    template_dir = os.path.dirname(args.template) or "."
    template_file = os.path.basename(args.template)
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    tpl = env.get_template(template_file)
    html = tpl.render(issues=issues)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[index] wrote {args.output} with {len(issues)} issues")


if __name__ == "__main__":
    main()
