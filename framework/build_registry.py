#!/usr/bin/env python3
"""
build_registry.py
-----------------
Flyxion project scaffolding tool.
Generates directories, README templates, and metadata files
from project_registry.yaml.

Usage:
  python build_registry.py --registry project_registry.yaml --outdir projects --git
"""

import argparse
import os
import yaml
import subprocess
from datetime import datetime

README_TEMPLATE = """# {name}
**Category:** {category}  
**Status:** {status}  
**Languages:** {stack}

---

## Description
{description}

## Dependencies
{deps}

## Metadata
- Created: {timestamp}
- Repository Path: `{repo_path}`
- Tags: {tags}
"""

def make_dir(path: str):
    os.makedirs(path, exist_ok=True)

def write_readme(project, outdir):
    readme_path = os.path.join(outdir, project["repo_path"], "README.md")
    make_dir(os.path.dirname(readme_path))
    deps = ", ".join(project.get("dependencies", [])) or "None"
    tags = ", ".join(project.get("tags", []))
    text = README_TEMPLATE.format(
        name=project["name"],
        category=project["category"],
        status=project["status"].replace("_", " ").title(),
        stack=", ".join(project["stack"]),
        description=project["description"].strip(),
        deps=deps,
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        repo_path=project["repo_path"],
        tags=tags,
    )
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[+] Created {readme_path}")

def init_git_repo(path):
    if not os.path.exists(os.path.join(path, ".git")):
        subprocess.run(["git", "init", path], check=False)
        print(f"[✓] Initialized git repo at {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, help="Path to project_registry.yaml")
    parser.add_argument("--outdir", default="projects", help="Output root directory")
    parser.add_argument("--git", action="store_true", help="Initialize Git repos")
    args = parser.parse_args()

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for project in data["projects"]:
        full_path = os.path.join(args.outdir, project["repo_path"])
        write_readme(project, args.outdir)
        if args.git:
            init_git_repo(full_path)

    print("\n[Flyxion] Registry build complete.")

if __name__ == "__main__":
    main()
