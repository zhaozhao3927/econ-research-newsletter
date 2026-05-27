import argparse
import json
import os

from jinja2 import Environment, FileSystemLoader


def render_issue(issue: dict, template_path: str, output_path: str) -> None:
    template_dir = os.path.dirname(template_path) or "."
    template_file = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    tpl = env.get_template(template_file)
    html = tpl.render(issue=issue)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        issue = json.load(f)
    render_issue(issue, args.template, args.output)
    print(f"[render] wrote {args.output}")


if __name__ == "__main__":
    main()
