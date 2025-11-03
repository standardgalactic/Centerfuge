
#!/usr/bin/env python3

import os, sys, subprocess, shutil, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "src")
OUT = os.path.join(ROOT, "docs", "_site")

def ensure_markdown():
    try:
        import markdown  # type: ignore
        return True
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
            import markdown  # noqa
            return True
        except Exception as e:
            print("[docs] Could not install 'markdown' package, using plaintext fallback:", e)
            return False

def render_markdown(md_text, md_enabled):
    if md_enabled:
        import markdown  # type: ignore
        return markdown.markdown(md_text, extensions=["fenced_code", "toc"])
    else:
        # Minimal fallback: escape HTML and wrap in <pre>
        import html
        return "<pre>" + html.escape(md_text) + "</pre>"

def main():
    os.makedirs(OUT, exist_ok=True)
    ok_md = ensure_markdown()

    # read SUMMARY.md to get ordering
    summary_path = os.path.join(SRC, "SUMMARY.md")
    if not os.path.exists(summary_path):
        print("[docs] Missing SUMMARY.md")
        sys.exit(1)
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = f.read()

    # Copy static assets
    static_src = os.path.join(ROOT, "docs", "static")
    if os.path.isdir(static_src):
        shutil.copytree(static_src, os.path.join(OUT, "static"), dirs_exist_ok=True)

    # Build an index.html with TOC
    index_html = render_markdown(summary, ok_md)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"<!doctype html><meta charset='utf-8'><title>flyxion-core docs</title>{index_html}")

    # Convert each .md to .html
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.endswith(".md"): continue
            md_path = os.path.join(root, fn)
            rel_dir = os.path.relpath(root, SRC)
            out_dir = os.path.join(OUT, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            with open(md_path, "r", encoding="utf-8") as f:
                md = f.read()
            html = render_markdown(md, ok_md)
            out_path = os.path.join(out_dir, fn[:-3] + ".html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"<!doctype html><meta charset='utf-8'><title>{fn}</title>{html}")
    print(f"[docs] Built fallback docs into {OUT}")

if __name__ == "__main__":
    main()
