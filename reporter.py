#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import hashlib
import yaml
from pathlib import Path
from datetime import date
import sys

# ---------------- Config ----------------

def load_config(path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[!] Config file not found: {path}")
        sys.exit(1)

# ---------------- Helpers ----------------

def run(cmd):
    subprocess.run(cmd, check=True)

def replace_metadata(md_file, cfg):
    text = md_file.read_text()

    replacements = {
        "title": cfg["metadata"].get("title", ""),
        "author": cfg["metadata"].get("author", ""),
        "date": str(date.today())
    }

    for key, value in replacements.items():
        text = text.replace(f'{key}: ""', f'{key}: "{value}"')

    md_file.write_text(text)

def md5sum(file):
    return hashlib.md5(file.read_bytes()).hexdigest()

# ---------------- Commands ----------------

def init_cmd(args, cfg):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"[!] Template not found: {template_path}")
        sys.exit(1)

    target = output / template_path.name
    shutil.copy(template_path, target)

    replace_metadata(target, cfg)

    print(f"[+] Template copied to {target}")
    print("[+] Edit the Markdown file, then run `generate`")

def generate_cmd(args, cfg):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    pdf = output / cfg["output"]["pdf_name"]

    pandoc_cfg = cfg["pandoc"]

    cmd = [
        "pandoc",
        args.input,
        "-o", str(pdf),
        "--from", "markdown+yaml_metadata_block+raw_html",
        "--template", pandoc_cfg["template"],
        "--highlight-style", pandoc_cfg["highlight_style"],
        "--resource-path", cfg["paths"]["resource_path"],
        "--top-level-division", pandoc_cfg["top_level_division"]
    ]

    if pandoc_cfg.get("toc", False):
        cmd.append("--table-of-contents")
        cmd.extend(["--toc-depth", str(pandoc_cfg.get("toc_depth", 6))])

    if pandoc_cfg.get("number_sections", False):
        cmd.append("--number-sections")

    print("[+] Generating PDF...")
    run(cmd)
    print(f"[+] PDF generated: {pdf}")

    if cfg["output"].get("archive", False):
        archive = output / f"{pdf.stem}.7z"
        print("[+] Creating archive...")
        run(["7z", "a", str(archive), str(pdf)])

        checksum = md5sum(archive)
        print(f"[+] Archive: {archive}")
        print(f"[+] MD5: {checksum}")

# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser(
        description="Generic Markdown Report Generator"
    )
    parser.add_argument(
        "--config",
        default="config.yml",
        help="Path to config file"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a report from template")
    init.add_argument(
        "--template",
        required=True,
        help="Path to markdown template"
    )
    init.add_argument(
        "--output",
        required=True,
        help="Output directory"
    )

    gen = sub.add_parser("generate", help="Generate PDF report")
    gen.add_argument(
        "--input",
        required=True,
        help="Markdown report file"
    )
    gen.add_argument(
        "--output",
        required=True,
        help="Output directory"
    )

    args = parser.parse_args()
    cfg = load_config(args.config)

    if args.command == "init":
        init_cmd(args, cfg)
    elif args.command == "generate":
        generate_cmd(args, cfg)

if __name__ == "__main__":
    main()
